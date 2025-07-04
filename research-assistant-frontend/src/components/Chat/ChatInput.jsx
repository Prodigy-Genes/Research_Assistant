import React, { useState } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';
import '../../styles/ChatInput.css'; 

const ChatInput = ({ onSendMessage, isLoading }) => {
  const [message, setMessage] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="chat-input-form">
      <div className="chat-input-container">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask a research question..."
          className="chat-input-textarea"
          rows="1"
          style={{ minHeight: '50px', maxHeight: '120px' }}
          disabled={isLoading}
        />
      </div>
      <motion.button
        type="submit"
        disabled={!message.trim() || isLoading}
        className="chat-submit-button"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        {isLoading ? (
          <Loader2 className="chat-loading-icon" />
        ) : (
          <Send className="chat-submit-icon" />
        )}
      </motion.button>
    </form>
  );
};

export default ChatInput;