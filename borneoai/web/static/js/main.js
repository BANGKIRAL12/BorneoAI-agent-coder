let session_id = '';
let isSending = false;
let uploadedImages = [];

async function init() {
    session_id = 'sess_' + Math.random().toString(36).substr(2, 9);
    await loadSettings();
}

async function loadSettings() {
    const res = await fetch('/api/config');
    const data = await res.json();
    document.getElementById('cfg-api-key').value = data.api_key;
    document.getElementById('cfg-model').value = data.default_model;
}

async function saveSettings() {
    const api_key = document.getElementById('cfg-api-key').value;
    const default_model = document.getElementById('cfg-model').value;
    
    const res = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key, default_model })
    });
    
    if (res.ok) {
        alert('Settings saved successfully!');
        toggleSettings();
    } else {
        alert('Failed to save settings.');
    }
}

function toggleSettings() {
    const modal = document.getElementById('settings-modal');
    modal.classList.toggle('hidden');
}

function toggleTheme() {
    alert('Theme feature coming soon!');
}

function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
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
            addSystemMessage(`Uploaded image: ${file.name}`);
        }
    } catch (e) {
        console.error('Upload failed', e);
    }
}

function addSystemMessage(text) {
    const container = document.getElementById('chat-container');
    const div = document.createElement('div');
    div.className = 'text-center text-xs text-gray-500 my-2';
    div.innerText = text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function addUserMessage(text) {
    const container = document.getElementById('chat-container');
    const div = document.createElement('div');
    div.className = 'flex justify-end';
    div.innerHTML = `
        <div class="user-bubble bg-purple-600 text-white p-3 rounded-2xl rounded-tr-none shadow-md">
            ${text}
        </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function createAiMessageElement() {
    const container = document.getElementById('chat-container');
    const div = document.createElement('div');
    div.className = 'ai-response flex gap-4';
    div.innerHTML = `
        <div class="w-8 h-8 rounded-full accent-bg flex items-center justify-center shrink-0 text-white font-bold text-xs">AI</div>
        <div class="flex-1 space-y-2">
            <p class="text-gray-400 text-xs font-medium uppercase tracking-wider">BorneoAI</p>
            <div class="ai-content text-gray-200 leading-relaxed prose prose-invert max-w-none">
            </div>
        </div>
    `;
    container.appendChild(div);
    return div.querySelector('.ai-content');
}

async function sendMessage() {
    if (isSending) {
        location.reload(); 
        return;
    }
    
    const input = document.getElementById('user-input');
    const prompt = input.value.trim();
    const mode = document.getElementById('mode-select').value;
    
    if (!prompt && uploadedImages.length === 0) return;
    
    isSending = true;
    setSendingState(true);
    
    addUserMessage(prompt);
    input.value = '';
    input.style.height = 'auto';
    
    const aiContentDiv = createAiMessageElement();
    
    try {
        const url = `/api/chat?session_id=${session_id}&prompt=${encodeURIComponent(prompt)}&mode=${mode}`;
        const response = await fetch(url);
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
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.substring(6));
                    if (data.status === 'done') {
                        // Finished
                    } else {
                        processAiChunk(aiContentDiv, data);
                    }
                }
            }
        }
    } catch (e) {
        aiContentDiv.innerHTML = `**System Error:** ${e.message}`;
    } finally {
        isSending = false;
        setSendingState(false);
        uploadedImages = [];
    }
}

function processAiChunk(div, data) {
    const { text, type } = data;
    
    if (type === 'ai') {
        // Render markdown for AI text
        div.innerHTML += marked.parse(text);
    } else if (type === 'action') {
        // Render action as a stylized block
        const actionDiv = document.createElement('div');
        actionDiv.className = 'text-sm font-mono text-gray-400 bg-gray-800/50 p-2 rounded border-l-4 border-purple-500 my-2';
        actionDiv.innerText = text;
        div.appendChild(actionDiv);
    } else if (type === 'info' || type === 'success' || type === 'warning' || type === 'error') {
        const infoDiv = document.createElement('div');
        infoDiv.className = `text-xs font-medium p-1 rounded ${
            type === 'success' ? 'text-green-400' : 
            type === 'error' ? 'text-red-400' : 
            type === 'warning' ? 'text-yellow-400' : 'text-cyan-400'
        }`;
        infoDiv.innerText = text;
        div.appendChild(infoDiv);
    } else if (type === 'code') {
        const codeDiv = document.createElement('div');
        codeDiv.className = 'text-xs text-gray-500 italic my-1';
        codeDiv.innerText = text.split('\n\n')[0]; // Just the header
        div.appendChild(codeDiv);
    } else if (type === 'status') {
        // Maybe a temporary spinner or status text
        const statusDiv = document.createElement('div');
        statusDiv.className = 'text-xs text-gray-500 italic animate-pulse';
        statusDiv.innerText = text;
        div.appendChild(statusDiv);
        // Remove it after some time or replace it
        setTimeout(() => statusDiv.remove(), 3000);
    }
    
    document.getElementById('chat-container').scrollTop = document.getElementById('chat-container').scrollHeight;
}

function setSendingState(sending) {
    const btn = document.getElementById('send-btn');
    const icon = document.getElementById('send-icon');
    
    if (sending) {
        btn.classList.remove('accent-bg');
        btn.classList.add('bg-red-500');
        icon.className = 'fa-solid fa-square';
    } else {
        btn.classList.add('accent-bg');
        btn.classList.remove('bg-red-500');
        icon.className = 'fa-solid fa-paper-plane';
    }
}

function startSpeech() {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'en-US';
    recognition.start();
    
    recognition.onresult = (event) => {
        const text = event.results[0][0].transcript;
        document.getElementById('user-input').value = text;
        document.getElementById('user-input').dispatchEvent(new Event('input'));
    };
    
    recognition.onerror = (event) => {
        console.error('Speech recognition error', event.error);
    };
}

init();
