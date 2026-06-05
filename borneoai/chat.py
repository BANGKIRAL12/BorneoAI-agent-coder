import os
import sys
from borneoai.tools import FileSandbox
from borneoai.ui import console, show_spinner, print_ai_markdown, print_error, print_action, print_info
from borneoai.gemini_client import GeminiRESTClient, TOOLS_DECLARATIONS

def run_chat_turn(client, prompt, images=None, system_instruction=None, tools_map=None, tools_declarations=None):
    """Runs a single chat turn, resolving read tools if requested by Gemini."""
    if prompt or images:
        parts = []
        if prompt:
            parts.append({"text": prompt})
        if images:
            for img_path in images:
                try:
                    parts.append(client.encode_image(img_path))
                except Exception as e:
                    print_error(f"Failed to load image {img_path}: {e}")
        
        client.append_message("user", parts)
        
    while True:
        with show_spinner("AI is thinking..."):
            try:
                response = client.generate_content(
                    system_instruction=system_instruction,
                    tools_declarations=tools_declarations
                )
            except Exception as e:
                print_error(f"\nGemini API Error: {e}")
                return False
                
        if "candidates" not in response or not response["candidates"]:
            print_error(f"Received empty response from Gemini: {response}")
            return False
            
        candidate = response["candidates"][0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])
        
        if not parts:
            break
            
        client.append_message("model", parts)
        
        text_content = ""
        function_calls = []
        
        for part in parts:
            if "text" in part:
                text_content += part["text"]
            elif "functionCall" in part:
                function_calls.append(part["functionCall"])
                
        if text_content.strip():
            print_ai_markdown(text_content, role_title="BorneoAI Explainer")
            
        if not function_calls:
            break
            
        # Execute tool calls (should only be read_file or list_directory in Chat mode)
        response_parts = []
        for call in function_calls:
            name = call["name"]
            args = call.get("args", {})
            
            if name in tools_map:
                try:
                    result = tools_map[name](**args)
                except Exception as e:
                    result = f"Error executing tool {name}: {str(e)}"
            else:
                result = f"Error: Tool '{name}' is not authorized in Chat Mode."
                print_action("ERROR", f"Attempted to call unauthorized tool: {name}")
                
            response_parts.append({
                "functionResponse": {
                    "name": name,
                    "response": {"result": str(result)}
                }
            })
            
        client.append_message("function", response_parts)
        
    return True

def start_chat_mode(api_key, model_name, workspace_root, single_prompt=None):
    """Starts Chat Mode, facilitating codebase discussion and explanations."""
    client = GeminiRESTClient(api_key, model_name)
    sandbox = FileSandbox(workspace_root)
    
    # In Chat Mode, we ONLY allow list_directory and read_file.
    tools_map = {
        "list_directory": sandbox.list_directory,
        "read_file": sandbox.read_file
    }
    
    # Filter declarations to only include read actions
    chat_tools_declarations = [
        decl for decl in TOOLS_DECLARATIONS 
        if decl["name"] in ["list_directory", "read_file"]
    ]
    
    # Try to scan the project directory to give the AI context about the structure on startup
    project_structure = ""
    try:
        items = os.listdir(workspace_root)
        if items:
            structure_list = []
            for item in sorted(items)[:30]:  # Limit to 30 items for display sanity
                is_dir = os.path.isdir(os.path.join(workspace_root, item))
                marker = "[DIR] " if is_dir else "      "
                structure_list.append(f" - {marker}{item}")
            project_structure = "\n".join(structure_list)
            if len(items) > 30:
                project_structure += f"\n - ... and {len(items)-30} more items."
        else:
            project_structure = "(Directory is empty)"
    except Exception:
        project_structure = "(Could not list directory structure)"

    system_instruction = (
        "You are BorneoAI, a senior software engineer and system architect running in Chat Mode.\n"
        f"The user's project workspace root is at: {os.path.abspath(workspace_root)}\n"
        "Your role is to explain code, design patterns, file structures, and project systems, "
        "and provide comprehensive, detailed guidance on how to write or debug code.\n\n"
        "Here is the list of top-level files and folders in the workspace root:\n"
        f"{project_structure}\n\n"
        "Capabilities & Constraints:\n"
        "1. You CANNOT write, modify, or delete files. You CANNOT execute shell/terminal commands.\n"
        "2. You CAN read files and list directories using the `read_file` and `list_directory` tools. "
        "   If the user asks you to explain, review, or debug a file, ALWAYS run the `read_file` tool to inspect the actual code first.\n"
        "3. Provide very clear, structured, and deep explanations of how things work. Use Markdown formatting, bullet points, and code blocks for readability.\n"
        "4. Be helpful, professional, and friendly."
    )
    
    if single_prompt:
        print_info(f"Starting Chat Mode in [bold cyan]{workspace_root}[bold cyan] to answer single prompt...")
        print_info(f"Model: [bold green]{model_name}[/bold green]")
        # For single prompt, we don't have interactive image selection, so images=None
        run_chat_turn(client, single_prompt, None, system_instruction, tools_map, chat_tools_declarations)
    else:
        from borneoai.shell import start_interactive_shell
        
        print_info(f"Starting Chat Mode in [bold cyan]{workspace_root}[/bold cyan]")
        print_info(f"Model: [bold green]{model_name}[/bold green]")
        print_info("Type your questions (e.g., 'explain the project structure' or 'review setup.py'). Type 'exit' to quit.")
        
        def chat_turn_handler(prompt, images):
            return run_chat_turn(client, prompt, images, system_instruction, tools_map, chat_tools_declarations)
            
        start_interactive_shell("borneoai-chat", chat_turn_handler, workspace_root)
