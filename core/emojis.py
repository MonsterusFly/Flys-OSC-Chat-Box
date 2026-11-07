"""Emoji picker data, separate from Qt so labels and insertion can be tested."""

EMOJIS = [
    ("😀", "Grinning"), ("😊", "Smiling"), ("🥰", "Love"), ("😍", "Heart eyes"),
    ("😂", "Laughing"), ("😭", "Crying"), ("🥺", "Pleading"), ("😎", "Cool"),
    ("😴", "Sleepy"), ("😈", "Mischief"), ("👀", "Eyes"), ("💀", "Skull"),
    ("❤️", "Red heart"), ("💜", "Purple heart"), ("💙", "Blue heart"),
    ("✨", "Sparkles"), ("⭐", "Star"), ("🔥", "Fire"), ("🎮", "Game"),
    ("🎵", "Music"), ("🎶", "Notes"), ("🎧", "Headphones"), ("🎤", "Mic"),
    ("💤", "Zzz"), ("✅", "Check"), ("❌", "Cross"), ("⚡", "Lightning"),
    ("🌙", "Moon"), ("☀️", "Sun"), ("🌈", "Rainbow"), ("🍀", "Clover"),
    ("🌸", "Flower"), ("🐱", "Cat"), ("🐺", "Wolf"), ("🦊", "Fox"),
    ("🐸", "Frog"), ("🤍", "White heart"), ("🖤", "Black heart"),
    ("💕", "Hearts"), ("💖", "Glitter heart"), ("🎉", "Party"),
    ("👋", "Wave"), ("👍", "Thumbs up"), ("💻", "Computer"),
    ("🕹️", "Joystick"), ("🔴", "Red dot"), ("🟢", "Green dot"),
    ("⏳", "Hourglass"),
]


def matching_emojis(query: str):
    """Return matching (character, readable label) pairs."""
    search = query.casefold().strip()
    return [(emoji, label) for emoji, label in EMOJIS if search in label.casefold()]
