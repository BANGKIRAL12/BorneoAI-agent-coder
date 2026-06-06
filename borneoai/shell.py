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

import os
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.key_binding import KeyBindings
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
            last_image_index = text.rfind("/image")
            filter_text = text[last_image_index + 6:].strip()
            images = find_images(filter_text, self.workspace_root)
            for img in images:
                start_pos = -(len(text) - last_image_index)
                yield Completion(img, start_position=start_pos)
        
        if "/image-cancel" in text:
            last_cancel_index = text.rfind("/image-cancel")
            for img in SELECTED_IMAGES:
                start_pos = -(len(text) - last_cancel_index)
                yield Completion(img, start_position=start_pos)

def get_bottom_toolbar():
    if not SELECTED_IMAGES:
        return ""
    files = [os.path.basename(p) for p in SELECTED_IMAGES]
    return f"Selected Images: {', '.join(files)}"

def process_input(user_input):
    """
    Processes the input to extract image paths and handle /image-cancel.
    Returns (cleaned_prompt, images_to_send).
    """
    global SELECTED_IMAGES
    
    words = user_input.split()
    cleaned_words = []
    
    for word in words:
        if os.path.isabs(word) and os.path.exists(word) and any(word.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"]):
            if word not in SELECTED_IMAGES:
                SELECTED_IMAGES.append(word)
        elif word == "/image-cancel":
            pass
        else:
            cleaned_words.append(word)
            
    return " ".join(cleaned_words), SELECTED_IMAGES

def start_interactive_shell(prompt_prefix, handle_turn_func, workspace_root):
    """
    Generic interactive shell with image support.
    """
    global SELECTED_IMAGES
    
    # Key bindings for the main shell
    kb = KeyBindings()

    @kb.add('tab')
    def _(event):
        global SELECTED_IMAGES
        document = event.current_buffer.document
        text = document.text_before_cursor
        
        # Check if /image is at the end of the text before cursor
        if text.strip().endswith("/image"):
            # 1. Find images
            images = find_images("", workspace_root)
            if not images:
                print_info("\nNo images found in the system.")
                return

            # 2. Display images list
            print("\n[bold cyan]Available Images:[/bold cyan]")
            for i, img in enumerate(images[:50]): # Limit to 50 for display
                print(f"[{i}] {os.path.basename(img)} [dim]({img})[/dim]")
            if len(images) > 50:
                print(f"... and {len(images)-50} more.")

            # 3. Inner prompt to select image using Tab to confirm
            inner_kb = KeyBindings()
            @inner_kb.add('tab')
            def _inner_tab(inner_event):
                # Submit the prompt when Tab is pressed
                inner_event.current_buffer.validate_and_handle()

            try:
                inner_session = PromptSession(key_bindings=inner_kb)
                choice = inner_session.prompt("Select image index (Press Tab to confirm) ❯ ").strip()
                
                if choice.isdigit():
                    idx = int(choice)
                    if 0 <= idx < len(images):
                        selected_img = images[idx]
                        SELECTED_IMAGES.append(selected_img)
                        print_info(f"Selected: {os.path.basename(selected_img)}")
                        
                        # 4. Remove /image from the main buffer
                        # Calculate length of "/image" and any trailing whitespace
                        # We search for the last occurrence of /image
                        last_image_pos = text.rfind("/image")
                        # We remove from the start of /image to the cursor
                        # Use delete_before_cursor
                        # Note: text is text_before_cursor.
                        # We need to delete from last_image_pos to the end.
                        # The buffer's current position is at the end of text.
                        # So we delete from (len(text) - last_image_pos) back.
                        # But if there was trailing whitespace, it's included.
                        
                        # a more precise way:
                        # find how many characters from the end the /image started
                        dist_from_end = len(text) - last_image_pos
                        event.current_buffer.delete_before_cursor(dist_from_end)
                    else:
                        print_error("Invalid index.")
                else:
                    print_error("Please enter a valid number.")
            except Exception as e:
                print_error(f"Error during image selection: {e}")
            
            return # Prevent default Tab behavior

    session = PromptSession(
        history=InMemoryHistory(),
        completer=ImageCompleter(workspace_root),
        bottom_toolbar=get_bottom_toolbar,
        key_bindings=kb
    )
    
    while True:
        try:
            user_input = session.prompt(f"{prompt_prefix} ❯ ").strip()
            
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit"]:
                print_info("Exiting...")
                break
                
            if user_input == "/image-cancel":
                if not SELECTED_IMAGES:
                    print_info("No images selected to cancel.")
                    continue
                
                print_info("Select an image to remove from the list:")
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

            cleaned_prompt, images = process_input(user_input)
            
            success = handle_turn_func(cleaned_prompt, images)
            
            if not success:
                print_error("An error occurred during the turn.")
                
            SELECTED_IMAGES = []
            
        except KeyboardInterrupt:
            print_info("\nAction cancelled.")
        except EOFError:
            print_info("\nExiting...")
            break
        except Exception as e:
            print_error(f"Error in shell: {e}")
