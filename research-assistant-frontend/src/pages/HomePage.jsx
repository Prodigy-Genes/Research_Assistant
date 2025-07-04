import React from 'react';
import { Link } from 'react-router-dom';
import { Search, FileText, Brain, MessageCircle, ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';
import '../styles/HomePage.css'; 

const HomePage = () => {
  const features = [
    {
      icon: <Search className="feature-icon" />,
      title: "Web Search",
      description: "Find up-to-date information from across the web with intelligent search capabilities",
    },
    {
      icon: <FileText className="feature-icon" />,
      title: "PDF Analysis",
      description: "Summarize and extract insights from PDF documents with advanced AI processing",
    },
    {
      icon: <Brain className="feature-icon" />,
      title: "Memory Recall",
      description: "Remembers previous conversations for context and personalized responses",
    },
  ];

  const examples = [
    "What are the latest developments in AI?",
    "Summarize this PDF: [PDF_URL]",
    "What did we discuss about Python earlier?",
    "Find recent news about climate change",
  ];

  return (
    <div className="home-page">
      {/* Hero Section */}
      <motion.section
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="hero-section"
      >
        <div className="hero-content">
          <motion.div
            initial={{ scale: 0.8 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.3, duration: 0.5 }}
            className="hero-title-wrapper"
          >
            <div className="hero-icon-bg">
              <Search className="hero-icon" />
            </div>
            <h1 className="hero-title">Research Assistant</h1>
          </motion.div>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5, duration: 0.5 }}
            className="hero-subtitle"
          >
            AI‑powered research assistant that finds answers with citations,
            analyzes documents, and remembers your conversations for intelligent,
            context‑aware responses.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7, duration: 0.5 }}
          >
            <Link to="/chat" className="hero-cta">
              <MessageCircle className="cta-icon" />
              <span>Start Chatting</span>
              <ArrowRight className="cta-icon-small" />
            </Link>
          </motion.div>
        </div>
      </motion.section>

      {/* Features Section */}
      <section className="features-section">
        <div className="features-grid">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 50 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.2, duration: 0.6 }}
              whileHover={{ y: -10 }}
              className="feature-card"
            >
              <div className="feature-icon-wrapper">{feature.icon}</div>
              <h3 className="feature-title">{feature.title}</h3>
              <p className="feature-desc">{feature.description}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Examples Section */}
      <section className="examples-section">
        <div className="examples-container">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="examples-glass"
          >
            <h3 className="examples-title">Try asking:</h3>
            <div className="examples-grid">
              {examples.map((example, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1, duration: 0.5 }}
                  whileHover={{ scale: 1.02 }}
                  className="example-card"
                  onClick={() => (window.location.href = '/chat')}
                >
                  <p className="example-text">"{example}"</p>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="home-footer">
        <p className="footer-text">
          Powered by LangGraph, LangChain, OpenAI and Brave Search
          <br />
          All rights reserved © {new Date().getFullYear()} Research Assistant -- prodigygenes
        </p>
      </footer>
    </div>
  );
};

export default HomePage;
