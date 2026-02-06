import React, { useState, useEffect, useRef } from 'react';
import { apiService } from './services/api';
import type { ChatMessage, SkillInfo, SessionInfo } from './types';
import './styles/global.css';
import './styles/App.css';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const EXAMPLE_QUERIES = [
  "提供给我Azure CLI命令来创建一个具有托管身份的Azure container app, search Microsoft Learn",
  "Is gpt-5.2 available in westeurope regions? fetch full doc",
  "搜索详细的，可运行的使用azure ai foundry评估SDK进行危害评估的python示例代码",
  "我需要理解Azure Function端到端, search Microsoft Learn and deep dive",
  "给我一个完整的分步教程，部署python应用程序到Azure Function服务, search Microsoft Learn and deep dive"
];

interface ThinkingMessage {
  type: 'thinking';
  content: string;
  timestamp: string;
}

interface MessageWithThinking extends ChatMessage {
  thinking?: ThinkingMessage[];
  thinkingCollapsed?: boolean;
}

function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [messages, setMessages] = useState<MessageWithThinking[]>([]);
  const [currentThinking, setCurrentThinking] = useState<ThinkingMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [skills, setSkills] = useState<SkillInfo[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string>('');
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [activeView, setActiveView] = useState<'chat' | 'skills'>('chat');
  const [sessionCounter, setSessionCounter] = useState(1);
  const [autoScroll, setAutoScroll] = useState(true);
  const [sessionMessages, setSessionMessages] = useState<Map<string, MessageWithThinking[]>>(new Map());
  const chatContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadSkills();
    // 只在初始化时创建一个session
    if (sessions.length === 0) {
      createInitialSession();
    }
  }, []);

  useEffect(() => {
    if (chatContainerRef.current && autoScroll) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages, currentThinking, autoScroll]);

  // 监听用户滚动
  useEffect(() => {
    const container = chatContainerRef.current;
    if (!container) return;

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = container;
      const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
      setAutoScroll(isNearBottom);
    };

    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, []);

  const toggleThinking = (messageIndex: number) => {
    setMessages(prev => prev.map((msg, idx) => 
      idx === messageIndex 
        ? { ...msg, thinkingCollapsed: !msg.thinkingCollapsed }
        : msg
    ));
  };

  const loadSkills = async () => {
    try {
      const skillsList = await apiService.listSkills();
      setSkills(skillsList);
    } catch (error) {
      console.error('Failed to load skills:', error);
    }
  };

  const createInitialSession = async () => {
    try {
      const result = await apiService.createThread();
      const newSession: SessionInfo = {
        id: result.thread_id,
        name: 'Session 1',
        created_at: new Date().toISOString(),
        message_count: 0
      };
      setCurrentSessionId(result.thread_id);
      setSessions([newSession]);
      setSessionCounter(2);
      setMessages([]);
      setCurrentThinking([]);
    } catch (error) {
      console.error('Failed to create initial session:', error);
    }
  };

  const createNewSession = async () => {
    try {
      // 保存当前session的消息
      if (currentSessionId && messages.length > 0) {
        setSessionMessages(prev => new Map(prev).set(currentSessionId, messages));
      }

      const result = await apiService.createThread();
      const newSession: SessionInfo = {
        id: result.thread_id,
        name: `Session ${sessionCounter}`,
        created_at: new Date().toISOString(),
        message_count: 0
      };
      setCurrentSessionId(result.thread_id);
      setSessions(prev => [...prev, newSession]);
      setSessionCounter(prev => prev + 1);
      setMessages([]);
      setCurrentThinking([]);
      setActiveView('chat');
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  const switchSession = (sessionId: string) => {
    // 保存当前session的消息
    if (currentSessionId && messages.length > 0) {
      setSessionMessages(prev => new Map(prev).set(currentSessionId, messages));
    }

    // 加载目标session的消息
    const savedMessages = sessionMessages.get(sessionId) || [];
    setCurrentSessionId(sessionId);
    setMessages(savedMessages);
    setCurrentThinking([]);
    setActiveView('chat');
  };

  const deleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    
    // 如果只剩一个session，不允许删除
    if (sessions.length === 1) {
      alert('至少需要保留一个会话');
      return;
    }

    try {
      // 删除session的消息记录
      setSessionMessages(prev => {
        const newMap = new Map(prev);
        newMap.delete(sessionId);
        return newMap;
      });

      setSessions(prev => prev.filter(s => s.id !== sessionId));
      
      // 如果删除的是当前session，切换到第一个session
      if (currentSessionId === sessionId) {
        const remainingSessions = sessions.filter(s => s.id !== sessionId);
        if (remainingSessions.length > 0) {
          switchSession(remainingSessions[0].id);
        }
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  const sendMessageStream = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: MessageWithThinking = {
      role: 'user',
      content: inputValue,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = inputValue;
    setInputValue('');
    setIsLoading(true);
    setCurrentThinking([]);
    setAutoScroll(true); // 开始新消息时启用自动滚动

    // 先创建一个空的assistant消息框架，thinking在前面
    const initialAssistantMessage: MessageWithThinking = {
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      thinking: [],
      thinkingCollapsed: false
    };
    setMessages(prev => [...prev, initialAssistantMessage]);

    try {
      const response = await fetch('http://localhost:8000/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: currentInput,
          thread_id: currentSessionId
        })
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let assistantContent = '';
      let thinkingForMessage: ThinkingMessage[] = [];

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.substring(6));
                
                if (data.type === 'thinking') {
                  // Add thinking message
                  const thinking: ThinkingMessage = {
                    type: 'thinking',
                    content: data.message,
                    timestamp: new Date().toISOString()
                  };
                  thinkingForMessage.push(thinking);
                  
                  // 更新最后一条消息的thinking
                  setMessages(prev => {
                    const newMessages = [...prev];
                    const lastMessage = newMessages[newMessages.length - 1];
                    if (lastMessage && lastMessage.role === 'assistant') {
                      lastMessage.thinking = [...thinkingForMessage];
                    }
                    return newMessages;
                  });
                } else if (data.type === 'text') {
                  // Append text content
                  assistantContent += data.content;
                  setMessages(prev => {
                    const newMessages = [...prev];
                    const lastMessage = newMessages[newMessages.length - 1];
                    if (lastMessage && lastMessage.role === 'assistant') {
                      lastMessage.content = assistantContent;
                      lastMessage.thinking = thinkingForMessage;
                    }
                    return newMessages;
                  });
                } else if (data.type === 'done') {
                  // Auto-collapse thinking after 2 seconds
                  setTimeout(() => {
                    setMessages(prev => {
                      const newMessages = [...prev];
                      const lastMsg = newMessages[newMessages.length - 1];
                      if (lastMsg && lastMsg.role === 'assistant') {
                        lastMsg.thinkingCollapsed = true;
                      }
                      return newMessages;
                    });
                  }, 2000);
                } else if (data.type === 'error') {
                  throw new Error(data.message);
                }
              } catch (e) {
                console.error('Error parsing SSE data:', e);
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      setMessages(prev => {
        const newMessages = [...prev];
        const lastMsg = newMessages[newMessages.length - 1];
        if (lastMsg && lastMsg.role === 'assistant' && lastMsg.content === '') {
          lastMsg.content = 'Sorry, an error occurred while processing your request.';
        }
        return newMessages;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleExampleQuery = (query: string) => {
    setInputValue(query);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessageStream();
    }
  };

  return (
    <div className="app">
      {/* Sidebar */}
      <div className={`sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
        <div className="sidebar-header">
          <h1 className="sidebar-title gradient-text">Azure Doc Agent</h1>
          <button
            className="toggle-btn"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          >
            {sidebarCollapsed ? '→' : '←'}
          </button>
        </div>

        <div className="sidebar-content">
          {/* Function Buttons Section */}
          <div className="nav-section">
            <div className="nav-section-title">Functions</div>
            <button className="nav-item" onClick={createNewSession}>
              <span className="nav-icon">➕</span>
              <span className="nav-text">New Session</span>
            </button>
            <button
              className={`nav-item ${activeView === 'skills' ? 'active' : ''}`}
              onClick={() => setActiveView('skills')}
            >
              <span className="nav-icon">⚡</span>
              <span className="nav-text">Skills</span>
            </button>
          </div>

          {/* Current Chat Section */}
          <div className="nav-section">
            <div className="nav-section-title">Active Session</div>
            {!sidebarCollapsed && sessions.map((session) => (
              <button
                key={session.id}
                className={`nav-item ${session.id === currentSessionId ? 'active' : ''}`}
                onClick={() => switchSession(session.id)}
                style={{
                  fontSize: '13px',
                  padding: '10px 12px',
                  marginBottom: '4px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1 }}>
                  <span className="nav-icon">💬</span>
                  <span className="nav-text" style={{ fontSize: '13px' }}>
                    {session.name}
                  </span>
                </div>
                <span
                  className="delete-session-btn"
                  onClick={(e) => deleteSession(session.id, e)}
                  style={{
                    fontSize: '16px',
                    opacity: 0.6,
                    cursor: 'pointer',
                    padding: '0 4px',
                    transition: 'opacity 0.2s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
                  onMouseLeave={(e) => e.currentTarget.style.opacity = '0.6'}
                  title="删除会话"
                >
                  🗑️
                </span>
              </button>
            ))}
          </div>

          {!sidebarCollapsed && (
            <div className="nav-section">
              <div className="nav-section-title">示例问题</div>
              {EXAMPLE_QUERIES.map((query, idx) => (
                <button
                  key={idx}
                  className="nav-item example-query"
                  onClick={() => handleExampleQuery(query)}
                  style={{
                    fontSize: '11px',
                    padding: '8px 10px',
                    whiteSpace: 'normal',
                    textAlign: 'left',
                    lineHeight: '1.4',
                    wordWrap: 'break-word',
                    overflowWrap: 'break-word',
                    height: 'auto',
                    minHeight: '35px',
                    display: 'flex',
                    gap: '6px',
                    alignItems: 'flex-start'
                  }}
                >
                  <span style={{ flexShrink: 0, fontSize: '14px' }}>💡</span>
                  <span style={{ fontSize: '11px', flex: 1, wordBreak: 'break-word' }}>
                    {query}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content">
        <div className="chat-header">
          <div className="chat-title">
            {activeView === 'chat' && `Session: ${currentSessionId.substring(0, 20)}...`}
            {activeView === 'skills' && 'Agent Skills'}
          </div>
        </div>

        {activeView === 'chat' && (
          <>
            <div className="chat-container" ref={chatContainerRef}>
              {messages.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-state-icon">🤖</div>
                  <h2 className="empty-state-title">Welcome to Azure Doc Agent</h2>
                  <p className="empty-state-desc">
                    Ask me anything about Microsoft documentation, Azure services, or code examples.
                    <br />
                    Try one of the example queries from the sidebar to get started!
                  </p>
                </div>
              ) : (
                <>
                  {messages.map((msg, idx) => (
                    <div key={idx}>
                      {/* User message */}
                      {msg.role === 'user' && (
                        <div className="message user">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {msg.content}
                          </ReactMarkdown>
                          <span className="message-timestamp">
                            {new Date(msg.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                      )}
                      
                      {/* Assistant message with thinking */}
                      {msg.role === 'assistant' && (
                        <>
                          {/* Thinking section - always present, collapsible */}
                          {msg.thinking && msg.thinking.length > 0 && (
                            <div className="thinking-container">
                              <button 
                                className="thinking-toggle"
                                onClick={() => toggleThinking(idx)}
                              >
                                <span className="thinking-icon">
                                  {msg.thinkingCollapsed ? '▶' : '▼'}
                                </span>
                                <span className="thinking-title">
                                  思考过程 ({msg.thinking.length} steps)
                                </span>
                              </button>
                              {!msg.thinkingCollapsed && (
                                <div className="thinking-content">
                                  {msg.thinking.map((thinking, tIdx) => (
                                    <div key={tIdx} className="thinking-step">
                                      {thinking.content}
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}
                          
                          {/* Assistant response */}
                          <div className="message assistant">
                            <ReactMarkdown
                              remarkPlugins={[remarkGfm]}
                              components={{
                                a: ({ node, ...props }) => (
                                  <a {...props} target="_blank" rel="noopener noreferrer" />
                                )
                              }}
                            >
                              {msg.content}
                            </ReactMarkdown>
                            <span className="message-timestamp">
                              {new Date(msg.timestamp).toLocaleTimeString()}
                            </span>
                          </div>
                        </>
                      )}
                    </div>
                  ))}
                  
                  {/* Loading indicator under thinking */}
                  {isLoading && (
                    <div className="loading">
                      <div className="spinner"></div>
                    </div>
                  )}
                </>
              )}
            </div>

            <div className="input-container">
              <div className="input-wrapper">
                <textarea
                  className="chat-input"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask about Azure documentation, APIs, or get code examples..."
                  disabled={isLoading}
                />
                <button
                  className="send-btn"
                  onClick={sendMessageStream}
                  disabled={isLoading || !inputValue.trim()}
                >
                  {isLoading ? 'Sending...' : 'Send 🚀'}
                </button>
              </div>
            </div>
          </>
        )}

        {activeView === 'skills' && (
          <div className="chat-container">
            <div style={{ maxWidth: '800px', margin: '0 auto', width: '100%' }}>
              <h2 style={{ marginBottom: '24px' }}>Available Skills</h2>
              {skills.map((skill) => (
                <div key={skill.name} className="card" style={{ marginBottom: '16px' }}>
                  <h3 style={{ marginBottom: '8px', color: 'var(--accent-blue)' }}>
                    {skill.name}
                  </h3>
                  <p style={{ color: 'var(--text-secondary)', marginBottom: '12px' }}>
                    {skill.description}
                  </p>
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    {skill.tags.map((tag) => (
                      <span
                        key={tag}
                        style={{
                          padding: '4px 12px',
                          background: 'var(--bg-tertiary)',
                          borderRadius: '12px',
                          fontSize: '12px',
                          color: 'var(--text-secondary)'
                        }}
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
