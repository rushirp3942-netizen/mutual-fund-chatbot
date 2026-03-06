import React, { useState, useRef, useEffect } from 'react';
import { Phone, Video, MoreVertical, Paperclip, Image, Smile, Mic, Camera, Send } from 'lucide-react';
import useChatStore from '../store/chatStore';
import { format } from 'date-fns';

// Suggested queries
const SUGGESTIONS = [
  "What is the expense ratio of SBI ELSS?",
  "Compare HDFC Mid Cap and Nippon Small Cap",
  "What is the minimum SIP for Axis Small Cap?",
  "Tell me about the risk level of Tata Small Cap"
];

const ChatPage = () => {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);
  const { messages, isLoading, sendMessage, clearMessages } = useChatStore();

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Handle send message
  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return;
    
    const message = inputValue.trim();
    setInputValue('');
    await sendMessage(message);
  };

  // Handle key press
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Handle suggestion click
  const handleSuggestionClick = (suggestion) => {
    setInputValue(suggestion);
  };

  // Format time
  const formatTime = (timestamp) => {
    if (!timestamp) return '';
    try {
      return format(new Date(timestamp), 'HH:mm');
    } catch {
      return '';
    }
  };

  return (
    <div className="chat-page">
      {/* Header */}
      <header className="chat-header">
        <div className="chat-header-avatar">MF</div>
        <div className="chat-header-info">
          <div className="chat-header-name">Mutual Fund Assistant</div>
          <div className="chat-header-status">AI-powered • RAG-based</div>
        </div>
        <div className="chat-header-actions">
          <button title="Voice call">
            <Phone size={20} />
          </button>
          <button title="Video call">
            <Video size={20} />
          </button>
          <button title="More options">
            <MoreVertical size={20} />
          </button>
        </div>
      </header>

      {/* Messages */}
      <div className="messages-container">
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}>
            <h3>Welcome to Mutual Fund Chatbot</h3>
            <p>Ask me about expense ratios, risk levels, SIP amounts, and more!</p>
          </div>
        )}
        
        {messages.map((message, index) => (
          <div
            key={message.id || index}
            className={`message ${message.role}`}
          >
            <div className="message-content">
              <div className="message-header">
                {message.role === 'assistant' && (
                  <div className="message-avatar">AI</div>
                )}
                <span>{message.role === 'user' ? 'You' : 'Assistant'}</span>
                <span style={{ marginLeft: '8px', opacity: 0.6 }}>
                  {formatTime(message.timestamp)}
                </span>
              </div>
              <div className="message-text">{message.content}</div>
              
              {/* Sources */}
              {message.sources && message.sources.length > 0 && (
                <div className="message-sources">
                  {message.sources.map((source, idx) => (
                    <a
                      key={idx}
                      href={source.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="source-link"
                    >
                      [{idx + 1}] Source
                    </a>
                  ))}
                </div>
              )}
              
              {message.role === 'user' && (
                <div className="message-avatar" style={{ marginLeft: '8px', marginRight: 0 }}>You</div>
              )}
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="message assistant">
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Suggestions */}
      {messages.length === 0 && (
        <div className="suggestions">
          {SUGGESTIONS.map((suggestion, index) => (
            <button
              key={index}
              className="suggestion-chip"
              onClick={() => handleSuggestionClick(suggestion)}
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="input-container">
        <div className="input-wrapper">
          <div className="input-actions">
            <button title="Attach file">
              <Paperclip size={20} />
            </button>
            <button title="Send image">
              <Image size={20} />
            </button>
            <button title="Add emoji">
              <Smile size={20} />
            </button>
          </div>
          
          <input
            type="text"
            className="chat-input"
            placeholder="Ask about mutual funds..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isLoading}
          />
          
          <div className="input-actions">
            <button title="Voice message">
              <Mic size={20} />
            </button>
            <button title="Take photo">
              <Camera size={20} />
            </button>
          </div>
          
          <button
            className="send-button"
            onClick={handleSend}
            disabled={!inputValue.trim() || isLoading}
            title="Send message"
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
