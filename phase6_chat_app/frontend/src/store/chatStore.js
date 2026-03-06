import { create } from 'zustand';

const useChatStore = create((set, get) => ({
  // State
  messages: [],
  sessionId: null,
  isLoading: false,
  isTyping: false,
  error: null,
  
  // Actions
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),
  
  setSessionId: (sessionId) => set({ sessionId }),
  
  setLoading: (isLoading) => set({ isLoading }),
  
  setTyping: (isTyping) => set({ isTyping }),
  
  setError: (error) => set({ error }),
  
  clearMessages: () => set({ messages: [], sessionId: null, error: null }),
  
  // Send message to API
  sendMessage: async (content) => {
    const { sessionId, messages } = get();
    
    // Add user message
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    };
    
    set((state) => ({
      messages: [...state.messages, userMessage],
      isLoading: true,
      error: null
    }));
    
    try {
      // Call API
      const response = await fetch('/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: content,
          session_id: sessionId
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to get response');
      }
      
      const data = await response.json();
      
      // Update session ID if new
      if (data.session_id && data.session_id !== sessionId) {
        set({ sessionId: data.session_id });
      }
      
      // Add assistant message
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.message.content,
        timestamp: data.message.timestamp,
        citations: data.message.citations,
        sources: data.sources
      };
      
      set((state) => ({
        messages: [...state.messages, assistantMessage],
        isLoading: false
      }));
      
    } catch (error) {
      set({
        error: error.message,
        isLoading: false
      });
      
      // Add error message
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString(),
        isError: true
      };
      
      set((state) => ({
        messages: [...state.messages, errorMessage]
      }));
    }
  }
}));

export default useChatStore;
