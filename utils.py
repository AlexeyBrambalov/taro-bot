import re

def sanitize_markdown(text: str) -> str:
    """
    Strips out unsupported or problematic characters for Markdown parsing in Telegram.
    """
    text = re.sub(r'[`*_{}\[\]()#+\-\.!]', '', text)
    return text