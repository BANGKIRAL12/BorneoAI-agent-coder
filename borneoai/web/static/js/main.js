let session_id = '';
let isSending = false;
let uploadedImages = [];
let activeMode = 'chat';

// Setup Custom Marked Renderer with syntax highlighting and premium solid blocks
const renderer = new marked.Renderer();

renderer.code = function(code, language, escaped) {
    const validLang = (language && hljs.getLanguage(language)) ? language : 'plaintext';
    let highlighted;
    try {
        highlighted = hljs.highlight(code, { language: validLang }).value;
    } catch (e) {
        highlighted = hljs.highlightAuto(code).value;
    }
    
    return `
        <div class="code-block-container my-4 rounded-lg overflow-hidden border border-slate-700 bg-slate-950 font-mono text-sm shadow-md">
            <div class="flex items-center justify-between px-4 py-2 bg-slate-900 border-b border-slate-800 text-xs text-slate-400 select-none">
                <span class="font-semibold uppercase">${validLang}</span>
                <button onclick="copyCode(this)" class="flex items-center gap-1.5 hover:text-slate-200 transition-colors py-0.5 px-1.5 rounded bg-slate-800 hover:bg-slate-700">
                    <i class="fa-regular fa-copy"></i>
                    <span>Copy</span>
                </button>
            </div>
            <pre class="p-4 overflow-x-auto m-0 !bg-transparent"><code class="hljs language-${validLang}">${highlighted}</code></pre>
        </div>
    `;
};

renderer.table = function(header, body) {
    return `
        <div class="my-6 overflow-x-auto rounded-lg border border-[var(--border-color)] shadow-sm">
            <table class="w-full border-collapse text-left text-sm text-[var(--text-primary)]">
                <thead class="bg-indigo-500/10 border-b border-[var(--border-color)] text-[var(--text-primary)] uppercase text-xs font-semibold">
                    ${header}
                </thead>
                <tbody class="divide-y divide-[var(--border-color)] bg-[var(--bg-card)]/40">
                    ${body}
                </tbody>
            </table>
        </div>
    `;
};

renderer.tablerow = function(content) {
    return `<tr class="hover:bg-indigo-500/5 transition-colors">${content}</tr>`;
};

renderer.tablecell = function(content, flags) {
    const type = flags.header ? 'th' : 'td';
    const align = flags.align ? `text-${flags.align}` : '';
    return `<${type} class="px-4 py-3 border-r last:border-r-0 border-[var(--border-color)] ${align}">${content}</${type}>`;
};

marked.use({ renderer });

async function init() {
    session_id = 'sess_' + Math.random().toString(36).substr(2, 9);
    initTheme();
    await loadSettings();
    setMode('chat');
}

async function loadSettings() {
    try {
        const res = await fetch('/api/config');
        const data = await res.json();
        document.getElementById('cfg-api-key').value = data.api_key;
        document.getElementById('cfg-model').value = data.default_model;
        
        // Populate model and workspace path in sidebar
        const modelSpan = document.getElementById('active-model');
        if (modelSpan && data.default_model) {
            modelSpan.innerText = data.default_model;
            modelSpan.title = data.default_model;
        }
        
        const workspaceDiv = document.getElementById('workspace-path');
        if (workspaceDiv && data.workspace_root) {
            workspaceDiv.innerText = data.workspace_root;
            workspaceDiv.title = data.workspace_root;
        }
    } catch (e) {
        console.error('Failed to load configuration:', e);
    }
}

async function saveSettings() {
    const api_key = document.getElementById('cfg-api-key').value;
    const default_model = document.getElementById('cfg-model').value;
    
    try {
        const res = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key, default_model })
        });
        
        if (res.ok) {
            alert('Settings saved successfully!');
            toggleSettings();
            await loadSettings(); // Reload to update UI elements
        } else {
            alert('Failed to save settings.');
        }
    } catch (e) {
        alert('Error saving settings: ' + e.message);
    }
}

function toggleSettings() {
    const modal = document.getElementById('settings-modal');
    modal.classList.toggle('hidden');
}

