# 🇧 🇴 🇷 🇳 🇪 🇴 🇦 🇮 (BorneoAI)

BorneoAI is a premium Python-based Command Line Interface (CLI) Coding Agent and Chat Assistant powered by the Google Gemini API (via Google AI Studio). It is designed to act as your autonomous programming partner, featuring rich terminal UI, step-by-step trace reporting, and an isolated sandboxed workspace.

---

## ✨ Features

- **Double Operating Modes**:
  - 💬 **Chat Mode**: Inspect files, list directories, explain codebase structures, and walk through design patterns in detail. (Read-only access ensures zero risk to your files).
  - 🛠 **Agent Mode**: Read, create, surgically modify (patch), and delete files, and run shell/terminal commands directly. The agent runs tests, parses compilation issues, and loops until the code works.
- **Visual Process Tracing**: Beautiful, color-coded logging of exactly what BorneoAI is doing (`[CREATE]`, `[MODIFY]`, `[READ]`, `[DELETE]`, `[RUN]`, `[THINK]`) using custom symbols and layout.
- **Model Selection & Wizard**: Supports `gemini-2.5-flash`, `gemini-2.5-pro`, `gemma-2-27b-it`, or any custom model supported by Google AI Studio.
- **Sandboxed Workspace**: BorneoAI is anchored to the workspace root directory where it is launched (or defined via `-d`). It cannot traverse, write, or modify files outside the workspace root, keeping the rest of your operating system safe.
- **Global Path Execution**: Install once and invoke `borneoai` from any directory.

---

## 🚀 Installation & Setup

1. **Prerequisites**: Ensure you have Python 3.10+ and `pip` installed.
   - For Termux users, pre-compile system cryptography binaries first to avoid compilation bottlenecks:
     ```bash
     pkg install python-cryptography
     ```

2. **Install BorneoAI**: Install in editable mode from the project root:
   ```bash
   pip install -e .
   ```

3. **Configure API Key**: Get a free Gemini API Key from [Google AI Studio](https://aistudio.google.com/) and run:
   ```bash
   borneoai config
   ```
   *Alternatively, you can export `GEMINI_API_KEY` in your shell profile:*
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```

---

## 🛠 Usage Guide

Launch BorneoAI from any terminal path:
```bash
borneoai
```
This triggers an interactive main menu:
```
borneoai Terminal UI
[1] Chat Mode     -(Inspect, explain code, and discuss design pattern)
[2] Agent Mode    -(Create/edit code, manage files, run terminal commands)
[3] Configuration -(Wizard setup for API key and default models)
[4] Exit
```

### Direct Commands

You can bypass the menu and directly launch features:

#### 1. Chat Mode
Discuss architecture and explain code with read-only workspace access:
```bash
borneoai chat
```
Or ask a direct question:
```bash
borneoai chat "Explain the structure of this project"
```

#### 2. Agent Mode
Let the agent build, test, and write code:
```bash
borneoai agent
```
Or execute a single-turn request:
```bash
borneoai agent "Create a fastapi server with a greeting route and run it to verify"
```

### Command Flags

- **Override Model**: Select a different model on-the-fly (e.g., using the smarter Pro model for debugging):
  ```bash
  borneoai agent -m gemini-2.5-pro "Debug this python project and fix failing tests"
  ```
- **Set Workspace**: Run BorneoAI on a different folder:
  ```bash
  borneoai chat -d /path/to/other/project
  ```

---

## 🎨 Design & Aesthetic Elements

BorneoAI uses **Rich** and **Prompt Toolkit** to deliver a premium terminal UI experience:
- **Markdown Rendering**: AI responses are fully formatted as beautiful GitHub-flavored markdown panels.
- **Syntax Highlighting**: Real-time syntax-colored views for code files read/written.
- **Action Tracing**: Distinctive indicators for actions:
  - 📝 `[CREATE]` in **green** when writing new files.
  - ✏️ `[MODIFY]` in **yellow** when editing/patching files.
  - 📖 `[READ]` in **cyan** when listing or viewing files.
  - 🗑️ `[DELETE]` in **red** when removing files.
  - 🐚 `[RUN]` in **magenta** when executing terminal commands.
  - 🧠 `[THINK]` in **blue** when generating responses.
