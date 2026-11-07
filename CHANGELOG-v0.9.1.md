# Fly's OSC Chat Box v0.9.1

## Window size and readability fixes

- Added page-wide scroll areas and minimum layout constraints across Chatbox, Statuses, Music, System, Integrations, Settings and Composer.
- Replaced crowded Chatbox toolbars with readable vertically stacked controls.
- Increased minimum editor and preview heights; the content no longer needs to collapse into thin horizontal strips when the window is short.
- Reflowed status and composer action buttons into two columns.
- Reduced minimum window size and allowed the sidebar to shrink modestly.
- Corrected the KDE desktop launcher generator to run the virtual-environment Python interpreter directly.
- Existing status, theme, music and composer settings stay in their original config directory.

## Install

Close Fly's OSC Chat Box completely, including its tray icon, and extract this archive over the existing `~/Documents/Projects/linux-osc-chatbox` source folder. Then run `python3 install-launcher.py --desktop` once to update the KDE shortcut. The archive does not include `.venv` or personal settings.
