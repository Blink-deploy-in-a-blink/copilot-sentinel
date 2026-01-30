"""
Interactive CLI helper functions for user input.
"""

from typing import List, Optional


def ask_choice(question: str, options: List[str], allow_back: bool = False) -> int:
    """
    Present multiple choice question.
    
    Args:
        question: The question to ask
        options: List of option strings
        allow_back: If True, adds a "Go back" option
    
    Returns:
        Index of selected option (0-based)
    """
    print(f"\n{question}")
    
    for i, opt in enumerate(options, 1):
        print(f"  [{i}] {opt}")
    
    if allow_back:
        print(f"  [{len(options) + 1}] ← Go back")
    
    while True:
        try:
            choice = input("\nYour choice: ").strip()
            idx = int(choice) - 1
            
            if allow_back and idx == len(options):
                return -1  # Signal to go back
            
            if 0 <= idx < len(options):
                return idx
            
            print(f"Invalid choice. Please enter 1-{len(options)}")
        except (ValueError, KeyboardInterrupt):
            print("Please enter a number.")


def ask_yes_no(question: str, default: Optional[bool] = None) -> bool:
    """
    Ask a yes/no question.
    
    Args:
        question: The question to ask
        default: Default answer if user presses Enter (None = no default)
    
    Returns:
        True for yes, False for no
    """
    if default is True:
        suffix = " [Y/n]: "
    elif default is False:
        suffix = " [y/N]: "
    else:
        suffix = " [y/n]: "
    
    while True:
        answer = input(question + suffix).strip().lower()
        
        if answer in ['y', 'yes']:
            return True
        if answer in ['n', 'no']:
            return False
        if answer == '' and default is not None:
            return default
        
        print("Please answer 'y' or 'n'.")


def ask_text(question: str, optional: bool = False, multiline: bool = False) -> Optional[str]:
    """
    Ask for free-text input.
    
    Args:
        question: The question to ask
        optional: If True, user can press Enter to skip
        multiline: If True, allows multiple lines (Ctrl+D to finish)
    
    Returns:
        User's text input, or None if skipped
    """
    if multiline:
        print(f"\n{question}")
        print("(Type your answer, press Ctrl+Z then Enter on Windows, or Ctrl+D on Mac/Linux when done)")
        print()
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        
        text = "\n".join(lines).strip()
        return text if text else None
    
    else:
        if optional:
            print(f"\n{question}")
            print("(Press Enter to skip)")
        else:
            print(f"\n{question}")
        
        answer = input("> ").strip()
        
        if optional and not answer:
            return None
        
        return answer if answer else None


def ask_number(question: str, default: Optional[int] = None, min_val: Optional[int] = None, max_val: Optional[int] = None) -> int:
    """
    Ask for a number.
    
    Args:
        question: The question to ask
        default: Default value if user presses Enter
        min_val: Minimum allowed value
        max_val: Maximum allowed value
    
    Returns:
        The number entered
    """
    suffix = f" [default: {default}]: " if default is not None else ": "
    
    while True:
        try:
            answer = input(question + suffix).strip()
            
            if answer == '' and default is not None:
                return default
            
            num = int(answer)
            
            if min_val is not None and num < min_val:
                print(f"Please enter a number >= {min_val}")
                continue
            
            if max_val is not None and num > max_val:
                print(f"Please enter a number <= {max_val}")
                continue
            
            return num
        
        except ValueError:
            print("Please enter a valid number.")


def display_box(title: str, content: str, width: int = 60, char: str = "━") -> None:
    """
    Display content in a pretty box.
    
    Args:
        title: Box title
        content: Content to display
        width: Box width
        char: Character to use for borders
    """
    print()
    print(char * width)
    print(title.center(width))
    print(char * width)
    print(content)
    print(char * width)
    print()


def display_header(text: str, width: int = 60) -> None:
    """Display a section header."""
    print()
    print("━" * width)
    print(text)
    print("━" * width)


def display_success(message: str) -> None:
    """Display a success message."""
    print(f"\n✓ {message}")


def display_error(message: str) -> None:
    """Display an error message."""
    print(f"\n✗ {message}")


def display_warning(message: str) -> None:
    """Display a warning message."""
    print(f"\n⚠  {message}")


def display_info(message: str) -> None:
    """Display an info message."""
    print(f"\n🤖 {message}")


def confirm_action(action: str) -> bool:
    """
    Ask user to confirm an action.
    
    Args:
        action: Description of the action
    
    Returns:
        True if confirmed, False otherwise
    """
    print(f"\n⚠  About to: {action}")
    return ask_yes_no("Continue?", default=False)
