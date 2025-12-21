// ArcticCodex Studio - Frontend Application

class StudioApp {
    constructor() {
        this.apiBase = '';
        this.convoId = null;
        this.currentTab = 'documents';
        this.messages = [];
        this.vault = {
            documents: [],
            facts: [],
            memory: []
        };
        
        this.init();
    }
    
    async init() {
        // Get server info
        await this.checkServerStatus();
        this.setupEventListeners();
        await this.loadVaultData();
        this.renderWelcome();
    }
    
    async checkServerStatus() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            this.convoId = data.conversation_id || 'session-' + Date.now();
            this.updateServerStatus(true);
        } catch (error) {
            console.error('Server not available:', error);
            this.updateServerStatus(false);
        }
    }
    
    updateServerStatus(online) {
        const status = document.querySelector('.server-status');
        if (online) {
            status.classList.remove('disconnected');
            status.textContent = 'Server Connected';
        } else {
            status.classList.add('disconnected');
            status.textContent = 'Server Disconnected';
        }
    }
    
    setupEventListeners() {
        // Tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });
        
        // Chat
        document.getElementById('send-btn').addEventListener('click', () => this.sendMessage());
        document.getElementById('message-input').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Search
        document.getElementById('search-btn').addEventListener('click', () => this.performSearch());
        document.getElementById('search-input').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.performSearch();
            }
        });
        
        // Vault explorer search
        document.getElementById('vault-search').addEventListener('input', (e) => {
            this.filterVaultItems(e.target.value);
        });
        
        // Modals
        document.querySelectorAll('.close-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.target.closest('.modal').classList.add('hidden');
            });
        });
        
        // Close modal on background click
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.add('hidden');
                }
            });
        });
    }
    
    async loadVaultData() {
        try {
            // Load documents
            const docsRes = await fetch('/api/vault/docs');
            this.vault.documents = await docsRes.json();
            
            // Load facts
            const factsRes = await fetch(`/api/vault/facts?convo_id=${this.convoId}`);
            this.vault.facts = await factsRes.json();
            
            // Load memory queue
            const memRes = await fetch('/api/memory');
            this.vault.memory = await memRes.json();
            
            this.renderVault();
        } catch (error) {
            console.error('Failed to load vault data:', error);
        }
    }
    
    switchTab(tab) {
        this.currentTab = tab;
        
        // Update buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tab);
        });
        
        // Update tabs
        document.querySelectorAll('.explorer-tab').forEach(el => {
            el.classList.toggle('active', el.dataset.tab === tab);
        });
    }
    
    renderVault() {
        // Documents
        const docList = document.getElementById('doc-list');
        if (this.vault.documents.length === 0) {
            docList.innerHTML = '<div class="empty-state">No documents loaded</div>';
        } else {
            docList.innerHTML = this.vault.documents.map(doc => `
                <div class="list-item document" onclick="app.showDocumentDetail('${doc.id}')">
                    <strong>${doc.title || doc.filename}</strong>
                    <div style="font-size: 12px; color: #5f6368;">
                        ${doc.chunk_count || 0} chunks · ${(doc.size || 0)} bytes
                    </div>
                </div>
            `).join('');
        }
        
        // Facts
        const factList = document.getElementById('fact-list');
        if (this.vault.facts.length === 0) {
            factList.innerHTML = '<div class="empty-state">No facts extracted yet</div>';
        } else {
            factList.innerHTML = this.vault.facts.map(fact => `
                <div class="list-item fact" onclick="app.showFactDetail('${fact.id}')">
                    <div><strong>${fact.subject}</strong> → ${fact.predicate}</div>
                    <div style="color: #5f6368;">${fact.object}</div>
                </div>
            `).join('');
        }
        
        // Memory queue
        const memList = document.getElementById('memory-list');
        if (this.vault.memory.length === 0) {
            memList.innerHTML = '<div class="empty-state">No pending approvals</div>';
        } else {
            memList.innerHTML = this.vault.memory.map(item => `
                <div class="list-item">
                    <div><strong>${item.subject}</strong> → ${item.predicate}</div>
                    <div style="font-size: 12px; color: #5f6368; margin-top: 4px;">
                        ${item.object}
                    </div>
                    <div style="margin-top: 8px; display: flex; gap: 8px;">
                        <button class="btn-secondary" style="flex: 1; padding: 4px; font-size: 12px;" 
                                onclick="app.approveFact('${item.id}')">Approve</button>
                        <button class="btn-secondary" style="flex: 1; padding: 4px; font-size: 12px; color: #ea4335;"
                                onclick="app.rejectFact('${item.id}')">Reject</button>
                    </div>
                </div>
            `).join('');
        }
    }
    
    filterVaultItems(query) {
        const items = document.querySelectorAll('.list-item');
        const lowerQuery = query.toLowerCase();
        
        items.forEach(item => {
            const text = item.textContent.toLowerCase();
            item.style.display = text.includes(lowerQuery) ? 'block' : 'none';
        });
    }
    
    renderWelcome() {
        const messagesDiv = document.getElementById('chat-messages');
        messagesDiv.innerHTML = `
            <div class="welcome-message">
                <h2>Welcome to ArcticCodex Studio</h2>
                <p>Start a conversation to begin exploring your knowledge base.</p>
                <p style="margin-top: 16px; font-size: 13px; color: #5f6368;">
                    Messages will be enriched with citations from your vault.
                </p>
            </div>
        `;
    }
    
    async sendMessage() {
        const input = document.getElementById('message-input');
        const message = input.value.trim();
        
        if (!message) return;
        
        input.value = '';
        
        // Add user message to chat
        await this.addMessageToChat(message, 'user');
        
        // Show loading state
        const messagesDiv = document.getElementById('chat-messages');
        const loadingEl = document.createElement('div');
        loadingEl.className = 'message assistant';
        loadingEl.textContent = 'Thinking...';
        messagesDiv.appendChild(loadingEl);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        
        try {
            // Send to server
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: message,
                    conversation_id: this.convoId
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Remove loading message
                loadingEl.remove();
                
                // Add assistant response
                await this.addMessageToChat(data.response, 'assistant', data.citations || []);
                
                // Update vault if new facts extracted
                if (data.new_facts) {
                    await this.loadVaultData();
                }
            } else {
                loadingEl.textContent = 'Error: ' + (data.error || 'Failed to get response');
            }
        } catch (error) {
            loadingEl.textContent = 'Error: Connection failed';
            console.error('Chat error:', error);
        }
    }
    
    async addMessageToChat(text, role, citations = []) {
        const messagesDiv = document.getElementById('chat-messages');
        
        // Remove welcome message on first real message
        const welcome = messagesDiv.querySelector('.welcome-message');
        if (welcome) welcome.remove();
        
        const msgEl = document.createElement('div');
        msgEl.className = `message ${role}`;
        msgEl.textContent = text;
        
        if (citations.length > 0) {
            const citDiv = document.createElement('div');
            citDiv.className = 'message-citations';
            citDiv.innerHTML = '<strong>Citations:</strong> ' + 
                citations.map((cite, i) => `
                    <span class="citation-link" onclick="app.showCitationDetail('${cite.id}')">
                        [${i + 1}] ${cite.title || 'Source'}
                    </span>
                `).join(' ');
            msgEl.appendChild(citDiv);
        }
        
        messagesDiv.appendChild(msgEl);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        
        // Store in messages array
        this.messages.push({ role, text, citations });
    }
    
    async performSearch() {
        const input = document.getElementById('search-input');
        const query = input.value.trim();
        
        if (!query) return;
        
        const resultsDiv = document.getElementById('search-results');
        resultsDiv.innerHTML = '<div style="color: #5f6368;">Searching...</div>';
        
        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query })
            });
            
            const data = await response.json();
            
            if (response.ok && data.results) {
                resultsDiv.innerHTML = data.results.map((result, i) => `
                    <div class="result-item">
                        <strong>${result.title || 'Result ' + (i + 1)}</strong>
                        <div style="margin-top: 4px;">${result.content.substring(0, 100)}...</div>
                        <div class="result-score">Relevance: ${(result.score * 100).toFixed(0)}%</div>
                    </div>
                `).join('');
            } else {
                resultsDiv.innerHTML = '<div style="color: #ea4335;">Search failed</div>';
            }
        } catch (error) {
            resultsDiv.innerHTML = '<div style="color: #ea4335;">Search error</div>';
            console.error('Search error:', error);
        }
    }
    
    showDocumentDetail(docId) {
        const doc = this.vault.documents.find(d => d.id === docId);
        if (!doc) return;
        
        const modal = document.getElementById('document-modal');
        const content = document.getElementById('document-detail');
        content.innerHTML = `
            <h3>${doc.title || doc.filename}</h3>
            <div style="margin-top: 16px; color: #5f6368;">
                <p><strong>Size:</strong> ${doc.size || 'Unknown'} bytes</p>
                <p><strong>Chunks:</strong> ${doc.chunk_count || 0}</p>
                <p><strong>ID:</strong> ${doc.id}</p>
                ${doc.metadata ? `<p><strong>Metadata:</strong> ${JSON.stringify(doc.metadata)}</p>` : ''}
            </div>
        `;
        modal.classList.remove('hidden');
    }
    
    showFactDetail(factId) {
        const fact = this.vault.facts.find(f => f.id === factId);
        if (!fact) return;
        
        const modal = document.getElementById('document-modal');
        const content = document.getElementById('document-detail');
        content.innerHTML = `
            <h3>Fact Detail</h3>
            <div style="margin-top: 16px; font-family: monospace; background-color: #f8f9fa; padding: 12px; border-radius: 8px;">
                <div><strong>Subject:</strong> ${fact.subject}</div>
                <div><strong>Predicate:</strong> ${fact.predicate}</div>
                <div><strong>Object:</strong> ${fact.object}</div>
            </div>
            <div style="margin-top: 16px; color: #5f6368;">
                <p><strong>ID:</strong> ${fact.id}</p>
                <p><strong>Confidence:</strong> ${(fact.confidence || 0.95).toFixed(2)}</p>
            </div>
        `;
        modal.classList.remove('hidden');
    }
    
    showCitationDetail(citationId) {
        const modal = document.getElementById('document-modal');
        const content = document.getElementById('document-detail');
        content.innerHTML = `
            <h3>Citation Source</h3>
            <div style="margin-top: 16px; color: #5f6368;">
                <p>Source ID: ${citationId}</p>
                <p>This citation was retrieved from your vault.</p>
            </div>
        `;
        modal.classList.remove('hidden');
    }
    
    async approveFact(factId) {
        try {
            const response = await fetch('/api/memory/approve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ fact_id: factId })
            });
            
            if (response.ok) {
                // Reload vault
                await this.loadVaultData();
            }
        } catch (error) {
            console.error('Approval error:', error);
        }
    }
    
    async rejectFact(factId) {
        try {
            const response = await fetch('/api/memory/reject', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ fact_id: factId })
            });
            
            if (response.ok) {
                // Reload vault
                await this.loadVaultData();
            }
        } catch (error) {
            console.error('Rejection error:', error);
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new StudioApp();
});
