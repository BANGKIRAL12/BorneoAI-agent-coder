import os
import json
import uuid
import queue
from flask import Flask, request, jsonify, render_template, Response, stream_with_context, send_from_directory
from flask_cors import CORS
from borneoai.config import load_config, save_config
from borneoai.gemini_client import GeminiRESTClient
from borneoai.tools import FileSandbox
from borneoai.chat import run_chat_turn
from borneoai.agent import run_agent_turn
from borneoai.gemini_client import TOOLS_DECLARATIONS
from borneoai.ui import output_callback as ui_callback_ref

app = Flask(__name__, 
            static_folder='static', 
            template_folder='templates')
CORS(app)

# Global session storage: {session_id: {"client": client, "sandbox": sandbox, "mode": mode}}
sessions = {}

def get_session(session_id, mode=None):
    if session_id in sessions:
        return sessions[session_id]
    
    # Create new session
    config = load_config()
    api_key = config.get("api_key")
    model_name = config.get("default_model")
    
    if not api_key:
        return None
        
    client = GeminiRESTClient(api_key, model_name)
    sandbox = FileSandbox(os.getcwd())
    
    session = {
        "client": client,
        "sandbox": sandbox,
        "mode": mode or "chat"
    }
    sessions[session_id] = session
    return session

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    config = load_config()
    return jsonify({
        "api_key": "********" if config.get("api_key") else "",
        "default_model": config.get("default_model"),
        "gui_port": config.get("gui_port"),
        "workspace_root": os.path.abspath(os.getcwd())
    })

@app.route('/api/config', methods=['POST'])
def update_config():
    data = request.json
    api_key = data.get("api_key")
    default_model = data.get("default_model")
    
    if save_config(api_key, default_model):
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Failed to save config"}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json or {}
    session_id = data.get("session_id", "default")
    prompt = data.get("prompt", "")
    mode = data.get("mode", "chat")
    images = data.get("images", [])
    
    session = get_session(session_id, mode)
    if not session:
        return Response("API Key not configured", status=401)
    
    client = session["client"]
    sandbox = session["sandbox"]
    
    # Queue to capture outputs from the UI callbacks
    out_queue = queue.Queue()

    def gui_callback(text, type):
        out_queue.put({"text": text, "type": type})

    # Temporarily hijack the global UI callback for this request
    # Note: This is NOT thread-safe for multiple users but works for local single-user GUI.
    # For a production app, we'd need a more robust way to handle multiple streams.
    import borneoai.ui
    original_callback = borneoai.ui.output_callback
    borneoai.ui.output_callback = gui_callback

    def generate():
        try:
            # Run the AI turn in a separate thread or just call it and let the queue fill
            import threading
            
            if mode == "agent":
                tools_map = {
                    "list_directory": sandbox.list_directory,
                    "read_file": sandbox.read_file,
                    "write_file": sandbox.write_file,
                    "patch_file": sandbox.patch_file,
                    "delete_file": sandbox.delete_file,
                    "run_terminal_command": sandbox.run_terminal_command
                }
                tools_declarations = TOOLS_DECLARATIONS
                system_instruction = (
                    "You are BorneoAI, a highly skilled and autonomous AI software engineering agent.\n"
                    f"Your current workspace root directory is: {os.path.abspath(os.getcwd())}\n"
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
                
                target = lambda: run_agent_turn(
                    client=client,
                    prompt=prompt,
                    images=images,
                    videos=None,
                    system_instruction=system_instruction,
                    tools_map=tools_map,
                    tools_declarations=tools_declarations
                )
            else: # chat mode
                tools_map = {
                    "list_directory": sandbox.list_directory,
                    "read_file": sandbox.read_file
                }
                chat_tools_declarations = [
                    decl for decl in TOOLS_DECLARATIONS 
                    if decl["name"] in ["list_directory", "read_file"]
                ]
                system_instruction = (
                    "You are BorneoAI, a senior software engineer and system architect running in Chat Mode.\n"
                    f"The user's project workspace root is at: {os.path.abspath(os.getcwd())}\n"
                    "Your role is to explain code, design patterns, file structures, and project systems, "
                    "and provide comprehensive, detailed guidance on how to write or debug code.\n\n"
                    "Capabilities & Constraints:\n"
                    "1. You CANNOT write, modify, or delete files. You CANNOT execute shell/terminal commands.\n"
                    "2. You CAN read files and list directories using the `read_file` and `list_directory` tools. "
                    "   If the user asks you to explain, review, or debug a file, ALWAYS run the `read_file` tool to inspect the actual code first.\n"
                    "3. Provide very clear, structured, and deep explanations of how things work. Use Markdown formatting, bullet points, and code blocks for readability.\n"
                    "4. Be helpful, professional, and friendly."
                )
                
                target = lambda: run_chat_turn(
                    client=client,
                    prompt=prompt,
                    images=images,
                    videos=None,
                    system_instruction=system_instruction,
                    tools_map=tools_map,
                    tools_declarations=chat_tools_declarations
                )

            thread = threading.Thread(target=target)
            thread.start()

            while thread.is_alive() or not out_queue.empty():
                try:
                    data = out_queue.get(timeout=0.1)
                    yield f"data: {json.dumps(data)}\n\n"
                except queue.Empty:
                    continue
            
            yield "data: {\"status\": \"done\"}\n\n"

        finally:
            borneoai.ui.output_callback = original_callback

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/api/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    upload_dir = os.path.join(os.getcwd(), "borneoai_uploads")
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, file.filename)
    file.save(filepath)
    
    return jsonify({"filepath": filepath})

@app.route('/borneoai_uploads/<filename>')
def uploaded_file(filename):
    upload_dir = os.path.join(os.getcwd(), "borneoai_uploads")
    return send_from_directory(upload_dir, filename)

def run_gui(workspace_root=None):
    if workspace_root:
        os.chdir(workspace_root)
    config = load_config()
    port = config.get("gui_port", 12123)
    print(f"Starting BorneoAI GUI on http://localhost:{port}...")
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    run_gui()
