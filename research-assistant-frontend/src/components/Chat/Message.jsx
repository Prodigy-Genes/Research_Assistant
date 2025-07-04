import React from 'react';
import { User, Bot, ExternalLink } from 'lucide-react';
import { motion } from 'framer-motion';
import '../../styles/Message.css'; 

const Message = ({ message }) => {
  const isUser = message.type === 'user';

  return (
    <div className={`message-container ${isUser ? 'user' : 'bot'}`}>
      {/* Avatar */}
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.2 }}
        className={`message-avatar ${isUser ? 'user' : 'bot'}`}
      >
        {isUser ? (
          <User className="message-avatar-icon" />
        ) : (
          <Bot className="message-avatar-icon" />
        )}
      </motion.div>

      {/* Message Content */}
      <div className={`message-content-wrapper ${isUser ? 'user' : 'bot'}`}>
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className={`message-bubble ${isUser ? 'user' : 'bot'}`}
        >
          <div className="message-text">{message.content}</div>
          
          {/* Citations */}
          {message.citations && message.citations.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className={`message-citations ${isUser ? 'user' : 'bot'}`}
            >
              <div className="message-citations-title">Sources:</div>
              <div className="message-citations-list">
                {message.citations.map((citation, index) => (
                  <motion.a
                    key={index}
                    href={citation.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`message-citation-link ${isUser ? 'user' : 'bot'}`}
                    whileHover={{ scale: 1.02 }}
                  >
                    <ExternalLink className="message-citation-icon" />
                    <span>{citation.id}. {citation.title}</span>
                  </motion.a>
                ))}
              </div>
            </motion.div>
          )}
        </motion.div>
        
        {/* Timestamp */}
        <div className={`message-timestamp ${isUser ? 'user' : 'bot'}`}>
          {message.timestamp}
        </div>
      </div>
    </div>
  );
};

export default Message;