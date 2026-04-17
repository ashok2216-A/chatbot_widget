import { useState, useRef, useEffect } from 'react'
import './index.css'

// Constants are now handled dynamically via props in the App component

export function AdaptiveView({ items, layout = 'grid', onCommand }) {
  return (
    <div className={`a2ui-adaptive-view ${layout}`}>
      {items.map((item, i) => (
        <div className="a2ui-card" key={i} style={{ animationDelay: `${i * 0.1}s` }}>
          {Object.entries(item).map(([key, value]) => {
            if (value === null || value === undefined) return null;
            
            const lowerKey = key.toLowerCase();
            
            // 1. Status Badges
            if (lowerKey === 'status' || lowerKey === 'state') {
              return (
                <div key={key} className={`a2ui-status-badge ${String(value).toLowerCase()}`}>
                  {String(value)}
                </div>
              );
            }

            // 2. Proficiency/Level Metrics
            const isLevel = lowerKey === 'level' || lowerKey === 'proficiency';
            if (isLevel) {
              const sanitize = (val) => {
                if (typeof val === 'number') return val;
                const num = parseInt(String(val).match(/\d+/)?.[0]);
                if (!isNaN(num)) return num;
                const map = { expert: 95, advanced: 85, intermediate: 70, beginner: 40, basic: 40 };
                return map[String(val).toLowerCase()] || 0;
              };
              const numericValue = sanitize(value);

              return (
                <div className="card-metric" key={key}>
                  <div className="metric-bar-track">
                    <div className="metric-bar-fill" style={{ '--target': `${numericValue}%` }} />
                  </div>
                  <span className="metric-val">{value}</span>
                </div>
              );
            }

            // 3. Selection Checkboxes (for multi-select tasks)
            if (typeof value === 'boolean' || lowerKey === 'selected') {
              return (
                <div className="card-row checkbox" key={key}>
                  <input type="checkbox" checked={!!value} readOnly />
                  <span className="row-key">{key}</span>
                </div>
              );
            }

            // Default Row
            return (
              <div className="card-row" key={key}>
                <span className="row-key">{key}</span>
                <span className="row-value">{String(value)}</span>
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
}

const COMPONENT_REGISTRY = {
  data_view: AdaptiveView,
};

export function A2UIRenderer({ data, onCommand }) {
  const componentKey = Object.keys(data).find(k => COMPONENT_REGISTRY[k]);
  
  if (!componentKey) {
    return <div className="cw-message bot">{JSON.stringify(data)}</div>;
  }

  const Component = COMPONENT_REGISTRY[componentKey];
  const content = data[componentKey];
  
  return (
    <div className="a2ui-wrapper">
      {content.text && <p className="a2ui-title">{content.text}</p>}
      
      <Component 
        items={content.items || []} 
        layout={content.layout || 'grid'} 
        onCommand={onCommand}
      />

      {/* 4. Action Buttons */}
      {content.actions && content.actions.length > 0 && (
        <div className="a2ui-actions">
          {content.actions.map((action, idx) => (
            <button 
              key={idx} 
              className={`a2ui-btn ${action.variant || 'primary'}`}
              onClick={() => onCommand(action.message)}
            >
              {action.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function formatText(text) {
  if (!text) return '';
  return text
    .replace(/\n/g, '<br />')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
}

function Message({ msg, onCommand }) {
  const isBot = msg.sender === 'bot';
  const chunks = msg.chunks || [{ type: 'text', content: msg.text }];

  return (
    <div className={`cw-message ${msg.sender}`}>
      {chunks.map((chunk, idx) => (
        <div key={idx} className="cw-msg-chunk">
          {chunk.type === 'a2ui' ? (
            <A2UIRenderer data={chunk.content} onCommand={onCommand} />
          ) : (
            <span dangerouslySetInnerHTML={{ __html: formatText(chunk.content) }} />
          )}
        </div>
      ))}
    </div>
  );
}

function TypingDots() {
  return (
    <div className="cw-message bot loading">
      <div className="cw-dot"></div>
      <div className="cw-dot"></div>
      <div className="cw-dot"></div>
    </div>
  )
}

// ─── Widget App ──────────────────────────────────────────────────────────────

// Persistence: Get or create a session ID that lasts until the tab is closed
const getSessionId = () => {
  let id = sessionStorage.getItem('chat_session_id');
  if (!id) {
    id = "sess_" + Math.random().toString(36).substring(2, 12);
    sessionStorage.setItem('chat_session_id', id);
  }
  return id;
};
const SESSION_ID = getSessionId();

export default function App({ config = {} }) {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  // Configuration with fallbacks
  const botName = config.botName || "Portfolio Assistant"
  const botLogo = config.botLogo || "./assets/img/my_logo.png"
  const welcomeMessage = config.welcomeMessage || "Hello! I'm your AI assistant. How can I help you today?"
  const apiUrl = config.apiUrl || (import.meta.env.VITE_BACKEND_URL ? `${import.meta.env.VITE_BACKEND_URL}/chat` : 'http://localhost:8000/chat')

  useEffect(() => {
    if (isOpen && messages.length === 0) {
      setMessages([{ sender: 'bot', text: welcomeMessage }])
    }
  }, [isOpen, welcomeMessage])

  useEffect(() => {
    // Small delay allows complex A2UI blocks (grids) to finish layout before scrolling
    const timer = setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
    return () => clearTimeout(timer);
  }, [messages, loading])

  const sendMessage = async () => {
    const text = input.trim()
    if (!text || loading) return

    setMessages(prev => [...prev, { sender: 'user', text }])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: SESSION_ID }),
      })
      
      if (res.status === 403) {
        setMessages(prev => [
          ...prev,
          { sender: 'bot', text: '🛑 **Access Denied**: This website origin is not authorized to use this chat assistant. Please check your CORS settings.' }
        ]);
        return;
      }
      
      const data = await res.json()
      setMessages(prev => [
        ...prev,
        { 
          sender: 'bot', 
          text: data.reply || "I'm having trouble right now.", 
          chunks: data.chunks || null
        },
      ])
    } catch {
      setMessages(prev => [
        ...prev, 
        { sender: 'bot', text: 'Oops! Servers seem down. Try again later.' }
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleCommand = (cmdText) => {
    if (!cmdText || loading) return;
    setInput(cmdText);
    setTimeout(() => {
      document.getElementById('cw-send')?.click();
    }, 10);
  };

  const handleKey = (e) => {
    if (e.key === 'Enter') { e.preventDefault(); sendMessage() }
  }

  return (
    <div id="cw-container" className={isOpen ? 'cw-open' : ''}>
      {/* Chat Window */}
      <div id="cw-window">
        <div id="cw-header">
          <div className="cw-header-title">
            <div className="cw-avatar">
              <img 
                src={botLogo} 
                alt="Bot Logo" 
                style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: 'inherit' }}
                onError={e => { 
                  e.target.src = "https://cdn-icons-png.flaticon.com/512/4712/4712027.png"; // Fallback to a nice AI icon
                }} 
              />
            </div>
            <div className="cw-info">
              <h3>{botName}</h3>
              <p>Online &amp; Ready</p>
            </div>
          </div>
          <button id="cw-close" onClick={() => setIsOpen(false)} aria-label="Close chat">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M13 1L1 13M1 1L13 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>

        <div id="cw-messages">
          {messages.map((m, i) => <Message key={i} msg={m} onCommand={handleCommand} />)}
          {loading && <TypingDots />}
          <div ref={messagesEndRef} />
        </div>

        <div id="cw-input-area">
          <div className="cw-input-wrapper">
            <input
              id="cw-input"
              type="text"
              placeholder="Type your message..."
              autoComplete="off"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              disabled={loading}
            />
            <button id="cw-send" onClick={sendMessage} disabled={loading} aria-label="Send message">
              <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
              </svg>
            </button>
          </div>
          <div className="cw-footer">⚡ Built by Ashok</div>
        </div>
      </div>

      {/* Toggle Button */}
      <button id="cw-toggle" onClick={() => setIsOpen(o => !o)} aria-label="Open chat">
        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
        </svg>
      </button>
    </div>
  )
}