function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    const isDark = savedTheme === 'dark';
    if (isDark) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
    updateThemeIcon(isDark);
}

function toggleTheme() {
    const isDark = document.documentElement.classList.toggle('dark');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    updateThemeIcon(isDark);
}

function updateThemeIcon(isDark) {
    const btn = document.getElementById('theme-toggle-btn');
    if (btn) {
        const icon = btn.querySelector('i');
        if (isDark) {
            icon.className = 'fa-solid fa-sun text-lg';
            btn.title = 'Switch to Light Mode';
        } else {
            icon.className = 'fa-solid fa-moon text-lg';
            btn.title = 'Switch to Dark Mode';
        }
    }
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    if (sidebar.classList.contains('-translate-x-full')) {
        sidebar.classList.remove('-translate-x-full');
        overlay.classList.remove('hidden');
    } else {
        sidebar.classList.add('-translate-x-full');
        overlay.classList.add('hidden');
    }
}

function setMode(mode) {
    activeMode = mode;
    
    // Update sidebar buttons
    const btnChat = document.getElementById('sidebar-mode-chat');
    const btnAgent = document.getElementById('sidebar-mode-agent');
    const dropdown = document.getElementById('mode-select');
    const badge = document.getElementById('header-mode-badge');
    const desc = document.getElementById('header-mode-desc');
    
    if (mode === 'chat') {
        if (btnChat) btnChat.className = "py-2 px-3 text-xs font-semibold rounded-lg border border-indigo-600 bg-indigo-600 text-white transition-all shadow flex flex-col items-center justify-center gap-1.5";
        if (btnAgent) btnAgent.className = "py-2 px-3 text-xs font-semibold rounded-lg border border-[var(--border-color)] hover:border-indigo-500 text-[var(--text-primary)] hover:bg-indigo-500/10 transition-all flex flex-col items-center justify-center gap-1.5";
        if (dropdown) dropdown.value = 'chat';
        if (badge) {
            badge.innerText = 'Chat Mode';
            badge.className = "px-2.5 py-0.5 rounded text-[10px] font-bold uppercase bg-indigo-600 text-white";
        }
        if (desc) desc.innerText = 'Explain & Discuss Code';
    } else {
        if (btnAgent) btnAgent.className = "py-2 px-3 text-xs font-semibold rounded-lg border border-indigo-600 bg-indigo-600 text-white transition-all shadow flex flex-col items-center justify-center gap-1.5";
        if (btnChat) btnChat.className = "py-2 px-3 text-xs font-semibold rounded-lg border border-[var(--border-color)] hover:border-indigo-500 text-[var(--text-primary)] hover:bg-indigo-500/10 transition-all flex flex-col items-center justify-center gap-1.5";
        if (dropdown) dropdown.value = 'agent';
        if (badge) {
            badge.innerText = 'Agent Mode';
            badge.className = "px-2.5 py-0.5 rounded text-[10px] font-bold uppercase bg-violet-600 text-white";
        }
        if (desc) desc.innerText = 'Autonomous Developer & Shell Executor';
    }
}

function syncModeFromDropdown(select) {
    setMode(select.value);
}

function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

function useSuggestion(text) {
    const input = document.getElementById('user-input');
    input.value = text;
    autoResize(input);
    input.focus();
}

function clearChat() {
    if (confirm("Clear current conversation?")) {
        const container = document.getElementById('chat-container');
        const welcome = document.getElementById('welcome-screen');
        
        // Remove all children except welcome screen
        container.innerHTML = '';
        container.appendChild(welcome);
        welcome.classList.remove('hidden');
        
        // Reset session ID
        session_id = 'sess_' + Math.random().toString(36).substr(2, 9);
    }
}

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const res = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (data.filepath) {
            uploadedImages.push(data.filepath);
            renderUploadedImages();
            addSystemMessage(`Attached image: ${file.name}`);
        }
    } catch (e) {
        console.error('Upload failed', e);
        alert('Failed to upload image: ' + e.message);
    }
}

