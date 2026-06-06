import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.theme import Theme
from rich.status import Status

# Define a cool, premium theme
BORNEO_THEME = Theme({
    "info": "cyan bold",
    "warning": "yellow bold",
    "error": "red bold",
    "success": "green bold",
    "action": "magenta bold",
    "system": "blue bold",
    "title": "bold white on dark_blue",
    "agent_title": "bold black on bright_magenta",
    "chat_title": "bold black on bright_cyan"
})

console = Console(theme=BORNEO_THEME)
output_callback = None # Global callback for GUI streaming

def _stream_output(text, type="text"):
    """Internal helper to send output to GUI callback if configured."""
    if output_callback:
        output_callback(text, type)

def print_banner():
    banner = """
[bold magenta]========================================================================[/bold magenta]
[bold cyan]  🇧 🇴 🇷 🇳 🇪 🇴 🇦 🇮  -  Your Premium AI Coding Agent & Chat Companion[/bold cyan]
[bold magenta]========================================================================[/bold magenta]
    """
    console.print(banner)
    _stream_output(banner, "banner")

def print_help():
    help_text = """
[bold cyan]Commands:[/bold cyan]
  [bold yellow]borneoai chat[/bold yellow]          Start in Chat Mode (interactive discussion, explanation)
  [bold yellow]borneoai agent[/bold yellow]         Start in Agent Mode (reads/writes files, runs commands)
  [bold yellow]borneoai config[/bold yellow]        Configure BorneoAI (API key, default model selection)
  [bold yellow]borneoai help[/bold yellow]          Show this help message

[bold cyan]Options (Chat & Agent modes):[/bold cyan]
  [bold yellow]-m, --model <name>[/bold yellow]    Override default model for this session
  [bold yellow]-d, --dir <path>[/bold yellow]      Set custom workspace directory (defaults to current dir)

[bold info]Tip: Agent mode is sandboxed to the project directory. It cannot escape it for file edits![/bold info]
"""
    console.print(Panel(help_text, title="BorneoAI CLI Usage", border_style="cyan"))
    _stream_output(help_text, "help")

def show_spinner(text="Thinking..."):
    _stream_output(text, "status")
    return console.status(text, spinner="dots")

def print_info(msg):
    text = f"ℹ {msg}"
    console.print(f"[info]ℹ[/info] {msg}")
    _stream_output(text, "info")

def print_success(msg):
    text = f"✔ {msg}"
    console.print(f"[success]✔[/success] {msg}")
    _stream_output(text, "success")

def print_warning(msg):
    text = f"⚠ {msg}"
    console.print(f"[warning]⚠[/warning] {msg}")
    _stream_output(text, "warning")

def print_error(msg):
    text = f"✘ {msg}"
    console.print(f"[error]✘[/error] {msg}", file=sys.stderr)
    _stream_output(text, "error")

def print_action(action_type, details):
    """
    Prints a standard trace of what the agent is doing in a premium styling.
    Action types: CREATE, MODIFY, READ, DELETE, RUN, THINK
    """
    symbol = "🛠"
    color = "white"
    if action_type == "CREATE":
        symbol = "📝 [bold green][CREATE][/bold green]"
        color = "green"
    elif action_type == "MODIFY":
        symbol = "✏️ [bold yellow][MODIFY][/bold yellow]"
        color = "yellow"
    elif action_type == "READ":
        symbol = "📖 [bold cyan][READ][/bold cyan]"
        color = "cyan"
    elif action_type == "DELETE":
        symbol = "🗑️ [bold red][DELETE][/bold red]"
        color = "red"
    elif action_type == "RUN":
        symbol = "🐚 [bold magenta][RUN][/bold magenta]"
        color = "magenta"
    elif action_type == "THINK":
        symbol = "🧠 [bold blue][THINK][/bold blue]"
        color = "blue"

    # Format for GUI: removing rich tags for the callback
    gui_symbol = symbol.replace("[bold green][CREATE][/bold green]", "[CREATE]") \
                      .replace("[bold yellow][MODIFY][/bold yellow]", "[MODIFY]") \
                      .replace("[bold cyan][READ][/bold cyan]", "[READ]") \
                      .replace("[bold red][DELETE][/bold red]", "[DELETE]") \
                      .replace("[bold magenta][RUN][/bold magenta]", "[RUN]") \
                      .replace("[bold blue][THINK][/bold blue]", "[THINK]")
    
    console.print(f"{symbol} [bold {color}]{details}[/bold {color}]")
    _stream_output(f"{gui_symbol} {details}", "action")

def print_code_preview(filepath, content, language=None):
    """Prints a neat syntax-highlighted block of code."""
    if not language:
        # Infer language from extension
        ext = os.path.splitext(filepath)[1].lower()
        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".html": "html",
            ".css": "css",
            ".json": "json",
            ".sh": "bash",
            ".md": "markdown",
            ".yml": "yaml",
            ".yaml": "yaml"
        }
        language = lang_map.get(ext, "text")

    # Limit display size to avoid cluttering terminal
    lines = content.splitlines()
    if len(lines) > 20:
        preview_content = "\n".join(lines[:18]) + f"\n\n... and {len(lines)-18} more lines ..."
    else:
        preview_content = content

    syntax = Syntax(preview_content, language, theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title=f"File content: {filepath}", border_style="dim white"))
    _stream_output(f"File content: {filepath}\n\n{preview_content}", "code")

def print_ai_markdown(text, role_title="BorneoAI"):
    """Render and print AI response in beautifully formatted markdown."""
    md = Markdown(text)
    # Ensure there's a margin and clean outline
    console.print()
    console.print(Panel(md, title=f" {role_title} ", border_style="magenta", expand=True))
    console.print()
    _stream_output(text, "ai")
