"""Text processing utilities."""


def truncate_text(text: str, max_length: int) -> str:
    """Truncate text to max_length and add ellipsis if needed.

    Args:
        text: The text to truncate
        max_length: Maximum allowed length

    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."
