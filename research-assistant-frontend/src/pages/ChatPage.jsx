import React from 'react';
import { Link } from 'react-router-dom';
import { Search, Plus, ArrowLeft } from 'lucide-react';
import { motion } from 'framer-motion';
import { useChat } from '../hooks/useChat';
import ChatHistory from '../components/Chat/ChatHistory';
import ChatInput from '../components/Chat/ChatInput';
import TypingIndicator from '../components/Chat/TypingIndicator';
import '../styles/ChatPage.css';

const ChatPage = () => {
  const { messages, isLoading, error, sendMessage, clearChat } = useChat();

  return (
    <div className="chat-page">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="chat-header"
      >
        <div className="header-content">
          <div className="header-left">
            <Link to="/" className="back-button">
              <ArrowLeft className="w-5 h-5" />
              <span>Back</span>
            </Link>
            <div className="header-center">
              <Search className="search-icon" />
              <h1 className="page-title">Research Assistant</h1>
            </div>
          </div>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={clearChat}
            className="new-chat-button"
          >
            <Plus className="plus-icon" />
            <span>New Chat</span>
          </motion.button>
        </div>
      </motion.header>

      {/* Chat Container */}
      <div className="chat-container">
        <div className="chat-content">
          {/* Chat History */}
          <div className="chat-history-section">
            <ChatHistory messages={messages} />
            {isLoading && <TypingIndicator />}
          </div>

          {/* Chat Input */}
          <div className="chat-input-section">
            <ChatInput onSendMessage={sendMessage} isLoading={isLoading} />
            {error && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="error-message"
              >
                <p>{error}</p>
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
