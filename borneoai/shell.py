import os
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.completion import Completer, Completion
from borneoai.image_handler import find_images
from borneoai.ui import console, print_error, print_info

# Global state for selected images in the current prompt attempt
SELECTED_IMAGES = []

class ImageCompleter(Completer):
    def __init__(self, workspace_root):
        self.workspace_root = workspace_root

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if "/image" in text:
            # Find the last occurrence of /image to support multiple image additions
            last_image_index = text.rfind("/image")
            filter_text = text[last_image_index + 6:].strip()
            
            # Scan for images
            images = find_images(filter_text, self.workspace_root)
            
            for img in images:
                # We replace the /image and the filter text with the image path
                # The start_position is relative to the cursor
                # We want to replace from the start of "/image" to the cursor
                start_pos = -(len(text) - last_image_index)
                yield Completion(img, start_position=start_pos)
        
        # Handle /image-cancel completions
        if "/image-cancel" in text:
            last_cancel_index = text.rfind("/image-cancel")
            # Suggest currently selected images to remove
            for img in SELECTED_IMAGES:
                start_pos = -(len(text) - last_cancel_index)
                yield Completion(img, start_position=start_pos)

def get_bottom_toolbar():
    if not SELECTED_IMAGES:
        return ""
    # Show only filenames to save space
    files = [os.path.basename(p) for p in SELECTED_IMAGES]
    return f"Selected Images: {', '.join(files)}"

def process_input(user_input):
    """
    Processes the input to extract image paths and handle /image-cancel.
    Returns (cleaned_prompt, images_to_send).
    """
    global SELECTED_IMAGES
    
    # 1. Handle /image-cancel
    if "/image-cancel" in user_input:
        # This is a bit tricky. If it's just /image-cancel, we might want to enter a mode.
        # But for simplicity, if it's "/image-cancel /path/to/img", we remove it.
        # If it's just "/image-cancel", we can't do much here, so we'll handle it in the main loop.
        pass

    # 2. Extract image paths
    # We look for paths that look like absolute paths or start with /
    # A simple way: any word that starts with / and is a file that exists
    words = user_input.split()
    cleaned_words = []
    
    for word in words:
        if os.path.isabs(word) and os.path.exists(word) and any(word.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"]):
            if word not in SELECTED_IMAGES:
                SELECTED_IMAGES.append(word)
        elif word == "/image-cancel":
            # If we find /image-cancel without a path, we'll handle it as a command to clear or enter cancel mode
            # But let's assume it's used with a path or as a trigger.
            pass
        else:
            cleaned_words.append(word)
            
    return " ".join(cleaned_words), SELECTED_IMAGES

def start_interactive_shell(prompt_prefix, handle_turn_func, workspace_root):
    """
    Generic interactive shell with image support.
    """
    global SELECTED_IMAGES
    
    session = PromptSession(
        history=InMemoryHistory(),
        completer=ImageCompleter(workspace_root),
        bottom_toolbar=get_bottom_toolbar
    )
    
    while True:
        try:
            # We need to handle /image-cancel specifically
            user_input = session.prompt(f"{prompt_prefix} ❯ ").strip()
            
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit"]:
                print_info("Exiting...")
                break
                
            # Handle /image-cancel specifically if it's the only thing typed
            if user_input == "/image-cancel":
                if not SELECTED_IMAGES:
                    print_info("No images selected to cancel.")
                    continue
                
                print_info("Select an image to remove from the list:")
                # Simple selection loop for cancellation
                for i, img in enumerate(SELECTED_IMAGES):
                    print(f"[{i}] {img}")
                
                try:
                    choice = input("Choose index: ")
                    idx = int(choice)
                    if 0 <= idx < len(SELECTED_IMAGES):
                        removed = SELECTED_IMAGES.pop(idx)
                        print_info(f"Removed {os.path.basename(removed)}")
                    else:
                        print_error("Invalid index.")
                except ValueError:
                    print_error("Invalid input.")
                continue

            # Process input to extract images and clean prompt
            cleaned_prompt, images = process_input(user_input)
            
            # Run the turn with cleaned prompt and selected images
            # We pass images to the turn handler
            success = handle_turn_func(cleaned_prompt, images)
            
            if not success:
                print_error("An error occurred during the turn.")
                
            # Clear selected images after a successful turn
            SELECTED_IMAGES = []
            
        except KeyboardInterrupt:
            print_info("\nAction cancelled.")
        except EOFError:
            print_info("\nExiting...")
            break
        except Exception as e:
            print_error(f"Error in shell: {e}")
