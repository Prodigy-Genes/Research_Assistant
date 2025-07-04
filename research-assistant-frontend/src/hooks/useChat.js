import { useState, useCallback } from 'react';
import { askQuestion } from '../services/api';

export const useChat = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'assistant',
      content: 'Hello! I\'m your research assistant. Ask me anything!',
      timestamp: new Date().toLocaleTimeString(),
      citations: []
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const addMessage = useCallback((message) => {
    const newMessage = {
      id: Date.now(),
      timestamp: new Date().toLocaleTimeString(),
      ...message
    };
    setMessages(prev => [...prev, newMessage]);
  }, []);

  const sendMessage = useCallback(async (content) => {
    setError(null);
    setIsLoading(true);

    // Add user message
    addMessage({
      type: 'user',
      content,
      citations: []
    });

    try {
      const response = await askQuestion(content);
      
      // Add assistant response
      addMessage({
        type: 'assistant',
        content: response.answer,
        citations: response.citations || []
      });
    } catch (err) {
      setError(err.message);
      addMessage({
        type: 'assistant',
        content: `Error: ${err.message}`,
        citations: []
      });
    } finally {
      setIsLoading(false);
    }
  }, [addMessage]);

  const clearChat = useCallback(() => {
    setMessages([
      {
        id: 1,
        type: 'assistant',
        content: 'Hello! I\'m your research assistant. Ask me anything!',
        timestamp: new Date().toLocaleTimeString(),
        citations: []
      }
    ]);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearChat
  };
};