function renderUploadedImages() {
    const container = document.getElementById('image-preview-container');
    if (!container) return;
    
    if (uploadedImages.length === 0) {
        container.classList.add('hidden');
        container.innerHTML = '';
        return;
    }
    
    container.classList.remove('hidden');
    container.innerHTML = uploadedImages.map((img, idx) => {
        const filename = img.split('/').pop();
        const url = `/borneoai_uploads/${filename}`;
        return `
            <div class="relative group w-14 h-14 rounded-lg border border-[var(--border-color)] bg-[var(--bg-main)] overflow-hidden flex items-center justify-center shrink-0 shadow-sm">
                <img src="${url}" class="w-full h-full object-cover" onerror="this.style.display='none'; this.nextElementSibling.style.display='block';" />
                <i class="fa-regular fa-image text-[var(--text-secondary)] text-lg hidden"></i>
                <button onclick="removeUploadedImage(${idx})" class="absolute top-0.5 right-0.5 bg-rose-600/90 text-white rounded-full w-4 h-4 flex items-center justify-center text-[10px] hover:bg-rose-700 transition-colors shadow" title="Remove image">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            </div>
        `;
    }).join('');
}

function removeUploadedImage(index) {
    uploadedImages.splice(index, 1);
    renderUploadedImages();
}

