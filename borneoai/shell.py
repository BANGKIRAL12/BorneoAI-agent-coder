import os
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.key_binding import KeyBindings
from borneoai.image_handler import find_images
from borneoai.video_handler import find_videos
from borneoai.ui import console, print_error, print_info

# Global state for selected media in the current prompt attempt
SELECTED_IMAGES = []
SELECTED_VIDEOS = []

class MediaCompleter(Completer):
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
        
        if "/video" in text:
            last_video_index = text.rfind("/video")
            filter_text = text[last_video_index + 6:].strip()
            videos = find_videos(filter_text, self.workspace_root)
            for vid in videos:
                start_pos = -(len(text) - last_video_index)
                yield Completion(vid, start_position=start_pos)
        
        if "/image-cancel" in text:
            last_cancel_index = text.rfind("/image-cancel")
            for img in SELECTED_IMAGES:
                start_pos = -(len(text) - last_cancel_index)
                yield Completion(img, start_position=start_pos)

        if "/video-cancel" in text:
            last_cancel_index = text.rfind("/video-cancel")
            for vid in SELECTED_VIDEOS:
                start_pos = -(len(text) - last_cancel_index)
                yield Completion(vid, start_position=start_pos)

def get_bottom_toolbar():
    parts = []
    if SELECTED_IMAGES:
        files = [os.path.basename(p) for p in SELECTED_IMAGES]
        parts.append(f"Images: {', '.join(files)}")
    if SELECTED_VIDEOS:
        files = [os.path.basename(p) for p in SELECTED_VIDEOS]
        parts.append(f"Videos: {', '.join(files)}")
    
    return " | ".join(parts) if parts else ""

def process_input(user_input):
    """
    Processes the input to extract media paths.
    Returns (cleaned_prompt, images_to_send, videos_to_send).
    """
    global SELECTED_IMAGES, SELECTED_VIDEOS
    
    words = user_input.split()
    cleaned_words = []
    
    # Media extensions
    IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
    VID_EXT = {".mp4", ".mkv", ".mov", ".avi", ".wmv", ".flv", ".webm"}
    
    for word in words:
        if os.path.isabs(word) and os.path.exists(word):
            ext = os.path.splitext(word)[1].lower()
            if ext in IMG_EXT:
                if word not in SELECTED_IMAGES:
                    SELECTED_IMAGES.append(word)
            elif ext in VID_EXT:
                if word not in SELECTED_VIDEOS:
                    SELECTED_VIDEOS.append(word)
            else:
                cleaned_words.append(word)
        elif word in ["/image-cancel", "/video-cancel"]:
            pass
        else:
            cleaned_words.append(word)
            
    return " ".join(cleaned_words), SELECTED_IMAGES, SELECTED_VIDEOS

def start_interactive_shell(prompt_prefix, handle_turn_func, workspace_root):
    """
    Generic interactive shell with image and video support.
    """
    global SELECTED_IMAGES, SELECTED_VIDEOS
    
    kb = KeyBindings()

    @kb.add('tab')
    def _(event):
        global SELECTED_IMAGES, SELECTED_VIDEOS
        document = event.current_buffer.document
        text = document.text_before_cursor
        
        # Handle /image
        if text.strip().endswith("/image"):
            images = find_images("", workspace_root)
            if not images:
                print_info("\nNo images found in the system.")
                return

            console.print("\n[bold cyan]Available Images:[/bold cyan]")
            for i, img in enumerate(images[:50]):
                console.print(f"[{i}] {os.path.basename(img)} [dim]({img})[/dim]")
            if len(images) > 50:
                console.print(f"... and {len(images)-50} more.")

            inner_kb = KeyBindings()
            @inner_kb.add('tab')
            def _inner_tab(inner_event):
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
                        last_image_pos = text.rfind("/image")
                        dist_from_end = len(text) - last_image_pos
                        event.current_buffer.delete_before_cursor(dist_from_end)
                    else:
                        print_error("Invalid index.")
                else:
                    print_error("Please enter a valid number.")
            except Exception as e:
                print_error(f"Error during image selection: {e}")
            return

        # Handle /video
        if text.strip().endswith("/video"):
            videos = find_videos("", workspace_root)
            if not videos:
                print_info("\nNo videos found in the system.")
                return

            console.print("\n[bold cyan]Available Videos:[/bold cyan]")
            for i, vid in enumerate(videos[:50]):
                console.print(f"[{i}] {os.path.basename(vid)} [dim]({vid})[/dim]")
            if len(videos) > 50:
                console.print(f"... and {len(videos)-50} more.")

            inner_kb = KeyBindings()
            @inner_kb.add('tab')
            def _inner_tab(inner_event):
                inner_event.current_buffer.validate_and_handle()

            try:
                inner_session = PromptSession(key_bindings=inner_kb)
                choice = inner_session.prompt("Select video index (Press Tab to confirm) ❯ ").strip()
                if choice.isdigit():
                    idx = int(choice)
                    if 0 <= idx < len(videos):
                        selected_vid = videos[idx]
                        SELECTED_VIDEOS.append(selected_vid)
                        print_info(f"Selected: {os.path.basename(selected_vid)}")
                        last_video_pos = text.rfind("/video")
                        dist_from_end = len(text) - last_video_pos
                        event.current_buffer.delete_before_cursor(dist_from_end)
                    else:
                        print_error("Invalid index.")
                else:
                    print_error("Please enter a valid number.")
            except Exception as e:
                print_error(f"Error during video selection: {e}")
            return

    session = PromptSession(
        history=InMemoryHistory(),
        completer=MediaCompleter(workspace_root),
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
                    console.print(f"[{i}] {img}")
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

            if user_input == "/video-cancel":
                if not SELECTED_VIDEOS:
                    print_info("No videos selected to cancel.")
                    continue
                print_info("Select a video to remove from the list:")
                for i, vid in enumerate(SELECTED_VIDEOS):
                    console.print(f"[{i}] {vid}")
                try:
                    choice = input("Choose index: ")
                    idx = int(choice)
                    if 0 <= idx < len(SELECTED_VIDEOS):
                        removed = SELECTED_VIDEOS.pop(idx)
                        print_info(f"Removed {os.path.basename(removed)}")
                    else:
                        print_error("Invalid index.")
                except ValueError:
                    print_error("Invalid input.")
                continue

            cleaned_prompt, images, videos = process_input(user_input)
            
            success = handle_turn_func(cleaned_prompt, images, videos)
            
            if not success:
                print_error("An error occurred during the turn.")
                
            SELECTED_IMAGES = []
            SELECTED_VIDEOS = []
            
        except KeyboardInterrupt:
            print_info("\nAction cancelled.")
        except EOFError:
            print_info("\nExiting...")
            break
        except Exception as e:
            print_error(f"Error in shell: {e}")
