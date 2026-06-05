import os
import sys
import argparse

# Verify dependencies before importing main modules to show helpful installation guides
missing_deps = []
try:
    import rich
except ImportError:
    missing_deps.append("rich")
try:
    import prompt_toolkit
except ImportError:
    missing_deps.append("prompt_toolkit")

if missing_deps:
    print(f"\n[BorneoAI Error] Missing required Python package(s): {', '.join(missing_deps)}", file=sys.stderr)
    print("Please run the following command to install them:", file=sys.stderr)
    print("  pip install -r requirements.txt", file=sys.stderr)
    print("Or if you are in the source directory:", file=sys.stderr)
    print("  pip install -e .", file=sys.stderr)
    sys.exit(1)

# Import our modules once dependencies are confirmed
from borneoai.ui import print_banner, print_help, print_error, print_info, console
from borneoai.config import get_api_key_or_prompt, configure_wizard
from borneoai.chat import start_chat_mode
from borneoai.agent import start_agent_mode

def main():
    # Show main banner
    print_banner()
    
    # Custom parser
    parser = argparse.ArgumentParser(description="BorneoAI CLI Coding Agent", add_help=False)
    parser.add_argument("command", nargs="?", choices=["chat", "agent", "config", "help"])
    parser.add_argument("prompt", nargs="*", help="Direct instruction prompt for chat or agent mode")
    parser.add_argument("-m", "--model", help="Override Gemini model name")
    parser.add_argument("-d", "--dir", default=".", help="Directory to run BorneoAI in")
    
    args = parser.parse_args()
    
    # Resolve workspace directory
    workspace_root = os.path.abspath(args.dir)
    if not os.path.exists(workspace_root):
        print_error(f"Workspace directory '{args.dir}' does not exist.")
        sys.exit(1)
        
    # Route to help menu
    if args.command == "help" or (len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]):
        print_help()
        sys.exit(0)
        
    # Route to configuration wizard
    if args.command == "config":
        configure_wizard()
        sys.exit(0)
        
    # Retrieve API key and default model name
    try:
        api_key, default_model = get_api_key_or_prompt()
    except SystemExit:
        sys.exit(1)
    except Exception as e:
        print_error(f"Failed to load configuration: {e}")
        sys.exit(1)
        
    # Determine model to use
    model_name = args.model if args.model else default_model
    
    # Parse direct CLI prompt string
    prompt_str = " ".join(args.prompt) if args.prompt else None
    
    # Route to Chat or Agent mode
    if args.command == "chat":
        start_chat_mode(api_key, model_name, workspace_root, prompt_str)
    elif args.command == "agent":
        start_agent_mode(api_key, model_name, workspace_root, prompt_str)
    elif args.command is None:
        # Interactive mode selection menu
        from rich.prompt import Prompt
        from rich.panel import Panel
        
        console.print(Panel(
            "[bold white]Welcome to BorneoAI! Choose a mode to proceed:[/bold white]\n\n"
            "  [bold cyan][1][/bold cyan] Chat Mode     [dim]-(Inspect, explain code, and discuss design pattern)[/dim]\n"
            "  [bold magenta][2][/bold magenta] Agent Mode    [dim]-(Create/edit code, manage files, run terminal commands)[/dim]\n"
            "  [bold yellow][3][/bold yellow] Configuration [dim]-(Wizard setup for API key and default models)[/dim]\n"
            "  [bold red][4][/bold red] Exit",
            title="BorneoAI Terminal UI",
            border_style="magenta",
            expand=False
        ))
        
        choice = Prompt.ask("\nChoose an option (1-4)", choices=["1", "2", "3", "4"], default="1")
        if choice == "1":
            start_chat_mode(api_key, model_name, workspace_root)
        elif choice == "2":
            start_agent_mode(api_key, model_name, workspace_root)
        elif choice == "3":
            configure_wizard()
        else:
            print_info("Goodbye!")
            sys.exit(0)

if __name__ == "__main__":
    main()
