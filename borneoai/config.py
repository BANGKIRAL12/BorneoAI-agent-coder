import os
import json
from borneoai.ui import console, print_success, print_error, print_info, print_warning

CONFIG_DIR = os.path.expanduser("~/.config/borneoai")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_MODELS = [
    {"name": "gemini-2.5-flash", "desc": "Default: Fast, smart, and efficient (recommended for most tasks)"},
    {"name": "gemini-2.5-pro", "desc": "Smartest model: Best for complex coding and deep debugging"},
    {"name": "gemini-1.5-flash", "desc": "Legacy Flash: High speed and 1M context"},
    {"name": "gemini-1.5-pro", "desc": "Legacy Pro: High performance and 2M context"},
    {"name": "gemma-2-27b-it", "desc": "Gemma 2: State-of-the-art open weights chat model"}
]

def load_config():
    """Loads configuration. Returns a dict, or empty dict if not found."""
    # Priority 1: Environment variable
    env_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    
    config = {
        "api_key": env_key,
        "default_model": "gemini-2.5-flash"
    }

    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                saved = json.load(f)
                if saved.get("api_key") and not config["api_key"]:
                    config["api_key"] = saved["api_key"]
                if saved.get("default_model"):
                    config["default_model"] = saved["default_model"]
        except Exception as e:
            print_error(f"Failed to read config file: {e}")
            
    return config

def save_config(api_key, default_model):
    """Saves config to ~/.config/borneoai/config.json"""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        config_data = {
            "api_key": api_key,
            "default_model": default_model
        }
        with open(CONFIG_PATH, "w") as f:
            json.dump(config_data, f, indent=4)
        return True
    except Exception as e:
        print_error(f"Failed to save configuration: {e}")
        return False

def configure_wizard():
    """Runs interactive setup wizard."""
    console.print("\n[bold cyan]🛠 BorneoAI Configuration Wizard[/bold cyan]")
    console.print("Set up your Google AI Studio configuration.\n")
    
    current = load_config()
    current_key = current.get("api_key") or ""
    current_model = current.get("default_model") or "gemini-2.5-flash"
    
    # 1. API Key Input
    masked_key = f"{current_key[:6]}...{current_key[-6:]}" if len(current_key) > 12 else "Not set"
    console.print(f"Current API Key: [yellow]{masked_key}[/yellow]")
    console.print("Get an API Key from: [link=https://aistudio.google.com/]https://aistudio.google.com/[/link]")
    
    new_key = input("Enter Gemini API Key (press Enter to keep current): ").strip()
    if not new_key:
        new_key = current_key
        
    if not new_key:
        print_error("Error: API Key is required to run BorneoAI!")
        return False
        
    # 2. Model Selection
    console.print("\nSelect default AI Model:")
    for idx, m in enumerate(DEFAULT_MODELS, 1):
        active_str = " *CURRENT*" if m["name"] == current_model else ""
        console.print(f"  [{idx}] [bold green]{m['name']}[/bold green]{active_str}")
        console.print(f"      {m['desc']}")
    
    console.print(f"  [{len(DEFAULT_MODELS)+1}] Custom Model")
    
    choice = input("\nSelect choice (1-6): ").strip()
    selected_model = current_model
    
    if choice.isdigit():
        c_idx = int(choice) - 1
        if 0 <= c_idx < len(DEFAULT_MODELS):
            selected_model = DEFAULT_MODELS[c_idx]["name"]
        elif c_idx == len(DEFAULT_MODELS):
            selected_model = input("Enter custom model name (e.g. gemma-2-9b-it): ").strip()
            if not selected_model:
                selected_model = current_model
                
    if save_config(new_key, selected_model):
        print_success(f"Configuration saved successfully to {CONFIG_PATH}!")
        print_info(f"Using default model: [bold green]{selected_model}[/bold green]")
        return True
    return False

def get_api_key_or_prompt():
    """Gets the API key or runs wizard if not found."""
    config = load_config()
    if not config.get("api_key"):
        print_warning("No API Key detected. Starting configuration wizard...")
        if configure_wizard():
            config = load_config()
        else:
            sys.exit(1)
    return config["api_key"], config["default_model"]
