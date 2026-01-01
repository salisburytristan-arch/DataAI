// ArcticCodex Studio - Enhanced Chat Frontend

class ChatApp {
    constructor() {
        this.convoId = `conv-${Date.now()}`;
        this.messages = [];
        this.isLoading = false;
        this.init();
    }
    
    async init() {
        this.setupEventListeners();
        await this.checkHealth();
        this.renderUI();
    }
    
    async checkHealth() {
        try {
            const res = await fetch('/api/health');
            const data = await res.json();
            console.log('Server healthy:', data);
        } catch (e) {
            console.error('Server unavailable:', e);
        }
    }
    
    setupEventListeners() {
        const sendBtn = document.getElementById('send-btn');
        const input = document.getElementById('message-input');
        
        sendBtn?.addEventListener('click', () => this.sendMessage());
        input?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey && !this.isLoading) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    }
    
    async sendMessage() {
        const input = document.getElementById('message-input');
        const msg = input.value.trim();
        
        if (!msg || this.isLoading) return;
        
        this.isLoading = true;
        
        // Add user message
        this.addMessage({
            role: 'user',
            content: msg,
            timestamp: new Date().toISOString()
        });
        
        input.value = '';
        
        try {
            // Stream response
            const response = await fetch('/api/chat/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: msg,
                    convo_id: this.convoId
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullText = '';
            let citations = [];
            
            const container = document.getElementById('chat-messages');
            const msgDiv = document.createElement('div');
            msgDiv.className = 'message assistant-message';
            container.appendChild(msgDiv);
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            msgDiv.appendChild(contentDiv);
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value);
                const lines = chunk.split('\n').filter(l => l);
                
                for (const line of lines) {
                    try {
                        const event = JSON.parse(line);
                        if (event.type === 'delta') {
                            fullText += event.token + ' ';
                            contentDiv.textContent = fullText;
                        } else if (event.type === 'done') {
                            citations = event.citations || [];
                        }
                    } catch (e) {
                        console.error('Parse error:', e);
                    }
                }
            }
            
            // Add citations if any
            if (citations.length > 0) {
                const citDiv = document.createElement('div');
                citDiv.className = 'citations';
                citations.forEach(cit => {
                    const link = document.createElement('a');
                    link.href = '#';
                    link.textContent = `[${cit.title}]`;
                    link.onclick = (e) => {
                        e.preventDefault();
                        this.showCitation(cit);
                    };
                    citDiv.appendChild(link);
                });
                msgDiv.appendChild(citDiv);
            }
            
            // Scroll to bottom
            container.scrollTop = container.scrollHeight;
            
        } catch (error) {
            this.addMessage({
                role: 'assistant',
                content: `Error: ${error.message}`,
                timestamp: new Date().toISOString()
            });
        } finally {
            this.isLoading = false;
        }
    }
    
    addMessage(msg) {
        this.messages.push(msg);
        const container = document.getElementById('chat-messages');
        const div = document.createElement('div');
        div.className = `message ${msg.role}-message`;
        div.innerHTML = `<div class="message-content">${this.escape(msg.content)}</div>`;
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    }
    
    showCitation(cit) {
        alert(`${cit.title}\n\n${cit.text.substring(0, 500)}...`);
    }
    
    escape(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    renderUI() {
        document.body.innerHTML = `
        <div class="studio-container">
            <header class="header">
                <h1>⧈ ArcticCodex Conversational</h1>
                <span class="convo-id">Session: ${this.convoId.substring(0, 12)}...</span>
            </header>
            <div class="chat-wrapper">
                <div id="chat-messages" class="chat-messages"></div>
                <div class="input-area">
                    <textarea id="message-input" placeholder="Ask anything..." rows="3"></textarea>
                    <button id="send-btn">Send (Ctrl+Enter)</button>
                </div>
            </div>
        </div>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; }
            .studio-container { display: flex; flex-direction: column; height: 100vh; }
            header { background: #1a1a1a; color: white; padding: 1rem; display: flex; justify-content: space-between; align-items: center; }
            header h1 { font-size: 1.5rem; }
            .convo-id { font-size: 0.9rem; opacity: 0.7; }
            .chat-wrapper { display: flex; flex-direction: column; flex: 1; }
            .chat-messages { flex: 1; overflow-y: auto; padding: 1rem; display: flex; flex-direction: column; gap: 1rem; }
            .message { padding: 1rem; border-radius: 8px; max-width: 80%; }
            .user-message { background: #0066cc; color: white; align-self: flex-end; }
            .assistant-message { background: #e0e0e0; color: #333; align-self: flex-start; }
            .citations { margin-top: 0.5rem; font-size: 0.9rem; }
            .citations a { color: #0066cc; margin-right: 0.5rem; text-decoration: none; }
            .input-area { padding: 1rem; border-top: 1px solid #ddd; display: flex; gap: 0.5rem; }
            textarea { flex: 1; padding: 0.75rem; border: 1px solid #ddd; border-radius: 4px; font-family: inherit; }
            button { padding: 0.75rem 1.5rem; background: #0066cc; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
            button:hover { background: #0052a3; }
        </style>
        `;
        this.setupEventListeners();
    }
}

// Initialize on load
window.addEventListener('load', () => new ChatApp());
