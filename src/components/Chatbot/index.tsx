import React, { useState, useRef, useEffect } from 'react';
import styles from './styles.module.css';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: Array<{
    title: string;
    module: string;
    path: string;
    score: number;
  }>;
}

const Chatbot: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Hi! I\'m your AI assistant for the Physical AI & Humanoid Robotics textbook. Ask me anything about ROS 2, simulation, NVIDIA Isaac, or VLA models!'
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isEmbedded, setIsEmbedded] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Check if documents are embedded on mount
  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      const response = await fetch(`${API_URL}/health`);
      const data = await response.json();
      setIsEmbedded(data.documents_embedded);
    } catch (error) {
      console.error('Health check failed:', error);
    }
  };

  const embedDocuments = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_URL}/embed`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to embed documents');
      }

      const data = await response.json();
      setIsEmbedded(true);

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `✓ Successfully embedded ${data.num_chunks} chunks from the textbook. You can now ask me questions!`
      }]);
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error embedding documents: ${error.message}. Please make sure the backend is running.`
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');

    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: userMessage,
          top_k: 5
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data = await response.json();

      // Add assistant message with sources
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.answer,
        sources: data.sources
      }]);
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${error.message}. Please make sure the backend is running at ${API_URL}`
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <>
      {/* Chat Button */}
      <button
        className={styles.chatButton}
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Toggle chat"
      >
        {isOpen ? '✕' : '💬'}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className={styles.chatWindow}>
          {/* Header */}
          <div className={styles.chatHeader}>
            <h3>🤖 AI Assistant</h3>
            <button
              className={styles.closeButton}
              onClick={() => setIsOpen(false)}
              aria-label="Close chat"
            >
              ✕
            </button>
          </div>

          {/* Messages */}
          <div className={styles.chatMessages}>
            {!isEmbedded && (
              <div className={styles.embedPrompt}>
                <p>📚 First time? Click below to load the textbook into memory:</p>
                <button
                  className={styles.embedButton}
                  onClick={embedDocuments}
                  disabled={isLoading}
                >
                  {isLoading ? 'Loading...' : 'Load Textbook'}
                </button>
              </div>
            )}

            {messages.map((message, index) => (
              <div
                key={index}
                className={`${styles.message} ${
                  message.role === 'user' ? styles.userMessage : styles.assistantMessage
                }`}
              >
                <div className={styles.messageContent}>
                  {message.content}
                </div>

                {/* Show sources for assistant messages */}
                {message.role === 'assistant' && message.sources && message.sources.length > 0 && (
                  <div className={styles.sources}>
                    <details>
                      <summary>📖 Sources ({message.sources.length})</summary>
                      <ul>
                        {message.sources.map((source, idx) => (
                          <li key={idx}>
                            <strong>{source.title}</strong>
                            <br />
                            <small>{source.module} • Score: {source.score.toFixed(3)}</small>
                          </li>
                        ))}
                      </ul>
                    </details>
                  </div>
                )}
              </div>
            ))}

            {isLoading && (
              <div className={`${styles.message} ${styles.assistantMessage}`}>
                <div className={styles.messageContent}>
                  <div className={styles.typing}>
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className={styles.chatInput}>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={isEmbedded ? "Ask about ROS 2, simulation, Isaac, VLA..." : "Load textbook first..."}
              disabled={!isEmbedded || isLoading}
              rows={1}
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isLoading || !isEmbedded}
              aria-label="Send message"
            >
              ➤
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default Chatbot;
