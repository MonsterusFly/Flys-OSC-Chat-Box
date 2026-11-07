"""Native Qt/KDE GUI with page navigation and independent OSC integrations."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QAction, QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFormLayout, QFrame, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QProgressBar,
    QPushButton, QSpinBox, QStackedWidget, QSystemTrayIcon, QMenu, QTextEdit,
    QVBoxLayout, QWidget, QInputDialog, QDialog, QGridLayout, QScrollArea, QToolButton, QSizePolicy, QLayout, QFileDialog,
)

from core.updater import APP_VERSION, RELEASES_URL, check_release, download_verified_rpm, installed_via_rpm, rpm_install_command, explain_update_error, human_size
from core.message_engine import MAX_CHARS, PRESETS, render_template, unknown_variables
from core.emojis import matching_emojis, EMOJIS
from core.emoji_assets import emoji_icon_path
from core.emoji_preview import rich_emoji_preview
from core.osc_client import OSCClient
from core.backups import export_backup, restore_backup
from core.diagnostics import SendHistory
from integrations.gpu import snapshot as gpu_snapshot, GPUStats
from integrations.artwork import local_album_art
from core.auto_sender import AutoSendScheduler
from core.status_profiles import StatusProfile, StatusRotator, next_enabled_index
from core.settings import Settings
from core.themes import THEMES, stylesheet
from core.sections import SectionComposer, SECTION_PRESETS, clean_sections
from integrations.music import Track, current_track, list_players, control_player, styled_progress_bar
from integrations.system import SystemSnapshot, SystemMonitor


class MainWindow(QMainWindow):
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self.settings = Settings.load()
        self.last_sent: str | None = None
        self._last_destination: tuple[str, int] | None = None
        self._real_close = False
        self.track = Track()
        self.stats = SystemSnapshot(0, 0)
        self.monitor = SystemMonitor()
        self.scheduler = AutoSendScheduler(self.settings.auto_interval)
        self.send_count = 0
        self.send_history = SendHistory()
        self.gpu_stats = GPUStats()
        self._gpu_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="gpu-poll")
        self._gpu_future = None
        raw_profiles = self.settings.status_profiles
        if raw_profiles is None:
            raw_profiles = [{"name": "Default", "text": self.settings.status_text, "enabled": True}]
        self.status_profiles = [StatusProfile(**item) for item in raw_profiles]
        self.selected_status = min(max(0, self.settings.selected_status), len(self.status_profiles)-1)
        self.status_rotator = StatusRotator(self.settings.status_rotation_interval)
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.setInterval(700)
        self._autosave_timer.timeout.connect(self._save_settings)
        self._music_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="music-poll")
        self._music_future = None
        self._player_scan_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="player-scan")
        self._player_scan_future = None
        self._player_selected_for_poll = "Auto"
        self.custom_layouts = dict(self.settings.custom_layouts or {})
        self.section_composer = SectionComposer()
        self.message_sections = clean_sections(self.settings.message_sections)
        self.setWindowTitle(f"Fly's OSC Chat Box · v{APP_VERSION}")
        self.resize(1000, 700)
        self.setMinimumSize(550, 420)
        self._build_ui()
        self._apply_theme(self.settings.theme)
        self._build_tray()
        self._wire_signals()

        # System sampling is independent of OSC transmission and music polling.
        self.monitor_timer = QTimer(self)
        self.monitor_timer.timeout.connect(self._poll_system)
        self.monitor_timer.start(2000)
        self._poll_system()

        self.music_timer = QTimer(self)
        self.music_timer.timeout.connect(self._poll_music)
        self.music_timer.start(3000)
        self._poll_music()
        self._scan_players()

        # One lightweight tick handles countdown and monotonic auto-send cadence.
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._clock_tick)
        self.clock_timer.start(250)
        self._update_auto_timer()
        self._update_rotation_timer()
        self._refresh_status_ui()
        self._refresh_preview()

        self._update_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="release-update")
        self._update_future = None
        self._update_action = None
        self._available_release = None
        self._downloaded_update = None
        self._update_install_process = None
        self._update_timer = QTimer(self)
        self._update_timer.setInterval(250)
        self._update_timer.timeout.connect(self._update_tick)
        self._update_timer.start()
        # Startup check is optional and delayed until the main window loads.
        if self.settings.check_updates:
            QTimer.singleShot(3000, lambda: self._check_for_updates(silent=True))

    def _build_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.sidebar = QListWidget()
        self.sidebar.setMinimumWidth(135)
        self.sidebar.setMaximumWidth(205)
        self.sidebar.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.sidebar.addItems(["Chatbox", "Composer", "Statuses", "Music", "System", "OSC Diagnostics", "Integrations", "Settings"])
        root.addWidget(self.sidebar, 0)
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        root.addWidget(line)
        self.pages = QStackedWidget()
        root.addWidget(self.pages, 1)
        self.pages.addWidget(self._scroll_page(self._page_chatbox()))
        self.pages.addWidget(self._page_composer())
        self.pages.addWidget(self._scroll_page(self._page_statuses()))
        self.pages.addWidget(self._scroll_page(self._page_music()))
        self.pages.addWidget(self._scroll_page(self._page_system()))
        self.pages.addWidget(self._scroll_page(self._page_diagnostics()))
        self.pages.addWidget(self._scroll_page(self._page_integrations()))
        self.pages.addWidget(self._scroll_page(self._page_settings()))
        self.sidebar.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.sidebar.setCurrentRow(0)
        self.statusBar().showMessage("Ready — UDP sends cannot confirm VRChat delivery")

    @staticmethod
    def _scroll_page(page: QWidget) -> QScrollArea:
        """Allow pages to keep usable control heights at any window size."""
        page.layout().setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        scroll = QScrollArea()
        scroll.setObjectName("contentScroll")
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setWidget(page)
        return scroll

    @staticmethod
    def _page(title: str, subtitle: str):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        heading = QLabel(title)
        heading.setObjectName("header")
        layout.addWidget(heading)
        desc = QLabel(subtitle)
        desc.setObjectName("subtitle")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        return widget, layout

    def _page_chatbox(self):
        page, layout = self._page("Chatbox", "Compose messages and send them through VRChat OSC.")
        group = QGroupBox("Your custom status")
        box = QVBoxLayout(group)
        self.status = QTextEdit()
        self.status.setPlaceholderText("What should VRChat show?")
        self.status.setFixedHeight(62)
        self.status.setPlainText(self.settings.status_text)
        self.status.setReadOnly(True)
        self.status.setToolTip("Edit the selected status in the Statuses page")
        box.addWidget(self.status)
        status_hint = QLabel("Edit or select statuses on the Statuses page. The selected status is used in {status}.")
        status_hint.setObjectName("subtitle")
        status_hint.setWordWrap(True)
        box.addWidget(status_hint)
        layout.addWidget(group)

        templates = QGroupBox("Message layout")
        template_layout = QVBoxLayout(templates)
        preset_row = QVBoxLayout()
        self.presets = QComboBox()
        self.presets.addItem("Choose a preset…")
        self.presets.addItems(PRESETS)
        preset_row.addWidget(QLabel("Preset"))
        preset_row.addWidget(self.presets, 1)
        template_layout.addLayout(preset_row)
        self.template = QTextEdit()
        self.template.setPlainText(self.settings.template)
        self.template.setMinimumHeight(115)
        self.template.setMaximumHeight(160)
        self.template.setPlaceholderText("{status} | {music} | {system} | {time}")
        template_layout.addWidget(self.template)
        tools_row = QVBoxLayout()
        self.insert_variable = QComboBox()
        self.insert_variable.addItem("Insert variable…", "")
        for variable in ("status", "music", "music_with_progress", "music_bar", "music_progress", "artist", "title", "position", "duration", "system", "cpu", "ram", "gpu", "gpu_usage", "gpu_temp", "vram", "time"):
            self.insert_variable.addItem("{" + variable + "}", "{" + variable + "}")
        tools_row.addWidget(self.insert_variable, 1)
        self.add_separator_btn = QPushButton("Insert | separator")
        self.add_newline_btn = QPushButton("Insert newline")
        tools_row.addWidget(self.add_separator_btn)
        tools_row.addWidget(self.add_newline_btn)
        template_layout.addLayout(tools_row)
        custom_row = QVBoxLayout()
        self.saved_layouts = QComboBox()
        self.saved_layouts.addItem("Saved layouts…")
        self._reload_layout_names()
        self.save_layout_btn = QPushButton("Save layout as…")
        self.delete_layout_btn = QPushButton("Delete saved layout")
        custom_row.addWidget(self.saved_layouts, 1)
        custom_row.addWidget(self.save_layout_btn)
        custom_row.addWidget(self.delete_layout_btn)
        template_layout.addLayout(custom_row)
        self.template_emoji_btn = QPushButton("Insert emoji into template")
        template_layout.addWidget(self.template_emoji_btn)
        token_help = QLabel("Variables: {status}, {music}, {music_progress}, {music_bar}, {music_with_progress}, {position}, {duration}, {system}, {time}, {cpu}, {ram}, {gpu}, {gpu_usage}, {gpu_temp}, {vram}, {artist}, {title}")
        token_help.setObjectName("subtitle")
        token_help.setWordWrap(True)
        template_layout.addWidget(token_help)
        layout.addWidget(templates)

        preview_group = QGroupBox("Live preview")
        preview_box = QVBoxLayout(preview_group)
        self.preview = QLabel()
        self.preview.setObjectName("preview")
        self.preview.setWordWrap(True)
        self.preview.setMinimumHeight(85)
        self.preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        self.preview.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        preview_box.addWidget(self.preview)
        local_hint = QLabel("Emoji icons in this preview are local images. VRChat receives Unicode text; some glyphs may not appear in-game.")
        local_hint.setObjectName("subtitle")
        local_hint.setWordWrap(True)
        preview_box.addWidget(local_hint)
        self.counter = QLabel()
        preview_box.addWidget(self.counter)
        layout.addWidget(preview_group)

        buttons = QVBoxLayout()
        self.send_btn = QPushButton("Send to VRChat")
        self.send_btn.setObjectName("primary")
        self.save_btn = QPushButton("Save settings")
        buttons.addWidget(self.send_btn, 2)
        buttons.addWidget(self.save_btn, 1)
        layout.addLayout(buttons)

        auto_row = QHBoxLayout()
        self.auto = QCheckBox("Automatically send status updates")
        self.auto.setChecked(self.settings.auto_send)
        auto_row.addWidget(self.auto)
        auto_row.addStretch()
        layout.addLayout(auto_row)
        self.auto_countdown = QLabel("Automatic sending disabled")
        self.auto_countdown.setObjectName("subtitle")
        layout.addWidget(self.auto_countdown)
        self.send_summary = QLabel("Automatic messages sent: 0")
        self.send_summary.setObjectName("subtitle")
        layout.addWidget(self.send_summary)
        self.notice = QLabel("Ready")
        self.notice.setObjectName("notice")
        self.notice.setWordWrap(True)
        layout.addWidget(self.notice)
        layout.addStretch()
        return page

    def _page_composer(self):
        page, layout = self._page("Visual Composer", "Drag rows to reorder. Each section can independently rotate through multiple lines.")
        self.section_mode = QCheckBox("Use visual sections for chatbox output (instead of the template editor)")
        self.section_mode.setChecked(self.settings.section_mode)
        layout.addWidget(self.section_mode)
        preset_row = QVBoxLayout()
        self.section_presets = QComboBox()
        self.section_presets.addItems(["Gaming", "Music", "AFK"])
        self.section_preset_btn = QPushButton("Load preset into composer")
        preset_row.addWidget(QLabel("Mode"))
        preset_row.addWidget(self.section_presets, 1)
        preset_row.addWidget(self.section_preset_btn)
        layout.addLayout(preset_row)
        self.section_list = QListWidget()
        self.section_list.setObjectName("sectionList")
        self.section_list.setStyleSheet("QListWidget#sectionList { padding: 4px; } QListWidget#sectionList::item { padding: 9px; margin: 1px; }")
        self.section_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.section_list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.section_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.section_list.setMinimumHeight(135)
        self.section_list.setMaximumHeight(225)
        layout.addWidget(self.section_list)
        row = QGridLayout()
        self.section_add = QPushButton("Add section")
        self.section_delete = QPushButton("Delete")
        self.section_up = QPushButton("Move up")
        self.section_down = QPushButton("Move down")
        for index, widget in enumerate((self.section_add, self.section_delete, self.section_up, self.section_down)):
            row.addWidget(widget, index // 2, index % 2)
        layout.addLayout(row)
        editor = QGroupBox("Selected section")
        form = QFormLayout(editor)
        self.section_enabled = QCheckBox("Show section")
        self.section_name = QLineEdit()
        self.section_text = QTextEdit()
        self.section_text.setMaximumHeight(80)
        self.section_text.setPlaceholderText("{status}, {music}, {time} or your own text")
        self.section_options = QTextEdit()
        self.section_options.setMaximumHeight(95)
        self.section_options.setPlaceholderText("Optional: one alternative message per line. Leave blank to use the default text.")
        self.section_interval = QSpinBox()
        self.section_interval.setRange(0, 3600)
        self.section_interval.setSuffix(" seconds (0 = no rotation)")
        form.addRow(self.section_enabled)
        form.addRow("Name", self.section_name)
        form.addRow("Default text", self.section_text)
        form.addRow("Rotating alternatives", self.section_options)
        form.addRow("Rotate every", self.section_interval)
        layout.addWidget(editor)
        self.section_hint = QLabel("Rotation affects the next message composed; auto-send controls when it reaches VRChat. Changes save automatically.")
        self.section_hint.setObjectName("subtitle")
        self.section_hint.setWordWrap(True)
        layout.addWidget(self.section_hint)
        layout.addStretch()
        self._reload_sections()
        return self._scroll_page(page)

    def _reload_sections(self, selected=0):
        self.section_list.blockSignals(True)
        self.section_list.clear()
        for i, section in enumerate(self.message_sections):
            item = QListWidgetItem(("✓ " if section['enabled'] else "○ ") + section['name'] +
                (f"  ·  {section['interval']}s rotation" if section['interval'] and len(section['options']) > 1 else ""))
            item.setData(Qt.ItemDataRole.UserRole, i)
            self.section_list.addItem(item)
        self.section_list.blockSignals(False)
        if self.message_sections:
            self.section_list.setCurrentRow(max(0, min(selected, len(self.message_sections)-1)))
        else:
            self._select_section(-1)

    def _sync_sections_from_list(self):
        # Rows preserve their identity through internal drag/drop, via original indices.
        if self.section_list.count() != len(self.message_sections):
            return
        old = list(self.message_sections)
        indices = [self.section_list.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.section_list.count())]
        if sorted(indices) != list(range(len(old))):
            return
        self.message_sections = [old[i] for i in indices]
        selected = self.section_list.currentRow()
        self._reload_sections(selected)
        self._queue_autosave()

    def _select_section(self, row):
        enabled = 0 <= row < len(self.message_sections)
        for widget in (self.section_enabled, self.section_name, self.section_text, self.section_options, self.section_interval):
            widget.blockSignals(True)
            widget.setEnabled(enabled)
        if enabled:
            section = self.message_sections[row]
            self.section_enabled.setChecked(section['enabled'])
            self.section_name.setText(section['name'])
            self.section_text.setPlainText(section['text'])
            self.section_options.setPlainText('\n'.join(section['options']))
            self.section_interval.setValue(section['interval'])
        else:
            self.section_name.clear()
            self.section_text.clear()
            self.section_options.clear()
        for widget in (self.section_enabled, self.section_name, self.section_text, self.section_options, self.section_interval):
            widget.blockSignals(False)

    def _section_edited(self, *_):
        row = self.section_list.currentRow()
        if not 0 <= row < len(self.message_sections):
            return
        item = self.message_sections[row]
        item.update(name=self.section_name.text()[:80] or 'Section',
            text=self.section_text.toPlainText()[:1024], enabled=self.section_enabled.isChecked(),
            interval=self.section_interval.value(),
            options=[line[:1024] for line in self.section_options.toPlainText().splitlines() if line.strip()][:20])
        self.section_list.item(row).setText(("✓ " if item['enabled'] else "○ ") + item['name'])
        self._refresh_preview()
        self._queue_autosave()

    def _add_section(self):
        self.message_sections.append(clean_sections([{'name': 'New section', 'text': '{status}', 'enabled': True, 'interval': 0}])[0])
        self._reload_sections(len(self.message_sections)-1)
        self._queue_autosave()

    def _delete_section(self):
        row = self.section_list.currentRow()
        if 0 <= row < len(self.message_sections):
            self.message_sections.pop(row)
            self._reload_sections(max(0, row-1))
            self._queue_autosave()
            self._refresh_preview()

    def _move_section(self, delta):
        row = self.section_list.currentRow()
        other = row + delta
        if 0 <= row < len(self.message_sections) and 0 <= other < len(self.message_sections):
            self.message_sections[row], self.message_sections[other] = self.message_sections[other], self.message_sections[row]
            self._reload_sections(other)
            self._queue_autosave()
            self._refresh_preview()

    def _load_section_preset(self):
        if self.message_sections:
            confirm = QMessageBox.question(self, 'Replace composer sections?',
                'Loading this preset replaces existing composer sections. Continue?')
            if confirm != QMessageBox.StandardButton.Yes:
                return
        self.message_sections = clean_sections(SECTION_PRESETS[self.section_presets.currentText()])
        self.section_composer.started = time.monotonic()
        self.section_mode.setChecked(True)
        self._reload_sections()
        self._refresh_preview()
        self._queue_autosave()

    def _page_statuses(self):
        page, layout = self._page("Statuses", "Select a saved status, or rotate through enabled statuses independently of OSC sending.")
        layout.setSpacing(8)

        group = QGroupBox("Saved statuses")
        group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        inner = QVBoxLayout(group)
        inner.setSpacing(8)
        self.status_list = QListWidget()
        self.status_list.setObjectName("savedStatuses")
        self.status_list.setMinimumHeight(105)
        self.status_list.setMaximumHeight(165)
        self.status_list.setStyleSheet("""
            QListWidget#savedStatuses { padding: 4px; }
            QListWidget#savedStatuses::item { padding: 9px 10px; margin: 1px; }
        """)
        inner.addWidget(self.status_list)
        buttons = QGridLayout()
        buttons.setSpacing(6)
        self.status_add_btn = QPushButton("Add")
        self.status_delete_btn = QPushButton("Delete")
        self.status_up_btn = QPushButton("Move up")
        self.status_down_btn = QPushButton("Move down")
        for index, btn in enumerate((self.status_add_btn, self.status_delete_btn, self.status_up_btn, self.status_down_btn)):
            buttons.addWidget(btn, index // 2, index % 2)
        inner.addLayout(buttons)
        layout.addWidget(group)

        editor = QGroupBox("Selected status editor")
        editor.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        form = QFormLayout(editor)
        form.setVerticalSpacing(7)
        self.status_name = QLineEdit()
        self.status_editor = QTextEdit()
        self.status_editor.setFixedHeight(78)
        self.status_apply_btn = QPushButton("Save changes to this status")
        form.addRow("Name", self.status_name)
        form.addRow("Message", self.status_editor)

        # A single compact rich-text preview stays immediately below the editor.
        # It uses bundled PNG assets, even where Qt cannot display emoji fonts.
        self.status_emoji_preview = QLabel()
        self.status_emoji_preview.setTextFormat(Qt.TextFormat.RichText)
        self.status_emoji_preview.setWordWrap(True)
        self.status_emoji_preview.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.status_emoji_preview.setFixedHeight(48)
        self.status_emoji_preview.setToolTip("Visual emoji preview; VRChat receives Unicode characters, not images.")
        self.status_emoji_preview.setStyleSheet(
            "background:#202a39; border:1px solid #455575; border-radius:7px; padding:5px 8px;"
        )
        form.addRow("Emoji preview", self.status_emoji_preview)
        self.status_emoji_btn = QPushButton("Insert emoji / emote")
        form.addRow(self.status_emoji_btn)
        form.addRow(self.status_apply_btn)
        layout.addWidget(editor)

        rotation = QGroupBox("Rotation")
        rotation.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        form = QFormLayout(rotation)
        form.setVerticalSpacing(7)
        self.rotate_status = QCheckBox("Automatically rotate through enabled statuses")
        self.rotate_status.setChecked(self.settings.rotate_statuses)
        self.rotation_interval = QSpinBox()
        self.rotation_interval.setRange(5, 3600)
        self.rotation_interval.setSuffix(" seconds")
        self.rotation_interval.setValue(self.settings.status_rotation_interval)
        self.rotation_notice = QLabel("Manual selection active")
        self.rotation_notice.setObjectName("subtitle")
        form.addRow(self.rotate_status)
        form.addRow("Switch every", self.rotation_interval)
        form.addRow(self.rotation_notice)
        layout.addWidget(rotation)
        note = QLabel("Selecting a status updates the preview immediately. Auto-send controls when VRChat receives it. Statuses are saved automatically.")
        note.setObjectName("subtitle")
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch(1)
        return page

    def _refresh_status_ui(self):
        self.status_list.blockSignals(True)
        self.status_list.clear()
        for profile in self.status_profiles:
            item = QListWidgetItem(profile.name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if profile.enabled else Qt.CheckState.Unchecked)
            item.setToolTip("Check to include this status in automatic rotation")
            self.status_list.addItem(item)
        if 0 <= self.selected_status < len(self.status_profiles):
            self.status_list.setCurrentRow(self.selected_status)
        self.status_list.blockSignals(False)
        self._select_status(self.selected_status)

    def _queue_autosave(self, *_):
        self._autosave_timer.start()

    def _edit_status_live(self, *_):
        if not 0 <= self.selected_status < len(self.status_profiles):
            return
        profile = self.status_profiles[self.selected_status]
        profile.name = self.status_name.text().strip()[:80] or "Unnamed"
        profile.text = self.status_editor.toPlainText()[:4096]
        item = self.status_list.item(self.selected_status)
        if item is not None:
            self.status_list.blockSignals(True)
            item.setText(profile.name)
            self.status_list.blockSignals(False)
        self.status.setPlainText(profile.text)
        self._refresh_status_emoji_preview()
        self._queue_autosave()

    def _refresh_status_emoji_preview(self):
        value = self.status_editor.toPlainText()
        self.status_emoji_preview.setText(rich_emoji_preview(value) if value else "Your status preview appears here")

    def _open_emoji_picker(self, editor: QTextEdit):
        """Emoji picker with visible text labels even if the OS lacks emoji glyphs."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Insert emoji / emote")
        dialog.resize(555, 475)
        layout = QVBoxLayout(dialog)
        hint = QLabel("Choose an emoji. Images are bundled with the application, no system emoji font required.")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        search = QLineEdit()
        search.setPlaceholderText("Search emojis (e.g. heart, music, fox)")
        layout.addWidget(search)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        panel = QWidget()
        grid = QGridLayout(panel)
        grid.setSpacing(6)
        scroll.setWidget(panel)
        layout.addWidget(scroll)

        def insert_emoji(value: str):
            # Keep focus/cursor selection from before the picker was opened.
            cursor = saved_cursor
            cursor.insertText(value)
            editor.setTextCursor(cursor)
            dialog.accept()

        saved_cursor = editor.textCursor()

        def populate(query=""):
            while grid.count():
                item = grid.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
            for i, (emoji, name) in enumerate(matching_emojis(query)):
                # Use a QToolButton's native icon painting, not child QLabel
                # overlays on a QPushButton (which KDE styles can obscure).
                button = QToolButton(panel)
                button.setObjectName("emojiTile")
                button.setText(name)
                button.setToolTip(f"Insert {name}: {emoji}")
                button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
                button.setIconSize(QSize(42, 42))
                button.setFixedSize(110, 91)
                icon_path = emoji_icon_path(emoji)
                if icon_path is not None:
                    button.setIcon(QIcon(str(icon_path)))
                button.setStyleSheet("""
                    QToolButton#emojiTile { background: #27364d; border: 1px solid #435575;
                        border-radius: 7px; padding: 4px; color: #f0f4ff; font-size: 11px; }
                    QToolButton#emojiTile:hover { background: #3b5281; border-color: #7896df; }
                """)
                button.clicked.connect(lambda checked=False, value=emoji: insert_emoji(value))
                grid.addWidget(button, i // 4, i % 4)
            if not matching_emojis(query):
                grid.addWidget(QLabel("No matching emojis"), 0, 0)

        search.textChanged.connect(populate)
        populate()
        dialog.exec()

    def _select_status(self, index: int):
        self.selected_status = index if 0 <= index < len(self.status_profiles) else -1
        profile = self.status_profiles[self.selected_status] if self.selected_status >= 0 else None
        for widget in (self.status_name, self.status_editor):
            widget.blockSignals(True)
        self.status_name.setText(profile.name if profile else "")
        self.status_editor.setPlainText(profile.text if profile else "")
        for widget in (self.status_name, self.status_editor):
            widget.blockSignals(False)
        self.status.setPlainText(profile.text if profile else "")
        self._refresh_status_emoji_preview()
        self._refresh_preview()
        self._queue_autosave()

    def _status_item_changed(self, item: QListWidgetItem):
        index = self.status_list.row(item)
        if 0 <= index < len(self.status_profiles):
            self.status_profiles[index].enabled = (item.checkState() == Qt.CheckState.Checked)
            self._update_rotation_notice()
            self._queue_autosave()

    def _add_status(self):
        name, ok = QInputDialog.getText(self, "New status", "Status name:")
        if not ok or not name.strip():
            return
        self.status_profiles.append(StatusProfile(name=name.strip()[:80], text="", enabled=True))
        self.selected_status = len(self.status_profiles) - 1
        self._refresh_status_ui()
        self.status_editor.setFocus()
        self._queue_autosave()

    def _delete_status(self):
        if self.selected_status < 0:
            return
        del self.status_profiles[self.selected_status]
        self.selected_status = min(self.selected_status, len(self.status_profiles) - 1)
        self._refresh_status_ui()
        self._queue_autosave()

    def _save_profile(self):
        if self.selected_status < 0:
            return
        profile = self.status_profiles[self.selected_status]
        profile.name = self.status_name.text().strip()[:80] or "Unnamed"
        profile.text = self.status_editor.toPlainText()[:4096]
        self._refresh_status_ui()
        self._save_settings()

    def _move_status(self, delta: int):
        i = self.selected_status
        j = i + delta
        if 0 <= i < len(self.status_profiles) and 0 <= j < len(self.status_profiles):
            self.status_profiles[i], self.status_profiles[j] = self.status_profiles[j], self.status_profiles[i]
            self.selected_status = j
            self._refresh_status_ui()
            self._queue_autosave()

    def _update_rotation_timer(self, *_):
        self.status_rotator.configure(self.rotate_status.isChecked(), self.rotation_interval.value())
        self._update_rotation_notice()

    def _update_rotation_notice(self):
        seconds = self.status_rotator.remaining()
        active = sum(profile.enabled for profile in self.status_profiles)
        if seconds is None:
            self.rotation_notice.setText("Manual selection — rotation disabled")
        elif active < 2:
            self.rotation_notice.setText("Enable at least two statuses to rotate")
        else:
            self.rotation_notice.setText(f"Next status in {seconds}s · {active} enabled")

    def _rotation_tick(self):
        if self.status_rotator.advance():
            next_index = next_enabled_index(self.status_profiles, self.selected_status)
            if next_index >= 0 and next_index != self.selected_status:
                self.selected_status = next_index
                self._refresh_status_ui()
        self._update_rotation_notice()

    def _page_music(self):
        page, layout = self._page("Music", "Displays currently playing MPRIS media from Linux players.")
        group = QGroupBox("Now playing")
        inner = QVBoxLayout(group)
        self.music_track = QLabel("No active media")
        self.music_track.setObjectName("stat")
        self.music_track.setWordWrap(True)
        self.music_player = QLabel("Install playerctl to discover music players.")
        self.music_player.setObjectName("subtitle")
        self.music_enabled = QLabel()
        inner.addWidget(self.music_track)
        inner.addWidget(self.music_player)
        inner.addWidget(self.music_enabled)
        player_row = QVBoxLayout()
        player_row.addWidget(QLabel("Music source"))
        self.player_select = QComboBox()
        self.player_select.addItem("Auto — first playing app", "Auto")
        if self.settings.music_player != "Auto":
            self.player_select.addItem(self.settings.music_player + " (saved)", self.settings.music_player)
            self.player_select.setCurrentIndex(1)
        player_row.addWidget(self.player_select, 1)
        self.scan_players_btn = QPushButton("Scan apps")
        player_row.addWidget(self.scan_players_btn)
        inner.addLayout(player_row)
        self.show_paused = QCheckBox("Show paused tracks in chatbox")
        self.show_paused.setChecked(self.settings.music_show_paused)
        inner.addWidget(self.show_paused)
        self.music_fallback = QCheckBox("If selected player closes, fall back to another playing app")
        self.music_fallback.setChecked(self.settings.music_fallback_to_auto)
        inner.addWidget(self.music_fallback)
        self.album_art = QLabel("No local album artwork")
        self.album_art.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.album_art.setMinimumHeight(145)
        self.album_art.setMaximumHeight(180)
        inner.addWidget(self.album_art)
        self.player_info = QLabel("Auto prefers a playing app; selecting an app pins it as the source.")
        self.player_info.setObjectName("subtitle")
        self.player_info.setWordWrap(True)
        inner.addWidget(self.player_info)
        self.music_progress = QProgressBar()
        self.music_progress.setRange(0, 1000)
        self.music_progress.setValue(0)
        self.music_progress.setTextVisible(False)
        self.music_progress.setMinimumHeight(14)
        self.music_progress.setStyleSheet("QProgressBar {border: 1px solid #455575; border-radius: 6px; background: #202a39;} QProgressBar::chunk {background: #6880f0; border-radius: 5px;}")
        self.music_progress_text = QLabel("Playback progress unavailable")
        self.music_progress_text.setObjectName("subtitle")
        inner.addWidget(self.music_progress)
        inner.addWidget(self.music_progress_text)
        controls = QGridLayout()
        self.previous_btn = QPushButton("⏮ Previous")
        self.play_pause_btn = QPushButton("⏯ Play / pause")
        self.next_btn = QPushButton("⏭ Next")
        for index, button in enumerate((self.previous_btn, self.play_pause_btn, self.next_btn)):
            controls.addWidget(button, index // 2, index % 2)
        inner.addLayout(controls)
        layout.addWidget(group)
        hint = QLabel("Compatible with Spotify, browser media, and other players exposing the MPRIS interface. Only actively playing tracks appear in chatbox messages.")
        hint.setWordWrap(True)
        hint.setObjectName("subtitle")
        layout.addWidget(hint)
        self.refresh_music_btn = QPushButton("Refresh music")
        layout.addWidget(self.refresh_music_btn)
        layout.addStretch()
        return page

    def _page_system(self):
        page, layout = self._page("System monitoring", "Live local CPU and memory data. No information is uploaded to a server.")
        group = QGroupBox("System stats")
        inner = QVBoxLayout(group)
        self.cpu_label = QLabel("CPU: --")
        self.ram_label = QLabel("RAM: --")
        self.ram_details_label = QLabel("RAM: waiting for first sample")
        self.uptime_label = QLabel("System uptime: --")
        self.system_health_label = QLabel("Monitor is starting...")
        for label in (self.cpu_label, self.ram_label):
            label.setObjectName("stat")
            inner.addWidget(label)
        for label in (self.ram_details_label, self.uptime_label, self.system_health_label):
            label.setObjectName("subtitle")
            inner.addWidget(label)
        self.gpu_label = QLabel("GPU: detecting...")
        self.gpu_label.setWordWrap(True)
        inner.addWidget(self.gpu_label)
        layout.addWidget(group)
        self.refresh_system_btn = QPushButton("Refresh system stats")
        layout.addWidget(self.refresh_system_btn)
        layout.addStretch()
        return page

    def _page_diagnostics(self):
        page, layout = self._page("OSC Diagnostics", "Shows outbound UDP attempts, not VRChat delivery confirmation.")
        self.osc_destination_label = QLabel("Destination: pending")
        self.osc_destination_label.setWordWrap(True)
        layout.addWidget(self.osc_destination_label)
        self.osc_log = QTextEdit()
        self.osc_log.setReadOnly(True)
        self.osc_log.setMinimumHeight(250)
        self.osc_log.setPlaceholderText("No messages sent this session.")
        layout.addWidget(self.osc_log)
        clear_btn = QPushButton("Clear session history")
        clear_btn.clicked.connect(self._clear_diagnostics)
        layout.addWidget(clear_btn)
        hint = QLabel("UDP is connectionless: 'sent' only means the local send call succeeded. It cannot establish VRChat receipt.")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        layout.addStretch()
        return page

    def _clear_diagnostics(self):
        self.send_history = SendHistory()
        self.osc_log.clear()

    def _update_diagnostics(self):
        self.osc_destination_label.setText(f"Target: {self.host.text().strip()}:{self.port.value()} UDP /chatbox/input")
        self.osc_log.setPlainText("\n".join(self.send_history.lines()))

    def _export_settings_backup(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Export settings backup", str(Path.home() / "flys-osc-chatbox-backup.json"), "JSON (*.json)")
        if not filename:
            return
        try:
            export_backup(Path(filename), self._collect_settings())
            self._notice(f"Settings backup exported: {filename}")
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "Backup failed", str(exc))

    def _restore_settings_backup(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Import settings backup", str(Path.home()), "JSON (*.json)")
        if not filename:
            return
        answer = QMessageBox.question(self, "Restore backup", "This will replace current settings and create a pre-import safety copy. The app will restart the next time you launch it. Continue?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self._autosave_timer.stop()
            restore_backup(Path(filename))
            QMessageBox.information(self, "Backup restored", "Settings restored. Please quit and relaunch the app to load the restored settings. Do not save settings from this open window.")
            self._real_close = True
            self._restoring_settings = True
            self._music_executor.shutdown(wait=False, cancel_futures=True)
            self._player_scan_executor.shutdown(wait=False, cancel_futures=True)
            self._gpu_executor.shutdown(wait=False, cancel_futures=True)
            self._update_executor.shutdown(wait=False, cancel_futures=True)
            self.app.quit()
        except (OSError, ValueError, TypeError) as exc:
            QMessageBox.warning(self, "Restore failed", str(exc))

    def _page_integrations(self):
        page, layout = self._page("Integrations", "Choose which sources are allowed in the outgoing chatbox message.")
        group = QGroupBox("Active integrations")
        inner = QVBoxLayout(group)
        self.clock = QCheckBox("Clock — {time}")
        self.clock.setChecked(self.settings.show_clock)
        self.system = QCheckBox("CPU / RAM — {system}, {cpu}, {ram}")
        self.system.setChecked(self.settings.show_system)
        self.gpu_checkbox = QCheckBox("GPU monitoring — {gpu}, {gpu_usage}, {gpu_temp}, {vram}")
        self.gpu_checkbox.setChecked(self.settings.show_gpu)
        self.music = QCheckBox("Now playing — {music}, {artist}, {title}")
        self.music.setChecked(self.settings.show_music)
        self.include_music_progress = QCheckBox("Include playback time in {music} when available")
        self.include_music_progress.setChecked(self.settings.show_music_progress)
        for checkbox in (self.clock, self.system, self.gpu_checkbox, self.music, self.include_music_progress):
            inner.addWidget(checkbox)
        styles = QVBoxLayout()
        styles.addWidget(QLabel("VRChat progress bar style"))
        self.music_bar_style = QComboBox()
        self.music_bar_style.addItems(["Blocks", "Squares", "Circles", "ASCII", "Custom"])
        self.music_bar_style.setCurrentText(self.settings.music_bar_style)
        styles.addWidget(self.music_bar_style)
        inner.addLayout(styles)
        custom = QVBoxLayout()
        custom.addWidget(QLabel("Filled"))
        self.bar_filled = QLineEdit(self.settings.music_bar_filled)
        self.bar_filled.setMaxLength(4)
        custom.addWidget(self.bar_filled)
        custom.addWidget(QLabel("Empty"))
        self.bar_empty = QLineEdit(self.settings.music_bar_empty)
        self.bar_empty.setMaxLength(4)
        custom.addWidget(self.bar_empty)
        custom.addWidget(QLabel("Width"))
        self.bar_width = QSpinBox()
        self.bar_width.setRange(3, 24)
        self.bar_width.setValue(self.settings.music_bar_width)
        custom.addWidget(self.bar_width)
        inner.addLayout(custom)
        hint = QLabel("Choose Custom to use your symbols. Use {music_bar} in the Chatbox template.")
        hint.setWordWrap(True)
        hint.setObjectName("subtitle")
        inner.addWidget(hint)
        layout.addWidget(group)
        detail = QLabel("More integrations (Discord, VR headset information, weather, and speech) will be separate optional modules in later releases. They are not active in v0.4.")
        detail.setWordWrap(True)
        detail.setObjectName("subtitle")
        layout.addWidget(detail)
        layout.addStretch()
        return page

    def _page_settings(self):
        page, layout = self._page("Settings", "VRChat OSC destination, update frequency and window behavior.")
        connection = QGroupBox("VRChat OSC destination")
        form = QFormLayout(connection)
        self.host = QLineEdit(self.settings.host)
        self.host.setPlaceholderText("127.0.0.1")
        self.port = QSpinBox()
        self.port.setRange(1, 65535)
        self.port.setValue(self.settings.port)
        form.addRow("Host / IP", self.host)
        form.addRow("UDP port", self.port)
        layout.addWidget(connection)
        appearance = QGroupBox("Appearance")
        appearance_form = QFormLayout(appearance)
        self.theme_select = QComboBox()
        self.theme_select.addItems(THEMES.keys())
        self.theme_select.setCurrentText(self.settings.theme)
        self.theme_select.currentTextChanged.connect(self._theme_changed)
        appearance_form.addRow("Application theme", self.theme_select)
        appearance_form.addRow(QLabel("Theme changes apply immediately and save automatically."))
        layout.addWidget(appearance)
        behavior = QGroupBox("Behavior")
        form = QFormLayout(behavior)
        self.interval = QSpinBox()
        self.interval.setRange(10, 600)
        self.interval.setSuffix(" seconds")
        self.interval.setValue(self.settings.auto_interval)
        self.minimize_to_tray = QCheckBox("Minimize to system tray on close")
        self.minimize_to_tray.setChecked(self.settings.minimize_to_tray)
        form.addRow("Auto-send interval", self.interval)
        self.only_changed = QCheckBox("Only auto-send when message changes")
        self.only_changed.setChecked(self.settings.only_send_when_changed)
        form.addRow(self.only_changed)
        form.addRow(self.minimize_to_tray)
        layout.addWidget(behavior)
        update_group = QGroupBox("Software updates")
        update_layout = QVBoxLayout(update_group)
        self.update_version = QLabel(f"Installed application version: {APP_VERSION}")
        update_layout.addWidget(self.update_version)
        self.check_updates_checkbox = QCheckBox("Check GitHub for updates when the app starts")
        self.check_updates_checkbox.setChecked(self.settings.check_updates)
        update_layout.addWidget(self.check_updates_checkbox)
        self.auto_download_checkbox = QCheckBox("Automatically download verified Fedora RPMs (never install silently)")
        self.auto_download_checkbox.setChecked(self.settings.auto_download_updates)
        update_layout.addWidget(self.auto_download_checkbox)
        self.update_status = QLabel("No update check performed yet")
        self.update_status.setWordWrap(True)
        update_layout.addWidget(self.update_status)
        self.update_details = QLabel("Release details will appear after checking for updates.")
        self.update_details.setTextFormat(Qt.TextFormat.PlainText)
        self.update_details.setWordWrap(True)
        self.update_details.setMaximumHeight(165)
        update_layout.addWidget(self.update_details)
        self.update_check_button = QPushButton("Check for updates")
        self.update_install_button = QPushButton("Download and install update…")
        self.update_install_button.setEnabled(False)
        self.update_page_button = QPushButton("Open GitHub releases")
        update_layout.addWidget(self.update_check_button)
        update_layout.addWidget(self.update_install_button)
        update_layout.addWidget(self.update_page_button)
        hint = QLabel("RPM updates require your confirmation and Fedora administrator authentication. Other install types open GitHub for manual updates. The app never installs updates silently.")
        hint.setObjectName("subtitle")
        hint.setWordWrap(True)
        update_layout.addWidget(hint)
        layout.addWidget(update_group)
        backup_group = QGroupBox("Backup and restore")
        backup_layout = QVBoxLayout(backup_group)
        backup_hint = QLabel("Export all profiles, composer layouts, theme, music preferences and OSC settings. Import requires restarting the application.")
        backup_hint.setWordWrap(True)
        backup_layout.addWidget(backup_hint)
        self.backup_export_btn = QPushButton("Export settings backup...")
        self.backup_import_btn = QPushButton("Import settings backup...")
        backup_layout.addWidget(self.backup_export_btn)
        backup_layout.addWidget(self.backup_import_btn)
        layout.addWidget(backup_group)
        warning = QLabel("Auto-send repeats at the selected interval by default. Turn on only-when-changed to suppress identical messages. UDP cannot confirm VRChat delivery.")
        warning.setWordWrap(True)
        warning.setObjectName("subtitle")
        layout.addWidget(warning)
        self.settings_save_btn = QPushButton("Save all settings")
        self.settings_save_btn.setObjectName("primary")
        layout.addWidget(self.settings_save_btn)
        layout.addStretch()
        return page

    def _apply_theme(self, name: str):
        self.setStyleSheet(stylesheet(name))
        # These widgets previously had fixed dark-only styles, so refresh them too.
        if hasattr(self, "music_progress"):
            self.music_progress.setStyleSheet("")
        if hasattr(self, "status_list"):
            self.status_list.setStyleSheet("")
        if hasattr(self, "status_emoji_preview"):
            self.status_emoji_preview.setStyleSheet("")

    def _theme_changed(self, name: str):
        self._apply_theme(name)
        self._autosave_timer.start()

    def _build_tray(self):
        self.tray = None
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.app.setQuitOnLastWindowClosed(True)
            return
        icon = self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon)
        self.tray = QSystemTrayIcon(icon, self)
        self.tray.setToolTip("Fly's OSC Chat Box")
        menu = QMenu(self)
        show = QAction("Show Fly's OSC Chat Box", self)
        show.triggered.connect(self._show_window)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._quit)
        menu.addAction(show)
        menu.addAction(quit_action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda reason: self._show_window() if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
        self.tray.show()

    def _wire_signals(self):
        self.status.textChanged.connect(self._refresh_preview)
        self.status_list.currentRowChanged.connect(self._select_status)
        self.status_name.textChanged.connect(self._edit_status_live)
        self.status_editor.textChanged.connect(self._edit_status_live)
        self.status_emoji_btn.clicked.connect(lambda: self._open_emoji_picker(self.status_editor))
        self.template_emoji_btn.clicked.connect(lambda: self._open_emoji_picker(self.template))
        self.status_list.itemChanged.connect(self._status_item_changed)
        self.status_add_btn.clicked.connect(self._add_status)
        self.status_delete_btn.clicked.connect(self._delete_status)
        self.status_apply_btn.clicked.connect(self._save_profile)
        self.status_up_btn.clicked.connect(lambda: self._move_status(-1))
        self.status_down_btn.clicked.connect(lambda: self._move_status(1))
        self.rotate_status.toggled.connect(self._update_rotation_timer)
        self.rotation_interval.valueChanged.connect(self._update_rotation_timer)
        self.section_mode.toggled.connect(self._refresh_preview)
        self.section_mode.toggled.connect(self._queue_autosave)
        self.section_presets.currentIndexChanged.connect(lambda *_: None)
        self.section_preset_btn.clicked.connect(self._load_section_preset)
        self.section_list.currentRowChanged.connect(self._select_section)
        self.section_list.model().rowsMoved.connect(lambda *_: self._sync_sections_from_list())
        self.section_add.clicked.connect(self._add_section)
        self.section_delete.clicked.connect(self._delete_section)
        self.section_up.clicked.connect(lambda: self._move_section(-1))
        self.section_down.clicked.connect(lambda: self._move_section(1))
        self.section_enabled.toggled.connect(self._section_edited)
        self.section_name.textChanged.connect(self._section_edited)
        self.section_text.textChanged.connect(self._section_edited)
        self.section_options.textChanged.connect(self._section_edited)
        self.section_interval.valueChanged.connect(self._section_edited)
        self.template.textChanged.connect(self._refresh_preview)
        self.presets.currentIndexChanged.connect(self._apply_preset)
        for checkbox in (self.clock, self.system, self.gpu_checkbox, self.music, self.include_music_progress):
            checkbox.toggled.connect(self._integration_changed)
        self.send_btn.clicked.connect(self._manual_send)
        self.save_btn.clicked.connect(self._save_settings)
        self.settings_save_btn.clicked.connect(self._save_settings)
        self.update_check_button.clicked.connect(self._check_for_updates)
        self.update_install_button.clicked.connect(self._start_update_install)
        self.update_page_button.clicked.connect(lambda: __import__('webbrowser').open(RELEASES_URL))
        self.check_updates_checkbox.toggled.connect(self._queue_autosave)
        self.auto_download_checkbox.toggled.connect(self._queue_autosave)
        self.backup_export_btn.clicked.connect(self._export_settings_backup)
        self.backup_import_btn.clicked.connect(self._restore_settings_backup)
        self.music_fallback.toggled.connect(self._queue_autosave)
        self.auto.toggled.connect(self._update_auto_timer)
        self.only_changed.toggled.connect(self._auto_mode_changed)
        self.interval.valueChanged.connect(self._update_auto_timer)
        self.refresh_music_btn.clicked.connect(self._poll_music)
        self.scan_players_btn.clicked.connect(self._scan_players)
        self.player_select.currentIndexChanged.connect(self._player_selection_changed)
        self.show_paused.toggled.connect(self._music_display_changed)
        self.insert_variable.currentIndexChanged.connect(self._insert_selected_variable)
        self.add_separator_btn.clicked.connect(lambda: self._insert_into_template(" | "))
        self.add_newline_btn.clicked.connect(lambda: self._insert_into_template("\n"))
        self.saved_layouts.currentIndexChanged.connect(self._load_saved_layout)
        self.save_layout_btn.clicked.connect(self._save_named_layout)
        self.delete_layout_btn.clicked.connect(self._delete_named_layout)
        self.previous_btn.clicked.connect(lambda: self._music_control("previous"))
        self.play_pause_btn.clicked.connect(lambda: self._music_control("play-pause"))
        self.next_btn.clicked.connect(lambda: self._music_control("next"))
        self.music_bar_style.currentTextChanged.connect(self._refresh_preview)
        for control in (self.bar_filled, self.bar_empty):
            control.textChanged.connect(self._refresh_preview)
        self.bar_width.valueChanged.connect(self._refresh_preview)
        for control in (self.bar_filled, self.bar_empty):
            control.textChanged.connect(self._queue_autosave)
        self.bar_width.valueChanged.connect(self._queue_autosave)
        self.music_bar_style.currentTextChanged.connect(self._queue_autosave)
        self.template.textChanged.connect(self._queue_autosave)
        self.rotate_status.toggled.connect(self._queue_autosave)
        self.rotation_interval.valueChanged.connect(self._queue_autosave)
        self.refresh_system_btn.clicked.connect(self._poll_system)
        self.host.textChanged.connect(self._destination_changed)
        self.port.valueChanged.connect(self._destination_changed)

    def _reload_layout_names(self):
        previous = self.saved_layouts.currentText() if hasattr(self, "saved_layouts") else ""
        self.saved_layouts.blockSignals(True)
        self.saved_layouts.clear()
        self.saved_layouts.addItem("Saved layouts…")
        self.saved_layouts.addItems(sorted(self.custom_layouts, key=str.casefold))
        match = self.saved_layouts.findText(previous)
        self.saved_layouts.setCurrentIndex(match if match >= 0 else 0)
        self.saved_layouts.blockSignals(False)

    def _insert_into_template(self, value):
        self.template.insertPlainText(value)
        self.template.setFocus()

    def _insert_selected_variable(self, index):
        value = self.insert_variable.itemData(index)
        if value:
            self._insert_into_template(value)
        self.insert_variable.setCurrentIndex(0)

    def _load_saved_layout(self, index):
        name = self.saved_layouts.currentText()
        if index > 0 and name in self.custom_layouts:
            self.template.setPlainText(self.custom_layouts[name])

    def _save_named_layout(self):
        name, ok = QInputDialog.getText(self, "Save message layout", "Layout name:")
        name = name.strip()[:60]
        if ok and name:
            self.custom_layouts[name] = self.template.toPlainText()
            self._reload_layout_names()
            self.saved_layouts.setCurrentText(name)
            self._save_settings()

    def _delete_named_layout(self):
        name = self.saved_layouts.currentText()
        if name in self.custom_layouts:
            del self.custom_layouts[name]
            self._reload_layout_names()
            self._save_settings()

    def _music_display_changed(self, *_):
        self._refresh_preview()
        self._queue_autosave()

    def _player_selection_changed(self, *_):
        self.track = Track()
        self._refresh_preview()
        self._queue_autosave()
        self._poll_music()

    def _scan_players(self):
        if self._player_scan_future is None:
            self.player_info.setText("Scanning MPRIS apps…")
            self._player_scan_future = self._player_scan_executor.submit(list_players)

    def _finish_player_scan(self):
        if self._player_scan_future is None or not self._player_scan_future.done():
            return
        try:
            players = self._player_scan_future.result()
        except Exception:
            players = []
        self._player_scan_future = None
        previous = self.player_select.currentData() or "Auto"
        self.player_select.blockSignals(True)
        self.player_select.clear()
        self.player_select.addItem("Auto — first playing app", "Auto")
        for name in players:
            self.player_select.addItem(name, name)
        if previous != "Auto" and previous not in players:
            self.player_select.addItem(previous + " (offline)", previous)
        index = self.player_select.findData(previous)
        self.player_select.setCurrentIndex(max(0, index))
        self.player_select.blockSignals(False)
        self.player_info.setText(f"{len(players)} MPRIS app(s) found. Browser tabs may appear as separate instances.")

    def _apply_preset(self, index):
        if index > 0:
            self.template.setPlainText(PRESETS[self.presets.currentText()])

    def _integration_changed(self, *_):
        self._poll_system()
        self._poll_music()
        self._refresh_preview()

    def _poll_system(self):
        try:
            self.stats = self.monitor.sample()
            self.cpu_label.setText(f"CPU: {self.stats.cpu}%")
            self.ram_label.setText(f"RAM: {self.stats.ram}%")
            self.ram_details_label.setText(
                f"Memory in use: {self.stats.used_gib:.1f} / {self.stats.total_gib:.1f} GiB"
            )
            hours, rem = divmod(self.stats.uptime_seconds, 3600)
            self.uptime_label.setText(f"System uptime: {hours}h {rem // 60}m")
            self.system_health_label.setText(
                "Monitoring active (2-second refresh) · Chatbox system integration: "
                + ("enabled" if self.system.isChecked() else "disabled")
            )
        except Exception as exc:
            self.system_health_label.setText(f"Monitoring error: {exc}")
        if self._gpu_future is not None and self._gpu_future.done():
            try:
                self.gpu_stats = self._gpu_future.result()
            except Exception:
                self.gpu_stats = GPUStats()
            self._gpu_future = None
        if self._gpu_future is None:
            self._gpu_future = self._gpu_executor.submit(gpu_snapshot)
        self.gpu_label.setText("GPU: " + (self.gpu_stats.name or "not detected") +
            (f" · {self.gpu_stats.usage_percent}% usage" if self.gpu_stats.usage_percent is not None else "") +
            (f" · {self.gpu_stats.temperature_c:.1f} °C" if self.gpu_stats.temperature_c is not None else "") +
            (f" · VRAM {self.gpu_stats.vram_used_mib}/{self.gpu_stats.vram_total_mib} MiB" if self.gpu_stats.vram_used_mib is not None and self.gpu_stats.vram_total_mib is not None else ""))
        self._refresh_preview()

    def _music_control(self, action: str):
        player = self.track.player
        if not player:
            self._notice("No media player detected. Enable Now Playing under Integrations.")
            return
        # A dedicated worker prevents playback commands from blocking the Qt UI.
        if not hasattr(self, "_control_executor"):
            self._control_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="music-controls")
        self._control_executor.submit(control_player, player, action)
        QTimer.singleShot(750, self._poll_music)

    def _poll_music(self):
        # subprocess calls must not block the Qt event loop: otherwise auto-send
        # appears frozen while playerctl times out.
        if self._music_future is not None:
            if self._music_future.done():
                try:
                    candidate = self._music_future.result() if self.music.isChecked() else Track()
                    requested = self.player_select.currentData() or "Auto"
                    self.track = candidate if (self._player_selected_for_poll == requested and
                                               (requested == "Auto" or candidate.player == requested or self.music_fallback.isChecked())) else Track()
                except Exception:
                    self.track = Track()
                self._music_future = None
                self.music_track.setText(self.track.display or "No active media")
                self.music_player.setText(
                    f"Player: {self.track.player or 'none'} · "
                    + ("Playing" if self.track.playing else "Not playing")
                )
                self._refresh_music_progress()
                self._update_album_art()
                self._refresh_preview()
            else:
                return
        if self.music.isChecked():
            self._player_selected_for_poll = self.player_select.currentData() or "Auto"
            self._music_future = self._music_executor.submit(current_track, self._player_selected_for_poll, self.music_fallback.isChecked())
        else:
            self.track = Track()
            self.music_track.setText("Music integration disabled")
            self.music_player.setText("Enable under Integrations")
            self._update_album_art()
        self.music_enabled.setText("Chatbox integration: " + ("enabled" if self.music.isChecked() else "disabled"))
        self._refresh_music_progress()
        self._refresh_preview()

    def _refresh_music_progress(self):
        """Animate the visible progress bar between MPRIS polls, including pause."""
        if self.music.isChecked() and self.track.has_progress and self.track.title:
            self.music_progress.setEnabled(True)
            self.music_progress.setValue(round(self.track.progress() * 1000))
            self.music_progress_text.setText(
                self.track.progress_text() + (" · Playing" if self.track.playing else " · Paused")
            )
        else:
            self.music_progress.setValue(0)
            self.music_progress.setEnabled(False)
            self.music_progress_text.setText("Playback progress unavailable (or music disabled)")

    def _update_album_art(self):
        """Update only when the track artwork URL changes (not on 250ms ticks)."""
        url = self.track.art_url if self.music.isChecked() else ""
        if getattr(self, "_last_art_url", None) == url:
            return
        self._last_art_url = url
        from PySide6.QtGui import QPixmap
        path = local_album_art(url)
        if path:
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                self.album_art.setPixmap(pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                self.album_art.setText("")
                return
        self.album_art.setPixmap(QPixmap())
        self.album_art.setText("No local album artwork" if not url else "Remote artwork not downloaded")

    def _variables(self) -> dict[str, str]:
        available = (self.music.isChecked() and (self.track.playing or self.show_paused.isChecked())
                     and bool(self.track.display))
        progress_available = available and self.track.has_progress
        progress = self.track.progress_text() if progress_available else ""
        bar = styled_progress_bar(self.track, self.music_bar_style.currentText(), self.bar_width.value(), self.bar_filled.text(), self.bar_empty.text()) if progress_available else ""
        music = "♫ " + self.track.display if available else ""
        if music and progress and self.include_music_progress.isChecked():
            music += " (" + progress + ")"
        return {
            "status": self.status.toPlainText().strip(),
            "time": datetime.now().strftime("%H:%M") if self.clock.isChecked() else "",
            "system": self.stats.display if self.system.isChecked() else "",
            "cpu": str(self.stats.cpu) if self.system.isChecked() else "",
            "ram": str(self.stats.ram) if self.system.isChecked() else "",
            "gpu": self.gpu_stats.display if self.gpu_checkbox.isChecked() else "",
            "gpu_usage": str(self.gpu_stats.usage_percent) if self.gpu_checkbox.isChecked() and self.gpu_stats.usage_percent is not None else "",
            "gpu_temp": f"{self.gpu_stats.temperature_c:.0f}" if self.gpu_checkbox.isChecked() and self.gpu_stats.temperature_c is not None else "",
            "vram": f"{self.gpu_stats.vram_used_mib}/{self.gpu_stats.vram_total_mib} MiB" if self.gpu_checkbox.isChecked() and self.gpu_stats.vram_used_mib is not None and self.gpu_stats.vram_total_mib is not None else "",
            "music": music,
            "music_progress": progress,
            "music_bar": bar,
            "music_bar_custom": bar,
            "music_with_progress": ("♫ " + self.track.display + " " + bar + " " + progress).strip() if progress_available else music,
            "position": self.track.progress_text().split(" / ")[0] if progress_available else "",
            "duration": self.track.progress_text().split(" / ")[1] if progress_available else "",
            "artist": self.track.artist if available else "",
            "title": self.track.title if available else "",
        }

    def _compose(self) -> str:
        if self.section_mode.isChecked():
            return self.section_composer.render(self.message_sections, self._variables())
        return render_template(self.template.toPlainText(), self._variables())

    def _clock_tick(self):
        self._rotation_tick()
        self._refresh_music_progress()
        self._finish_player_scan()
        self._refresh_preview()
        if self.scheduler.advance():
            self._automatic_send()
        self._update_countdown()

    def _update_countdown(self):
        seconds = self.scheduler.seconds_remaining()
        if seconds is None:
            self.auto_countdown.setText("Automatic sending disabled")
        else:
            self.auto_countdown.setText(
                f"Next automatic send in {seconds}s · every {self.scheduler.interval_seconds}s"
            )

    def _auto_mode_changed(self, *_):
        self.last_sent = None
        self._last_destination = None

    def _refresh_preview(self):
        message = self._compose()
        self.preview.setTextFormat(Qt.TextFormat.RichText)
        self.preview.setText(rich_emoji_preview(message) if message else "Your chatbox message will appear here.")
        self.counter.setText(f"{len(message)} / {MAX_CHARS} characters (truncated at 144)")
        invalid = unknown_variables(self.template.toPlainText()) if not self.section_mode.isChecked() else set()
        if invalid:
            self.counter.setText(self.counter.text() + " · Unknown: " + ", ".join(sorted(invalid)))

    def _destination_changed(self, *_):
        self.last_sent = None
        self._last_destination = None
        self._update_diagnostics()

    def _manual_send(self):
        self._send(manual=True)

    def _automatic_send(self):
        if self.auto.isChecked():
            self._send(manual=False)

    def _send(self, *, manual: bool):
        message = self._compose()
        destination = (self.host.text().strip(), self.port.value())
        if not message:
            self._notice("Nothing to send. Enter status text or enable an integration.")
            return
        if not self.section_mode.isChecked() and unknown_variables(self.template.toPlainText()):
            self._notice("Fix unknown template variables before sending.")
            return
        if not manual and self.only_changed.isChecked() and message == self.last_sent and destination == self._last_destination:
            return
        try:
            OSCClient(*destination).send_chatbox(message, notify=manual)
        except (OSError, ValueError) as exc:
            self.send_history.add("Manual" if manual else "Auto", *destination, message, error=str(exc))
            self._update_diagnostics()
            self._notice(f"OSC error: {exc}")
            if manual:
                QMessageBox.warning(self, "OSC send error", str(exc))
            return
        self.send_history.add("Manual" if manual else "Auto", *destination, message)
        self._update_diagnostics()
        self.last_sent = message
        self._last_destination = destination
        if not manual:
            self.send_count += 1
            self.send_summary.setText(f"Automatic messages sent this session: {self.send_count}")
        kind = "Manual" if manual else "Automatic"
        self._notice(f"{kind} UDP packet sent to {destination[0]}:{destination[1]} at {datetime.now():%H:%M:%S} (delivery unconfirmed).")

    def _notice(self, message: str):
        self.notice.setText(message)
        self.statusBar().showMessage(message)

    def _update_auto_timer(self, *_):
        # On/off and interval changes reset the monotonic deadline.
        self.scheduler.configure(self.auto.isChecked(), self.interval.value())
        self._update_countdown()

    def _collect_settings(self) -> Settings:
        return Settings(
            host=self.host.text().strip() or "127.0.0.1",
            port=self.port.value(), status_text=self.status.toPlainText(),
            show_clock=self.clock.isChecked(), show_system=self.system.isChecked(),
            show_music=self.music.isChecked(), music_player=self.player_select.currentData() or "Auto",
            music_show_paused=self.show_paused.isChecked(), music_fallback_to_auto=self.music_fallback.isChecked(), show_gpu=self.gpu_checkbox.isChecked(), custom_layouts=dict(self.custom_layouts),
            show_music_progress=self.include_music_progress.isChecked(), music_bar_style=self.music_bar_style.currentText(),
            music_bar_filled=self.bar_filled.text() or "◆", music_bar_empty=self.bar_empty.text() or "◇",
            music_bar_width=self.bar_width.value(), auto_send=self.auto.isChecked(),
            only_send_when_changed=self.only_changed.isChecked(),
            auto_interval=self.interval.value(), minimize_to_tray=self.minimize_to_tray.isChecked(),
            template=self.template.toPlainText(),
            status_profiles=[{"name": p.name, "text": p.text, "enabled": p.enabled} for p in self.status_profiles],
            selected_status=self.selected_status, rotate_statuses=self.rotate_status.isChecked(),
            status_rotation_interval=self.rotation_interval.value(),
            section_mode=self.section_mode.isChecked(), message_sections=clean_sections(self.message_sections),
            theme=self.theme_select.currentText(), check_updates=self.check_updates_checkbox.isChecked(),
            auto_download_updates=self.auto_download_checkbox.isChecked(), version=10,
        )

    def _save_settings(self):
        self._autosave_timer.stop()
        self.settings = self._collect_settings()
        try:
            self.settings.save()
            self._notice("Settings saved to ~/.config/linux-osc-chatbox/settings.json")
        except OSError as exc:
            self._notice(f"Failed to save settings: {exc}")
            QMessageBox.warning(self, "Save failed", str(exc))

    def _check_for_updates(self, silent=False):
        if self._update_future is not None or self._update_install_process is not None:
            return
        self._update_action = ('check', silent)
        self._available_release = None
        self._downloaded_update = None
        self.update_install_button.setText("Download and install update…")
        self.update_install_button.setEnabled(False)
        self.update_check_button.setEnabled(False)
        self.update_status.setText("Checking GitHub releases…")
        self._update_future = self._update_executor.submit(check_release)

    def _can_download_update(self, release):
        return bool(release and release.get('rpm_url') and release.get('checksum_url') and installed_via_rpm())

    def _download_update(self, *, automatic=False):
        if self._update_future is not None or not self._can_download_update(self._available_release):
            return
        self._update_action = ('download', automatic)
        self.update_install_button.setEnabled(False)
        self.update_status.setText("Downloading and verifying the Fedora RPM…")
        self._update_future = self._update_executor.submit(download_verified_rpm, dict(self._available_release))

    def _update_tick(self):
        future = self._update_future
        if future is not None and future.done():
            self._update_future = None
            action, automatic = self._update_action
            try:
                result = future.result()
            except Exception as exc:
                message = explain_update_error(exc)
                self.update_status.setText(f"Update {action} failed: {message}")
                if action == 'download':
                    self.update_install_button.setEnabled(self._can_download_update(self._available_release))
                if not automatic:
                    QMessageBox.warning(self, "Update error", message)
            else:
                if action == 'check':
                    self._available_release = result
                    if result is None:
                        self.update_status.setText(f"You're up to date (v{APP_VERSION}).")
                        self.update_details.setText("No newer public release found.")
                    else:
                        detail = (f"Available version: {result['version']}\n"
                                  f"Fedora RPM: {result.get('rpm_name') or 'Not available for this Fedora version'}\n"
                                  f"Download size: {human_size(result.get('rpm_size'))}\n\n"
                                  f"Release notes:\n{result.get('notes', 'No release notes provided.')}")
                        self.update_details.setText(detail)
                        compatible = self._can_download_update(result)
                        self.update_status.setText(
                            f"Update v{result['version']} available. " +
                            ("Verified RPM installation supported." if compatible else
                             "Automatic RPM installation unavailable here; use GitHub Releases.")
                        )
                        self.update_install_button.setEnabled(compatible)
                        if automatic and self.tray is not None:
                            self.tray.showMessage("Fly's OSC Chat Box update", f"Version {result['version']} is available. See Settings > Software updates.")
                        if not automatic:
                            QMessageBox.information(self, "Update available", f"Version {result['version']} is available. See Settings for release notes.")
                        if compatible and self.auto_download_checkbox.isChecked():
                            self._download_update(automatic=True)
                elif action == 'download':
                    self._downloaded_update = result
                    self.update_status.setText("Update downloaded and checksum verified. Ready to install with your approval.")
                    self.update_install_button.setText("Install verified update…")
                    self.update_install_button.setEnabled(True)
                    if automatic and self.tray is not None:
                        self.tray.showMessage("Fly's OSC Chat Box update", "A verified update is ready. Open Settings to approve installation.")
            self.update_check_button.setEnabled(self._update_future is None)
        proc = self._update_install_process
        if proc is not None and proc.poll() is not None:
            self._update_install_process = None
            if proc.returncode == 0:
                self.update_status.setText("Update installed. Quit and reopen the application to use the new version.")
                QMessageBox.information(self, "Update installed", "The RPM update was installed successfully. Quit and reopen Fly's OSC Chat Box to run the new version. Your settings are preserved.")
            else:
                self.update_status.setText("Update installation cancelled or failed. Check DNF/Polkit messages.")
                QMessageBox.warning(self, "Update not installed", "Fedora did not complete the RPM update. Your current version is unchanged.")
            self.update_install_button.setEnabled(self._can_download_update(self._available_release))

    def _start_update_install(self):
        release = self._available_release
        if not self._can_download_update(release) or self._update_future is not None:
            return
        if self._downloaded_update is None:
            if QMessageBox.question(self, "Download update", f"Download v{release['version']} from the official GitHub release?\n\nIts checksum will be verified before installation.") != QMessageBox.StandardButton.Yes:
                return
            self._download_update(automatic=False)
            return
        if QMessageBox.question(self, "Install verified update", f"Install verified v{release['version']} now?\n\nFedora will ask for administrator authorization. Your saved statuses and settings will be kept.") != QMessageBox.StandardButton.Yes:
            return
        self._begin_authorized_install(self._downloaded_update)

    def _begin_authorized_install(self, rpm_path):
        try:
            command = rpm_install_command(rpm_path)
            self._update_install_process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.update_status.setText("Waiting for Fedora administrator authorization and installation…")
            self.update_install_button.setEnabled(False)
        except Exception as exc:
            self.update_status.setText(f"Unable to start RPM installation: {exc}")
            QMessageBox.warning(self, "Update error", str(exc))
            self.update_install_button.setEnabled(True)

    def _show_window(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _quit(self):
        self._real_close = True
        self._save_settings()
        self._music_executor.shutdown(wait=False, cancel_futures=True)
        self._player_scan_executor.shutdown(wait=False, cancel_futures=True)
        self._gpu_executor.shutdown(wait=False, cancel_futures=True)
        self._update_executor.shutdown(wait=False, cancel_futures=True)
        if hasattr(self, "_control_executor"):
            self._control_executor.shutdown(wait=False, cancel_futures=True)
        self.app.quit()

    def closeEvent(self, event: QCloseEvent):
        if self.tray and self.minimize_to_tray.isChecked() and not self._real_close:
            self._save_settings()
            event.ignore()
            self.hide()
        else:
            if not getattr(self, "_restoring_settings", False):
                self._save_settings()
            event.accept()
            self._music_executor.shutdown(wait=False, cancel_futures=True)
            self._player_scan_executor.shutdown(wait=False, cancel_futures=True)
            self._gpu_executor.shutdown(wait=False, cancel_futures=True)
            self._update_executor.shutdown(wait=False, cancel_futures=True)
            if hasattr(self, "_control_executor"):
                self._control_executor.shutdown(wait=False, cancel_futures=True)
