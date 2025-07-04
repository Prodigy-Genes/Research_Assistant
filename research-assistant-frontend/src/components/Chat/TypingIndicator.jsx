import React from 'react';
import { motion } from 'framer-motion';
import { Bot } from 'lucide-react';
import '../../styles/TypingIndicator.css'; 

const TypingIndicator = () => {
  return (
    <div className="typing-indicator-container">
      <div className="typing-indicator-avatar">
        <Bot className="typing-indicator-avatar-icon" />
      </div>
      <div className="typing-indicator-content">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="typing-indicator-bubble"
        >
          <div className="typing-indicator-content-wrapper">
            <div className="typing-indicator-dots">
              {[0, 1, 2].map((i) => (
                <motion.div
                  key={i}
                  className="typing-indicator-dot"
                  animate={{ y: [0, -8, 0] }}
                  transition={{
                    duration: 0.6,
                    repeat: Infinity,
                    delay: i * 0.2
                  }}
                />
              ))}
            </div>
            <span className="typing-indicator-text">Thinking...</span>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default TypingIndicator;