/**
 * Chat Application JavaScript
 * Handles WebSocket communication and UI interactions
 */

// Global state
let socket = null;
let sessionId = null;
let isTyping = false;

// DOM Elements
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const messagesArea = document.getElementById('messages-area');
const typingIndicator = document.getElementById('typing-indicator');
const suggestions = document.getElementById('suggestions');
const connectionStatus = document.getElementById('connection-status');

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeSocket();
    setupEventListeners();
});

/**
 * Initialize WebSocket connection
 */
function initializeSocket() {
    // Connect to Flask-SocketIO server
    socket = io('http://localhost:3000');
    
    socket.on('connect', function() {
        console.log('Connected to server');
        updateConnectionStatus('Connected', 'connected');
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from server');
        updateConnectionStatus('Disconnected', 'disconnected');
    });
    
    socket.on('receive_message', function(data) {
        hideTypingIndicator();
        displayAssistantMessage(data);
    });
    
    socket.on('error', function(data) {
        hideTypingIndicator();
        displayErrorMessage(data.message);
    });
}

/**
 * Update connection status indicator
 */
function updateConnectionStatus(text, status) {
    if (connectionStatus) {
        connectionStatus.textContent = text;
        connectionStatus.className = 'chat-status ' + status;
    }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Send on Enter key
    if (messageInput) {
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        // Typing indicator
        messageInput.addEventListener('input', function() {
            if (!isTyping) {
                isTyping = true;
                socket.emit('typing', { typing: true });
                
                setTimeout(() => {
                    isTyping = false;
                    socket.emit('typing', { typing: false });
                }, 1000);
            }
        });
    }
}

/**
 * Send a message
 */
function sendMessage() {
    const message = messageInput.value.trim();
    
    if (!message) return;
    
    // Display user message
    displayUserMessage(message);
    
    // Clear input
    messageInput.value = '';
    
    // Hide suggestions after first message
    if (suggestions) {
        suggestions.style.display = 'none';
    }
    
    // Show typing indicator
    showTypingIndicator();
    
    // Send via WebSocket
    if (socket && socket.connected) {
        socket.emit('send_message', {
            message: message,
            session_id: sessionId
        });
    } else {
        // Fallback to HTTP API
        sendMessageHTTP(message);
    }
}

/**
 * Send message via HTTP API (fallback)
 */
async function sendMessageHTTP(message) {
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        });
        
        const data = await response.json();
        
        hideTypingIndicator();
        
        if (data.message) {
            sessionId = data.session_id;
            displayAssistantMessage(data);
        } else {
            displayErrorMessage('Failed to get response');
        }
        
    } catch (error) {
        hideTypingIndicator();
        displayErrorMessage('Network error: ' + error.message);
    }
}

/**
 * Send a suggestion as message
 */
function sendSuggestion(text) {
    messageInput.value = text;
    sendMessage();
}

/**
 * Display user message
 */
function displayUserMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user-message';
    
    const time = new Date().toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false 
    });
    
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-bubble">${escapeHtml(text)}</div>
            <span class="message-time">${time}</span>
        </div>
        <div class="message-avatar user-avatar">You</div>
    `;
    
    messagesArea.appendChild(messageDiv);
    scrollToBottom();
}

/**
 * Display assistant message
 */
function displayAssistantMessage(data) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant-message';
    
    const time = new Date().toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false 
    });
    
    let sourcesHtml = '';
    if (data.sources && data.sources.length > 0) {
        sourcesHtml = '<div style="margin-top: 8px; font-size: 0.8rem; opacity: 0.8;">Source: ';
        data.sources.forEach((source, index) => {
            const displayName = source.fund_name || `Source ${index + 1}`;
            sourcesHtml += `<a href="${source.source_url}" target="_blank" style="color: inherit; text-decoration: underline; font-weight: 500;">${displayName}</a>`;
        });
        sourcesHtml += '</div>';
    }
    
    messageDiv.innerHTML = `
        <div class="message-avatar assistant-avatar">AI</div>
        <div class="message-content">
            <div class="message-bubble">${formatMessage(data.message.content || data.message)}${sourcesHtml}</div>
            <span class="message-time">${time}</span>
        </div>
    `;
    
    messagesArea.appendChild(messageDiv);
    scrollToBottom();
}

/**
 * Display error message
 */
function displayErrorMessage(error) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant-message';
    
    messageDiv.innerHTML = `
        <div class="message-avatar assistant-avatar">!</div>
        <div class="message-content">
            <div class="message-bubble" style="background: #fee2e2; color: #dc2626; border-color: #fecaca;">
                Sorry, I encountered an error. Please try again.
            </div>
        </div>
    `;
    
    messagesArea.appendChild(messageDiv);
    scrollToBottom();
}

/**
 * Show typing indicator
 */
function showTypingIndicator() {
    if (typingIndicator) {
        typingIndicator.style.display = 'flex';
        scrollToBottom();
    }
}

/**
 * Hide typing indicator
 */
function hideTypingIndicator() {
    if (typingIndicator) {
        typingIndicator.style.display = 'none';
    }
}

/**
 * Scroll to bottom of messages
 */
function scrollToBottom() {
    if (messagesArea) {
        messagesArea.scrollTop = messagesArea.scrollHeight;
    }
}

/**
 * Clear chat history
 */
function clearChat() {
    if (confirm('Are you sure you want to clear the chat?')) {
        // Keep only welcome message
        const welcomeMessage = messagesArea.firstElementChild;
        messagesArea.innerHTML = '';
        messagesArea.appendChild(welcomeMessage);
        
        // Reset session
        sessionId = null;
        
        // Show suggestions again
        if (suggestions) {
            suggestions.style.display = 'flex';
        }
    }
}

/**
 * Format message text (convert newlines to <br>)
 */
function formatMessage(text) {
    return escapeHtml(text).replace(/\n/g, '<br>');
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Export functions for global access
window.sendMessage = sendMessage;
window.sendSuggestion = sendSuggestion;
window.clearChat = clearChat;
