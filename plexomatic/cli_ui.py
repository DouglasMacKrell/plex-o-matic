"""UI enhancements for the command line interface using Rich."""

try:
    # Python 3.9+ has native support for these types
    from typing import Dict, Any, Optional, Union, Tuple, Generator
except ImportError:
    # For Python 3.8 support
    from typing_extensions import Dict, Any, Optional, Union, Tuple, Generator
from pathlib import Path
import logging
from contextlib import contextmanager
import os

from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TaskID
from rich.style import Style
from rich.text import Text
from rich.panel import Panel
from rich.table import Table

# Initialize console
console = Console()

# Setup logger
logger = logging.getLogger("plexomatic.cli_ui")

# Styles
STYLES = {
    "success": Style(color="green", bold=True),
    "error": Style(color="red", bold=True),
    "warning": Style(color="yellow", bold=True),
    "info": Style(color="blue", bold=True),
    "highlight": Style(color="cyan", bold=True),
    "filename": Style(color="cyan"),
    "command": Style(color="green", bold=True),
    "option": Style(color="yellow"),
    "heading": Style(color="magenta", bold=True),
    "subheading": Style(color="magenta"),
}

# Status indicators
INDICATORS = {
    "success": "✓ ",
    "error": "✗ ",
    "warning": "! ",
    "info": "ℹ ",
}


def print_status(message: str, status: str = "info") -> None:
    """Print a status message with appropriate styling and icon.

    Args:
        message: The message to print
        status: The status type ('success', 'error', 'warning', 'info')
    """
    indicator = INDICATORS.get(status, "")
    style = STYLES.get(status, STYLES["info"])
    console.print(f"{indicator}{message}", style=style)


def print_heading(heading: str, subheading: Optional[str] = None) -> None:
    """Print a styled heading.

    Args:
        heading: The main heading text
        subheading: Optional subheading text
    """
    console.print(heading, style=STYLES["heading"])
    if subheading:
        console.print(subheading, style=STYLES["subheading"])


def print_file_change(original: Union[str, Path], new: Union[str, Path]) -> None:
    """Print a styled file rename operation.

    Args:
        original: Original filename or path
        new: New filename or path
    """
    # Get just the filename if Path objects are provided
    if isinstance(original, Path):
        original = original.name
    else:
        # If it's a string that might be a path, extract just the filename
        original = os.path.basename(str(original))

    if isinstance(new, Path):
        new = new.name
    else:
        # If it's a string that might be a path, extract just the filename
        new = os.path.basename(str(new))

    text = Text()
    text.append(str(original), style=STYLES["filename"])
    text.append(" → ", style=STYLES["info"])
    text.append(str(new), style=STYLES["highlight"])
    console.print(text)


def print_summary(title: str, items: Dict[str, Any]) -> None:
    """Print a summary of operations.

    Args:
        title: Summary title
        items: Dictionary of items to display
    """
    table = Table(title=title)
    table.add_column("Item", style="cyan")
    table.add_column("Value", style="green")

    for key, value in items.items():
        table.add_row(key, str(value))

    console.print(table)


@contextmanager
def progress_bar(
    description: str, total: Optional[int] = None
) -> Generator[Tuple[Progress, TaskID], None, None]:
    """Create a progress bar context manager.

    Args:
        description: Description of the task
        total: Total number of steps (optional)

    Yields:
        Tuple of (Progress object, task_id)
    """
    progress = Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=40),
        TaskProgressColumn(),
        TextColumn(
            "[bold green]{task.completed}/{task.total}" if total else "[bold green]{task.completed}"
        ),
    )

    with progress:
        task_id = progress.add_task(description, total=total)
        yield progress, task_id


def setup_help_formatter(help_text: str) -> str:
    """Format help text with colors and styling.

    Args:
        help_text: Original help text

    Returns:
        Formatted help text
    """
    # This could be used to enhance Click's help text, but we'll just pass through for now
    # since we'd need to monkey-patch Click's help formatter for full control
    return help_text


def color_help_sections(text: str) -> str:
    """Add color to help text sections.

    Args:
        text: Original help text

    Returns:
        Colored help text
    """
    # Replace headers with colored versions
    # This would need integration with Click's formatter
    return text


def format_error(message: str) -> None:
    """Format and print an error message.

    Args:
        message: Error message to display
    """
    panel = Panel(message, style="red", title="Error")
    console.print(panel)


def format_warning(message: str) -> None:
    """Format and print a warning message.

    Args:
        message: Warning message to display
    """
    panel = Panel(message, style="yellow", title="Warning")
    console.print(panel)


def print_info(message: str) -> None:
    """Print an info message with blue color.

    Args:
        message: The message to print
    """
    console.print(message, style=STYLES["info"])


def print_result(message: str) -> None:
    """Print a result with cyan color.

    Args:
        message: The result to print
    """
    console.print(message, style=STYLES["highlight"])


def print_newline() -> None:
    """Print a newline for better spacing."""
    console.print("")
