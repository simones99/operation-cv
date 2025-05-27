def load_prompt(path):
    """Load a prompt from a text file."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
