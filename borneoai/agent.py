import os
import sys
from borneoai.tools import FileSandbox
from borneoai.ui import console, show_spinner, print_ai_markdown, print_error, print_action, print_info
from borneoai.gemini_client import GeminiRESTClient, TOOLS_DECLARATIONS

def run_agent_turn(client, prompt, images=None, videos=None, system_instruction=None, tools_map=None, tools_declarations=None):
    """Runs a single agent turn, executing tools requested by Gemini and feeding back responses."""
    if prompt or images or videos:
        parts = []
        if prompt:
            parts.append({"text": prompt})
        if images:
            for img_path in images:
                try:
                    parts.append(client.encode_image(img_path))
                except Exception as e:
                    print_error(f"Failed to load image {img_path}: {e}")
        if videos:
            for vid_path in videos:
                try:
                    parts.append(client.encode_video(vid_path))
                except Exception as e:
                    print_error(f"Failed to load video {vid_path}: {e}")
        
        client.append_message("user", parts)

    max_turns = 10
    turns = 0
        
    while turns < max_turns:
	    turns += 1

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
            # If the response doesn't contain candidates, check for error details
            print_error(f"Received empty response from Gemini: {response}")
            return False
            
        candidate = response["candidates"][0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])
        
        if not parts:
            break
            
        # Append the model's message parts to history
        client.append_message("model", parts)
        
        # Parse text content and function calls
        text_content = ""
        function_calls = []
        
        for part in parts:
            if "text" in part:
                text_content += part["text"]
            elif "functionCall" in part:
                function_calls.append(part["functionCall"])
                
        # Display AI text explanation
        if text_content.strip():
            print_ai_markdown(text_content, role_title="BorneoAI Agent")
            
        # Stop loop if no function calls are present
        if not function_calls:
            break
            
        # Process and execute function calls
        response_parts = []
        for call in function_calls:
            name = call["name"]
            args = call.get("args", {})
            
            # Execute matching tool
            if name in tools_map:
                try:
                    # Execute tool function with keyword args from Gemini
                    result = tools_map[name](**args)
                except Exception as e:
                    result = f"Error executing tool {name}: {str(e)}"
            else:
                result = f"Error: Tool '{name}' is not supported."
                print_action("ERROR", f"Attempted to call unregistered tool: {name}")
                
            # Create a function response part structure
            response_parts.append({
                "functionResponse": {
                    "name": name,
                    "response": {"result": str(result)}
                }
            })
            
        # Append function responses with role 'function'
        client.append_message("function", response_parts)
        
	if turns >= max_turns:
        print_error("Agent dihentikan karena mencapai batas maksimal putaran (Max Turns Limit).")
        return False

    return True

def start_agent_mode(api_key, model_name, workspace_root, single_prompt=None):
    """Starts Agent Mode, either executing a single instruction or booting the shell."""
    client = GeminiRESTClient(api_key, model_name)
    sandbox = FileSandbox(workspace_root)
    
    # Map tool names to Python implementations
    tools_map = {
        "list_directory": sandbox.list_directory,
        "read_file": sandbox.read_file,
        "write_file": sandbox.write_file,
        "patch_file": sandbox.patch_file,
        "delete_file": sandbox.delete_file,
        "run_terminal_command": sandbox.run_terminal_command
    }
    
    # Filter tools declarations for Agent Mode (all tools are allowed)
    agent_tools_declarations = TOOLS_DECLARATIONS
    
    system_instruction = (
        "You are BorneoAI, a highly skilled and autonomous AI software engineering agent.\n"
        f"Your current workspace root directory is: {os.path.abspath(workspace_root)}\n"
        "You have direct access to tools that let you read, write, edit, and delete files, list directories, and execute shell commands.\n\n"
        "Core Sandboxing Rule:\n"
        "- You MUST NOT read or write files outside the workspace root directory. Any attempt to write/edit/read files outside "
        "will result in a Security Violation.\n"
        "- All paths you pass to file tools must be relative to the workspace root.\n\n"
        "Guidelines for Success:\n"
        "1. Understand before acting: List the directory contents or read files to understand the project structure and context first.\n"
        "2. Think step-by-step: Formulate a plan and explain it to the user before running tools.\n"
        "3. Write production-ready code: Never write placeholder code, incomplete code, or mock implementations. Write complete, well-documented code.\n"
        "4. Edit files surgical-style: Use `patch_file` to make targeted changes to files. Specify the exact search_content block to replace.\n"
        "5. Test your edits: Always run terminal commands to build, run, test, lint, or execute your code (e.g., using `python <file>.py`, `pytest`, `npm test` etc.) to verify your changes are correct and did not introduce bugs.\n"
        "6. Auto-recovery: If a command fails or a compiler/test error occurs, analyze the error output carefully, patch the code to fix the error, and re-run tests. Continue this loop until the task is successfully accomplished.\n"
        "7. Delete files only when requested or when cleaning up temporary files you created.\n\n"
        "Work autonomously. Do not ask for user permission before executing commands or creating files once the task has started. Just execute them."
    )
    
    if single_prompt:
        print_info(f"Starting Agent Mode in [bold cyan]{workspace_root}[/bold cyan] to perform single task...")
        print_info(f"Model: [bold green]{model_name}[/bold green]")
        run_agent_turn(
            client=client,
            prompt=single_prompt,
            images=None,
            videos=None,
            system_instruction=system_instruction,
            tools_map=tools_map,
            tools_declarations=agent_tools_declarations
        )
        print_info("Task finished.")
    else:
        from borneoai.shell import start_interactive_shell
        
        print_info(f"Starting Interactive Agent Mode in [bold cyan]{workspace_root}[/bold cyan]")
        print_info(f"Model: [bold green]{model_name}[/bold green]")
        print_info("Type your instructions (e.g., 'create a FastAPI server in server.py and run it to verify'). Type 'exit' to quit.")
        
        def agent_turn_handler(prompt, images, videos=None):
            return run_agent_turn(
                client=client,
                prompt=prompt,
                images=images,
                videos=videos,
                system_instruction=system_instruction,
                tools_map=tools_map,
                tools_declarations=agent_tools_declarations
            )
            
        start_interactive_shell("borneoai-agent", agent_turn_handler, workspace_root)
