import os
import subprocess
import shutil
from borneoai.ui import print_action, print_code_preview

class FileSandbox:
    def __init__(self, workspace_root):
        self.workspace_root = os.path.abspath(workspace_root)

    def _resolve(self, path):
        """Resolves the path relative to workspace root and verifies it's within root."""
        # If path is absolute, check if it's within workspace root
        if os.path.isabs(path):
            abs_path = os.path.abspath(path)
        else:
            abs_path = os.path.abspath(os.path.join(self.workspace_root, path))
            
        # Verify it starts with workspace_root
        common = os.path.commonpath([self.workspace_root, abs_path])
        if common != self.workspace_root:
            raise PermissionError(
                f"Security Violation: Access denied. Path '{path}' resolves to '{abs_path}', "
                f"which is outside the workspace root '{self.workspace_root}'."
            )
        return abs_path

    def list_directory(self, relative_path: str = ".") -> str:
        """
        List all files and folders in a directory, relative to the workspace root.
        
        Args:
            relative_path: The directory path to list, relative to the workspace root. Default is '.'.
        """
        try:
            target_dir = self._resolve(relative_path)
            if not os.path.exists(target_dir):
                return f"Error: Directory '{relative_path}' does not exist."
            if not os.path.isdir(target_dir):
                return f"Error: '{relative_path}' is a file, not a directory."
            
            print_action("READ", f"Listing contents of directory: {relative_path}")
            
            items = os.listdir(target_dir)
            if not items:
                return "Directory is empty."
                
            out = []
            for item in sorted(items):
                item_path = os.path.join(target_dir, item)
                is_dir = os.path.isdir(item_path)
                marker = "[DIR] " if is_dir else "      "
                size = f" ({os.path.getsize(item_path)} bytes)" if not is_dir else ""
                out.append(f"{marker}{item}{size}")
            return "\n".join(out)
        except Exception as e:
            return f"Error listing directory: {str(e)}"

    def read_file(self, relative_path: str) -> str:
        """
        Read the entire content of a file in the workspace.
        
        Args:
            relative_path: Path of the file to read, relative to workspace root.
        """
        try:
            target_file = self._resolve(relative_path)
            if not os.path.exists(target_file):
                return f"Error: File '{relative_path}' does not exist."
            if os.path.isdir(target_file):
                return f"Error: '{relative_path}' is a directory, not a file."
                
            print_action("READ", f"Reading file: {relative_path}")
            
            with open(target_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Show a nice code preview in console
            print_code_preview(relative_path, content)
            return content
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def write_file(self, relative_path: str, content: str) -> str:
        """
        Create a new file or completely overwrite an existing file with the given content.
        
        Args:
            relative_path: Path of the file to create or overwrite, relative to workspace root.
            content: The text content to write into the file.
        """
        try:
            target_file = self._resolve(relative_path)
            
            # Create directories if they don't exist
            os.makedirs(os.path.dirname(target_file), exist_ok=True)
            
            is_overwrite = os.path.exists(target_file)
            action_str = "Overwriting file" if is_overwrite else "Creating new file"
            
            print_action("CREATE" if not is_overwrite else "MODIFY", f"{action_str}: {relative_path}")
            
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(content)
                
            # Show preview
            print_code_preview(relative_path, content)
            return f"Successfully wrote {len(content)} characters to '{relative_path}'."
        except Exception as e:
            return f"Error writing file: {str(e)}"

    def patch_file(self, relative_path: str, search_content: str, replace_content: str) -> str:
        """
        Edit a file by replacing a specific block of text with new content.
        Use this tool when you want to modify a section of a file without rewriting it entirely.
        The search_content must match EXACTLY a block of text in the file.
        
        Args:
            relative_path: Path of the file to edit, relative to workspace root.
            search_content: The exact text block to search for.
            replace_content: The new text block to replace the search_content with.
        """
        try:
            target_file = self._resolve(relative_path)
            if not os.path.exists(target_file):
                return f"Error: File '{relative_path}' does not exist."
                
            print_action("MODIFY", f"Patching file: {relative_path}")
            
            with open(target_file, "r", encoding="utf-8") as f:
                content = f.read()
                
            if search_content not in content:
                return (
                    f"Error: Could not find search_content in '{relative_path}'. "
                    "Make sure your search block matches the file content exactly, "
                    "including spaces, indentation, and newlines."
                )
                
            # Replace exactly once to be safe
            new_content = content.replace(search_content, replace_content, 1)
            
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(new_content)
                
            # Display patch action
            print_code_preview(relative_path, replace_content)
            return f"Successfully patched '{relative_path}'."
        except Exception as e:
            return f"Error patching file: {str(e)}"

    def delete_file(self, relative_path: str) -> str:
        """
        Delete a file in the workspace.
        
        Args:
            relative_path: Path of the file to delete, relative to workspace root.
        """
        try:
            target_file = self._resolve(relative_path)
            if not os.path.exists(target_file):
                return f"Error: File '{relative_path}' does not exist."
            if os.path.isdir(target_file):
                return f"Error: '{relative_path}' is a directory. To delete a directory, use terminal commands if necessary."
                
            print_action("DELETE", f"Deleting file: {relative_path}")
            os.remove(target_file)
            return f"Successfully deleted file '{relative_path}'."
        except Exception as e:
            return f"Error deleting file: {str(e)}"

    def run_terminal_command(self, command: str) -> str:
        """
        Run a terminal command in the shell inside the workspace directory.
        The command is executed with the working directory set to the workspace root.
        
        Args:
            command: The command to run in the terminal shell (e.g. 'pytest', 'npm install', 'python test.py').
        """
        try:
            print_action("RUN", f"Running command: {command}")
            
            # Execute command with cwd set to the workspace root
            # Note: shell=True is needed to run command lines with pipes, redirects, etc.
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.workspace_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=120  # Prevent infinite hangs
            )
            
            output = ""
            if result.stdout:
                output += f"--- STDOUT ---\n{result.stdout}\n"
            if result.stderr:
                output += f"--- STDERR ---\n{result.stderr}\n"
                
            if not output:
                output = "(Command executed with no output)"
                
            exit_code_str = f"Exit Code: {result.returncode}"
            print_action("RUN", f"Command completed. {exit_code_str}")
            
            return f"{exit_code_str}\n\n{output}"
        except subprocess.TimeoutExpired:
            print_action("RUN", "Command timed out after 120 seconds.")
            return "Error: Command timed out after 120 seconds."
        except Exception as e:
            return f"Error executing command: {str(e)}"