function addSystemMessage(text) {
    const container = document.getElementById('chat-container');
    const div = document.createElement('div');
    div.className = 'text-center text-[11px] text-[var(--text-secondary)] font-medium my-2 bg-[var(--bg-card)] border border-[var(--border-color)] py-1 px-3 rounded-lg w-fit mx-auto shadow-sm';
    div.innerText = text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function addUserMessage(text) {
    const container = document.getElementById('chat-container');
    const div = document.createElement('div');
    div.className = 'flex justify-end p-2';
    div.innerHTML = `
        <div class="user-bubble bg-indigo-600 text-white p-3.5 rounded-lg shadow-md max-w-[80%] text-sm md:text-base leading-relaxed break-words">
            ${text.replace(/\n/g, '<br>')}
        </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function createAiMessageElement() {
    const container = document.getElementById('chat-container');
    const div = document.createElement('div');
    div.className = 'ai-message-wrapper flex gap-4 p-4 md:p-6 rounded-lg bg-[var(--bg-card)] border border-[var(--border-color)] transition-all';
    
    // Determine header style according to mode
    const isAgent = activeMode === 'agent';
    const badgeText = isAgent ? 'Agent' : 'Chat';
    const badgeColor = isAgent ? 'bg-violet-600' : 'bg-indigo-600';
    
    div.innerHTML = `
        <!-- AI Icon -->
        <div class="w-9 h-9 rounded-lg ${badgeColor} flex items-center justify-center shrink-0 text-white shadow-md">
            <i class="fa-solid fa-robot text-sm"></i>
        </div>
        
        <div class="flex-1 min-w-0 space-y-4">
            <div class="flex items-center justify-between">
                <span class="text-sm font-bold text-[var(--text-primary)]">BorneoAI</span>
                <span class="text-[10px] font-bold uppercase px-2 py-0.5 rounded text-white ${badgeColor}">${badgeText}</span>
            </div>
            
            <!-- Tool executions area (collapsible) -->
            <div class="tools-accordion hidden flex flex-col gap-2">
                <button onclick="toggleToolsAccordion(this)" class="flex items-center gap-2 text-xs font-semibold text-indigo-500 hover:text-indigo-400 dark:text-indigo-400 dark:hover:text-indigo-300 transition-colors py-1.5 px-3 bg-indigo-500/10 rounded border border-indigo-500/20 w-fit">
                    <i class="fa-solid fa-chevron-down transform transition-transform duration-200"></i>
                    <span>Running tasks & tools...</span>
                </button>
                <div class="tools-log-container hidden pl-4 border-l border-[var(--border-color)] mt-2 space-y-2 text-xs font-mono text-[var(--text-primary)]">
                </div>
            </div>
            
            <!-- Main AI Response Content -->
            <div class="ai-content text-[var(--text-primary)] leading-relaxed prose prose-invert max-w-none text-sm md:text-base">
                <!-- Floating typing indicator initially -->
                <div class="flex items-center gap-1.5 py-2">
                    <span class="w-2 h-2 rounded-full bg-indigo-500 animate-bounce" style="animation-delay: 0ms"></span>
                    <span class="w-2 h-2 rounded-full bg-indigo-500 animate-bounce" style="animation-delay: 150ms"></span>
                    <span class="w-2 h-2 rounded-full bg-indigo-500 animate-bounce" style="animation-delay: 300ms"></span>
                </div>
            </div>
        </div>
    `;
    
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    
    return {
        wrapper: div,
        textBox: div.querySelector('.ai-content'),
        toolsBox: div.querySelector('.tools-log-container'),
        toolsAccordion: div.querySelector('.tools-accordion')
    };
}

async function sendMessage() {
    if (isSending) {
        location.reload(); 
        return;
    }
    
    const input = document.getElementById('user-input');
    const prompt = input.value.trim();
    
    if (!prompt && uploadedImages.length === 0) return;
    
    isSending = true;
    setSendingState(true);
    
    // Hide welcome screen
    const welcome = document.getElementById('welcome-screen');
    if (welcome) welcome.classList.add('hidden');
    
    addUserMessage(prompt);
    input.value = '';
    input.style.height = 'auto';
    
    const responseBox = createAiMessageElement();
    let accumulatedAiText = "";
    let isFirstAiChunk = true;
    
    const payload = {
        session_id: session_id,
        prompt: prompt,
        mode: activeMode,
        images: [...uploadedImages]
    };
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const errText = await response.text();
            throw new Error(errText || `HTTP ${response.status}`);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        let buffer = '';
        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n\n');
            buffer = lines.pop();
            
            for (const line of lines) {
                if (line.trim().startsWith('data: ')) {
                    const data = JSON.parse(line.substring(6));
                    if (data.status === 'done') {
                        // Finished
                    } else {
                        if (data.type === 'ai') {
                            if (isFirstAiChunk) {
                                responseBox.textBox.innerHTML = "";
                                isFirstAiChunk = false;
                            }
                            accumulatedAiText += data.text;
                            responseBox.textBox.innerHTML = marked.parse(accumulatedAiText);
                        } else {
                            processAiChunk(responseBox, data);
                        }
                    }
                }
            }
        }
    } catch (e) {
        if (isFirstAiChunk) {
            responseBox.textBox.innerHTML = "";
        }
        responseBox.textBox.innerHTML += `
            <div class="p-3 bg-red-500/10 border border-red-500/30 text-red-500 dark:text-red-400 rounded-lg text-sm my-2 shadow-sm">
                <i class="fa-solid fa-circle-exclamation mr-1.5"></i><b>System Error:</b> ${e.message}
            </div>
        `;
    } finally {
        isSending = false;
        setSendingState(false);
        uploadedImages = [];
        renderUploadedImages();
        
        if (isFirstAiChunk) {
            responseBox.textBox.innerHTML = "";
        }
    }
}

function processAiChunk(responseBox, data) {
    const { text, type } = data;
    
    // Show tools container accordion
    responseBox.toolsAccordion.classList.remove('hidden');
    const container = responseBox.toolsBox;
    
    const div = document.createElement('div');
    
    if (type === 'action') {
        div.className = 'flex items-start gap-2 py-1 text-xs border-l-2 border-indigo-500 pl-2 bg-indigo-500/5 my-1 rounded-r';
        div.innerHTML = `
            <span class="text-indigo-500 font-bold shrink-0">[ACTION]</span>
            <span class="text-[var(--text-primary)]">${text}</span>
        `;
    } else if (type === 'info' || type === 'success' || type === 'warning' || type === 'error') {
        let textClass = 'text-cyan-500';
        let prefix = 'ℹ [INFO]';
        let bgClass = 'bg-cyan-500/5 border-cyan-500/20';
        
        if (type === 'success') {
            textClass = 'text-emerald-500';
            prefix = '✔ [SUCCESS]';
            bgClass = 'bg-emerald-500/5 border-emerald-500/20';
        } else if (type === 'warning') {
            textClass = 'text-amber-500';
            prefix = '⚠ [WARNING]';
            bgClass = 'bg-amber-500/5 border-amber-500/20';
        } else if (type === 'error') {
            textClass = 'text-rose-500';
            prefix = '✘ [ERROR]';
            bgClass = 'bg-rose-500/5 border-rose-500/20';
        }
        
        div.className = `p-2 my-1 border rounded text-xs ${bgClass}`;
        div.innerHTML = `
            <span class="${textClass} font-bold mr-1.5">${prefix}</span>
            <span class="text-[var(--text-primary)]">${text}</span>
        `;
    } else if (type === 'code') {
        const fileHeader = text.split('\n\n')[0] || 'Code preview';
        const fileContent = text.substring(fileHeader.length).trim();
        
        div.className = 'flex flex-col gap-1 py-1.5 my-1';
        div.innerHTML = `
            <span class="text-[var(--text-secondary)] font-bold flex items-center gap-1">
                <i class="fa-regular fa-file-lines text-indigo-500"></i> ${fileHeader}
            </span>
            <pre class="p-2 bg-slate-950 rounded border border-slate-800 text-[11px] overflow-x-auto max-h-48 text-slate-300 font-mono">${fileContent}</pre>
        `;
    } else if (type === 'status') {
        div.className = 'text-xs text-indigo-500 dark:text-indigo-400 italic animate-pulse flex items-center gap-1.5 py-1';
        div.innerHTML = `
            <i class="fa-solid fa-spinner animate-spin"></i>
            <span>${text}</span>
        `;
        container.appendChild(div);
        setTimeout(() => div.remove(), 4000);
        document.getElementById('chat-container').scrollTop = document.getElementById('chat-container').scrollHeight;
        return;
    }
    
    container.appendChild(div);
    document.getElementById('chat-container').scrollTop = document.getElementById('chat-container').scrollHeight;
}

function toggleToolsAccordion(button) {
    const logContainer = button.nextElementSibling;
    const icon = button.querySelector('i');
    
    if (logContainer.classList.contains('hidden')) {
        logContainer.classList.remove('hidden');
        icon.classList.add('rotate-180');
    } else {
        logContainer.classList.add('hidden');
        icon.classList.remove('rotate-180');
    }
}

function copyCode(button) {
    const pre = button.closest('.code-block-container').querySelector('pre');
    const code = pre.innerText;
    
    navigator.clipboard.writeText(code).then(() => {
        const span = button.querySelector('span');
        const icon = button.querySelector('i');
        
        span.innerText = 'Copied!';
        icon.className = 'fa-solid fa-check text-green-400';
        
        setTimeout(() => {
            span.innerText = 'Copy';
            icon.className = 'fa-regular fa-copy';
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy text', err);
    });
}

function setSendingState(sending) {
    const btn = document.getElementById('send-btn');
    const icon = document.getElementById('send-icon');
    
    if (sending) {
        btn.className = 'bg-red-500 hover:bg-red-600 text-white rounded-lg transition-all shrink-0 flex items-center justify-center w-11 h-11 shadow-md';
        icon.className = 'fa-solid fa-square text-sm';
    } else {
        btn.className = 'bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-all shrink-0 flex items-center justify-center w-11 h-11 shadow-md';
        icon.className = 'fa-solid fa-paper-plane text-sm';
    }
}

function startSpeech() {
    try {
        const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.lang = 'en-US';
        recognition.start();
        
        addSystemMessage("Speech recognition active. Speak now...");
        
        recognition.onresult = (event) => {
            const text = event.results[0][0].transcript;
            const input = document.getElementById('user-input');
            input.value = text;
            autoResize(input);
        };
        
        recognition.onerror = (event) => {
            console.error('Speech recognition error', event.error);
            addSystemMessage("Speech recognition error: " + event.error);
        };
    } catch (e) {
        alert("Speech Recognition not supported on this browser.");
    }
}

init();
