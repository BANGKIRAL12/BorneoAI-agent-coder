import json
import urllib.request
import urllib.error
import base64
import mimetypes

class GeminiRESTClient:
    def __init__(self, api_key, model_name="gemini-2.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self.history = []

    def encode_image(self, image_path):
        """Reads an image file and returns a Gemini-compatible inline_data part."""
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type or not mime_type.startswith("image/"):
            mime_type = "image/jpeg" # Fallback
            
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
            
        return {
            "inline_data": {
                "mime_type": mime_type,
                "data": image_data
            }
        }

    def generate_content(self, system_instruction=None, tools_declarations=None, contents=None):
        """
        Sends a request to the Gemini API generateContent endpoint.
        
        Args:
            system_instruction: The system instructions string to guide the model.
            tools_declarations: A list of function declarations dicts.
            contents: A list of message turn dicts. If None, self.history is used.
        """
        if contents is None:
            contents = self.history

        # Use the Gemini v1beta endpoint for generateContent
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        
        payload = {
            "contents": contents
        }
        
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }
            
        if tools_declarations:
            payload["tools"] = [
                {
                    "functionDeclarations": tools_declarations
                }
            ]
            
        # Optional: set safety settings or generation config if needed
        # We can configure maxOutputTokens or temperature here
        
        headers = {
            "Content-Type": "application/json"
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                resp_body = response.read().decode("utf-8")
                return json.loads(resp_body)
        except urllib.error.HTTPError as e:
            try:
                err_body = e.read().decode("utf-8")
                err_json = json.loads(err_body)
                msg = err_json.get("error", {}).get("message", str(e))
                raise Exception(f"HTTP {e.code}: {msg}")
            except Exception:
                raise Exception(f"HTTP Error {e.code}: {e.reason}")
        except Exception as e:
            raise Exception(f"Connection Failed: {e}")

    def append_message(self, role, parts):
        """Appends a standard chat turn to history."""
        self.history.append({
            "role": role,
            "parts": parts
        })

    def clear_history(self):
        self.history = []

# Define the exact tool schema templates in JSON Schema format
TOOLS_DECLARATIONS = [
    {
        "name": "list_directory",
        "description": "List all files and folders in a directory, relative to the workspace root.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "relative_path": {
                    "type": "STRING",
                    "description": "The directory path to list, relative to the workspace root. Default is '.'."
                }
            },
            "required": []
        }
    },
    {
        "name": "read_file",
        "description": "Read the entire content of a file in the workspace.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "relative_path": {
                    "type": "STRING",
                    "description": "Path of the file to read, relative to workspace root."
                }
            },
            "required": ["relative_path"]
        }
    },
    {
        "name": "write_file",
        "description": "Create a new file or completely overwrite an existing file with the given content.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "relative_path": {
                    "type": "STRING",
                    "description": "Path of the file to create or overwrite, relative to workspace root."
                },
                "content": {
                    "type": "STRING",
                    "description": "The text content to write into the file."
                }
            },
            "required": ["relative_path", "content"]
        }
    },
    {
        "name": "patch_file",
        "description": "Edit a file by replacing a specific block of text with new content. Use this to modify a section of a file without rewriting it entirely. The search_content must match EXACTLY a block of text in the file.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "relative_path": {
                    "type": "STRING",
                    "description": "Path of the file to edit, relative to workspace root."
                },
                "search_content": {
                    "type": "STRING",
                    "description": "The exact text block to search for in the file."
                },
                "replace_content": {
                    "type": "STRING",
                    "description": "The new text block to replace the search_content with."
                }
            },
            "required": ["relative_path", "search_content", "replace_content"]
        }
    },
    {
        "name": "delete_file",
        "description": "Delete a file in the workspace.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "relative_path": {
                    "type": "STRING",
                    "description": "Path of the file to delete, relative to workspace root."
                }
            },
            "required": ["relative_path"]
        }
    },
    {
        "name": "run_terminal_command",
        "description": "Run a terminal command in the shell inside the workspace directory.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "command": {
                    "type": "STRING",
                    "description": "The command to run in the terminal shell (e.g. 'pytest', 'npm install', 'python test.py')."
                }
            },
            "required": ["command"]
        }
    }
]
