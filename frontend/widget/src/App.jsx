import { useState, useRef, useEffect } from 'react'
import './index.css'
import { A2UIRenderer } from './a2ui/renderer'

/**
 * Lightweight Markdown → HTML renderer (zero dependencies).
 * Handles: headings, bold, italic, inline code, fenced code blocks,
 *          bullet lists, numbered lists, horizontal rules, links.
 */
function formatText(text) {
  if (!text) return '';

  const lines = text.split('\n');
  const output = [];
  let inUl = false;
  let inOl = false;
  let inCode = false;
  let codeLang = '';
  let codeLines = [];

  const closeList = () => {
    if (inUl) { output.push('</ul>'); inUl = false; }
    if (inOl) { output.push('</ol>'); inOl = false; }
  };

  const closeCode = () => {
    if (inCode) {
      const escaped = codeLines.join('\n')
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
      output.push(`<pre class="md-codeblock"><code class="lang-${codeLang}">${escaped}</code></pre>`);
      codeLines = [];
      codeLang = '';
      inCode = false;
    }
  };

  // Inline formatting (applied to non-code lines)
  const inline = (str) => str
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/`([^`]+)`/g, '<code class="md-code">$1</code>')
    .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/__(.+?)__/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/_(.+?)_/g, '<em>$1</em>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener" class="md-link">$1</a>');

  for (const raw of lines) {
    const line = raw;

    // ── Fenced code block toggle ──────────────────────────────────────
    if (/^```/.test(line)) {
      if (!inCode) {
        closeList();
        codeLang = line.replace(/^```/, '').trim() || 'text';
        inCode = true;
      } else {
        closeCode();
      }
      continue;
    }

    if (inCode) { codeLines.push(line); continue; }

    // ── Horizontal rule ───────────────────────────────────────────────
    if (/^---+$/.test(line.trim()) || /^\*\*\*+$/.test(line.trim())) {
      closeList();
      output.push('<hr class="md-hr" />');
      continue;
    }

    // ── ATX Headings (# ## ###) ───────────────────────────────────────
    const h = line.match(/^(#{1,6})\s+(.+)/);
    if (h) {
      closeList();
      const level = h[1].length;
      output.push(`<h${level} class="md-h${level}">${inline(h[2])}</h${level}>`);
      continue;
    }

    // ── Unordered list ────────────────────────────────────────────────
    const ul = line.match(/^[\s]*[-*+]\s+(.+)/);
    if (ul) {
      if (inOl) { output.push('</ol>'); inOl = false; }
      if (!inUl) { output.push('<ul class="md-ul">'); inUl = true; }
      output.push(`<li class="md-li">${inline(ul[1])}</li>`);
      continue;
    }

    // ── Ordered list ──────────────────────────────────────────────────
    const ol = line.match(/^[\s]*\d+[.)]\s+(.+)/);
    if (ol) {
      if (inUl) { output.push('</ul>'); inUl = false; }
      if (!inOl) { output.push('<ol class="md-ol">'); inOl = true; }
      output.push(`<li class="md-li">${inline(ol[1])}</li>`);
      continue;
    }

    // ── Blank line ────────────────────────────────────────────────────
    if (line.trim() === '') {
      closeList();
      output.push('<br />');
      continue;
    }

    // ── Normal paragraph line ─────────────────────────────────────────
    closeList();
    output.push(`<span class="md-line">${inline(line)}</span><br />`);
  }

  closeList();
  closeCode();

  return output.join('\n');
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

  // ── Theme: persisted in localStorage, default is dark ──────────────────
  const [theme, setTheme] = useState(() => localStorage.getItem('cw_theme') || 'dark')
  const toggleTheme = () => {
    setTheme(prev => {
      const next = prev === 'dark' ? 'light' : 'dark'
      localStorage.setItem('cw_theme', next)
      
      // Reset color customizations that conflict with standard theme switching
      setCustomBg('');         localStorage.removeItem('cw_bg')
      setCustomUserBubble(''); localStorage.removeItem('cw_usr_bubble')
      setCustomBotBubble('');  localStorage.removeItem('cw_bot_bubble')
      setCustomHeaderBg('');   localStorage.removeItem('cw_header_bg')
      setCustomHeaderText(''); localStorage.removeItem('cw_header_txt')
      
      return next
    })
  }

  // ── Helpers: Colour Contrast ──────────────────────────────────────────
  const getLuminance = (hex) => {
    if (!hex || hex.length < 6) return 0
    const rgb = hex.replace('#', '')
    const r = parseInt(rgb.slice(0, 2), 16)
    const g = parseInt(rgb.slice(2, 4), 16)
    const b = parseInt(rgb.slice(4, 6), 16)
    return (r * 299 + g * 587 + b * 114) / 1000
  }
  const isLightColor = (hex) => getLuminance(hex) > 165

  // ── Customizer: logo + colours ───────────────────────────────────────
  const [showCustomizer, setShowCustomizer] = useState(false)
  const [customLogo,      setCustomLogo]      = useState(() => localStorage.getItem('cw_logo')       || '')
  const [customAccent,    setCustomAccent]    = useState(() => localStorage.getItem('cw_accent')     || '')
  const [customBg,        setCustomBg]        = useState(() => localStorage.getItem('cw_bg')         || '')
  const [customUserBubble,setCustomUserBubble]= useState(() => localStorage.getItem('cw_usr_bubble') || '')
  const [customBotBubble, setCustomBotBubble] = useState(() => localStorage.getItem('cw_bot_bubble') || '')
  const [customHeaderBg,   setCustomHeaderBg]   = useState(() => localStorage.getItem('cw_header_bg')  || '')
  const [customHeaderText, setCustomHeaderText] = useState(() => localStorage.getItem('cw_header_txt') || '')
  const [customBotName,    setCustomBotName]    = useState(() => localStorage.getItem('cw_bot_name') || '')
  const [logoInput,       setLogoInput]       = useState(customLogo.startsWith('data:') ? '' : customLogo)

  const ACCENT_PRESETS = [
    { label: 'Purple', value: '#7C6AF7' },
    { label: 'Blue',   value: '#3B82F6' },
    { label: 'Teal',   value: '#06B6D4' },
    { label: 'Green',  value: '#10B981' },
    { label: 'Orange', value: '#F59E0B' },
    { label: 'Pink',   value: '#EC4899' },
    { label: 'Red',    value: '#EF4444' },
    { label: 'Indigo', value: '#6366F1' },
  ]

  const applyAccent = (color) => { setCustomAccent(color); localStorage.setItem('cw_accent', color) }

  const applyLogo = () => {
    const v = logoInput.trim()
    setCustomLogo(v)
    localStorage.setItem('cw_logo', v)
  }

  // File upload → base64 data URL stored in localStorage
  const handleLogoUpload = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (ev) => {
      const dataUrl = ev.target.result
      setCustomLogo(dataUrl)
      localStorage.setItem('cw_logo', dataUrl)
      setLogoInput('')          // clear URL field when a file is uploaded
    }
    reader.readAsDataURL(file)
  }

  const resetCustomizations = () => {
    setCustomAccent('');     localStorage.removeItem('cw_accent')
    setCustomLogo('');       localStorage.removeItem('cw_logo')
    setCustomBg('');         localStorage.removeItem('cw_bg')
    setCustomUserBubble(''); localStorage.removeItem('cw_usr_bubble')
    setCustomBotBubble('');  localStorage.removeItem('cw_bot_bubble')
    setCustomHeaderBg('');   localStorage.removeItem('cw_header_bg')
    setCustomHeaderText(''); localStorage.removeItem('cw_header_txt')
    setCustomBotName('');    localStorage.removeItem('cw_bot_name')
    setLogoInput('')
  }

  // All custom CSS variable overrides applied inline to the container
  const bgIsLight = customBg ? isLightColor(customBg) : false
  
  const customStyle = {
    ...(customAccent     && { '--cw-accent': customAccent, '--cw-accent-glow': customAccent + '55' }),
    ...(customBg         && { 
      '--cw-bg': customBg, 
      '--cw-surface': customBg,
      // Contrast flip for text when custom background is used
      ...(bgIsLight ? {
        '--cw-text': '#1A1A2E',
        '--cw-text-dim': 'rgba(26,26,46,0.7)',
        '--cw-border': 'rgba(0,0,0,0.1)',
        '--cw-border-hi': 'rgba(0,0,0,0.15)',
      } : {
        '--cw-text': '#DDDDF0',
        '--cw-text-dim': 'rgba(221,221,240,0.7)',
      })
    }),
    ...(customUserBubble && { '--cw-msg-usr-bg': customUserBubble }),
    ...(customBotBubble  && { '--cw-msg-bot-bg': customBotBubble }),
    ...(customHeaderBg   && { '--cw-header-bg': customHeaderBg }),
    ...(customHeaderText && { '--cw-header-text': customHeaderText }),
  }

  // Configuration with fallbacks
  const botName       = customBotName        || config.botName       || "Portfolio Assistant"
  const botLogo       = customLogo           || config.botLogo || "./assets/img/my_logo.png"
  const welcomeMessage = config.welcomeMessage || "Hello! I'm your AI assistant. How can I help you today?"
  const apiUrl        = config.apiUrl || (import.meta.env.VITE_BACKEND_URL ? `${import.meta.env.VITE_BACKEND_URL}/chat` : 'http://localhost:8000/chat')

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
        body: JSON.stringify({ 
          message: text, 
          session_id: SESSION_ID,
          bot_name: botName
        }),
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
    <div
      id="cw-container"
      className={`${isOpen ? 'cw-open' : ''} ${theme === 'light' ? 'cw-light' : ''}`}
      style={customStyle}
    >
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
          <div className="cw-header-controls">
            {/* Customizer */}
            <button
              id="cw-customize-btn"
              onClick={() => setShowCustomizer(v => !v)}
              aria-label="Customize widget"
              title="Customize"
              className={showCustomizer ? 'active' : ''}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 3c-4.97 0-9 4.03-9 9s4.03 9 9 9c.83 0 1.5-.67 1.5-1.5 0-.39-.15-.74-.39-1.01-.23-.26-.38-.61-.38-.99 0-.83.67-1.5 1.5-1.5H16c2.76 0 5-2.24 5-5 0-4.42-4.03-8-9-8zm-5.5 9c-.83 0-1.5-.67-1.5-1.5S5.67 9 6.5 9 8 9.67 8 10.5 7.33 12 6.5 12zm3-4C8.67 8 8 7.33 8 6.5S8.67 5 9.5 5s1.5.67 1.5 1.5S10.33 8 9.5 8zm5 0c-.83 0-1.5-.67-1.5-1.5S13.67 5 14.5 5s1.5.67 1.5 1.5S15.33 8 14.5 8zm3 4c-.83 0-1.5-.67-1.5-1.5S16.67 9 17.5 9s1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/>
              </svg>
            </button>
            {/* Theme Toggle */}
            <button id="cw-theme-toggle" onClick={toggleTheme} aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`} title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}>
              {theme === 'dark' ? (
                <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 7c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5-2.24-5-5-5zM2 13h2c.55 0 1-.45 1-1s-.45-1-1-1H2c-.55 0-1 .45-1 1s.45 1 1 1zm18 0h2c.55 0 1-.45 1-1s-.45-1-1-1h-2c-.55 0-1 .45-1 1s.45 1 1 1zM11 2v2c0 .55.45 1 1 1s1-.45 1-1V2c0-.55-.45-1-1-1s-1 .45-1 1zm0 18v2c0 .55.45 1 1 1s1-.45 1-1v-2c0-.55-.45-1-1-1s-1 .45-1 1zM5.99 4.58c-.39-.39-1.03-.39-1.41 0-.39.39-.39 1.03 0 1.41l1.06 1.06c.39.39 1.03.39 1.41 0 .38-.39.39-1.03 0-1.41L5.99 4.58zm12.37 12.37c-.39-.39-1.03-.39-1.41 0-.39.39-.39 1.03 0 1.41l1.06 1.06c.39.39 1.03.39 1.41 0 .39-.38.39-1.02 0-1.41l-1.06-1.06zm1.06-12.37l-1.06 1.06c-.39.39-.39 1.03 0 1.41.39.39 1.03.39 1.41 0l1.06-1.06c.39-.39.39-1.03 0-1.41-.38-.39-1.02-.39-1.41 0zM7.05 18.36l-1.06 1.06c-.39.39-.39 1.03 0 1.41.39.39 1.03.39 1.41 0l1.06-1.06c.39-.39.39-1.03 0-1.41-.39-.38-1.03-.39-1.41 0z"/>
                </svg>
              ) : (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 3c-4.97 0-9 4.03-9 9s4.03 9 9 9 9-4.03 9-9c0-.46-.04-.92-.1-1.36-.98 1.37-2.58 2.26-4.4 2.26-2.98 0-5.4-2.42-5.4-5.4 0-1.81.89-3.42 2.26-4.4-.44-.06-.9-.1-1.36-.1z"/>
                </svg>
              )}
            </button>
            {/* Close */}
            <button id="cw-close" onClick={() => setIsOpen(false)} aria-label="Close chat">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M13 1L1 13M1 1L13 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>
        </div>

        {/* ── Customizer Panel ──────────────────────────────────────── */}
        {showCustomizer && (
          <div id="cw-customizer">

            {/* ─ Bot Name ─────────────────────────────────────── */}
            <div className="cw-cust-section">
              <p className="cw-cust-label">Chatbot Name</p>
              <div className="cw-cust-logo-row">
                <input
                  className="cw-cust-input"
                  type="text"
                  placeholder="e.g. Jarvis, Friday..."
                  value={customBotName}
                  onChange={e => { setCustomBotName(e.target.value); localStorage.setItem('cw_bot_name', e.target.value) }}
                />
              </div>
            </div>

            {/* ─ Accent Colour ────────────────────────────────── */}
            <div className="cw-cust-section">
              <p className="cw-cust-label">Accent Colour</p>
              <div className="cw-cust-swatches">
                {ACCENT_PRESETS.map(p => (
                  <button
                    key={p.value}
                    className={`cw-swatch ${customAccent === p.value ? 'active' : ''}`}
                    style={{ background: p.value }}
                    title={p.label}
                    onClick={() => applyAccent(p.value)}
                  />
                ))}
                <label className="cw-swatch cw-swatch-picker" title="Custom colour">
                  <input type="color" value={customAccent || '#7C6AF7'} onChange={e => applyAccent(e.target.value)} />
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M20.71 5.63l-2.34-2.34a1 1 0 00-1.41 0l-3.12 3.12-1.41-1.42-1.42 1.42 1.41 1.41-6.6 6.6A2 2 0 005 16v3h3a2 2 0 001.42-.59l6.6-6.6 1.41 1.42 1.42-1.42-1.42-1.41 3.12-3.12a1 1 0 000-1.65z"/></svg>
                </label>
              </div>
            </div>

            {/* ─ Bubble Colours ──────────────────────────────── */}
            <div className="cw-cust-section">
              <p className="cw-cust-label">Bubble Colours</p>
              <div className="cw-cust-colour-rows">
                <div className="cw-cust-colour-row">
                  <span className="cw-cust-colour-name">Background</span>
                  <label className="cw-cust-colour-picker">
                    <input type="color"
                      value={customBg || (theme === 'light' ? '#F5F5FA' : '#0C0C12')}
                      onChange={e => { setCustomBg(e.target.value); localStorage.setItem('cw_bg', e.target.value) }}
                    />
                    <span className="cw-cust-colour-preview" style={{ background: customBg || (theme === 'light' ? '#F5F5FA' : '#0C0C12') }} />
                    <span className="cw-cust-colour-hex">{customBg || 'default'}</span>
                  </label>
                  {customBg && <button className="cw-cust-colour-clear" onClick={() => { setCustomBg(''); localStorage.removeItem('cw_bg') }}>✕</button>}
                </div>

                <div className="cw-cust-colour-row">
                  <span className="cw-cust-colour-name">Bot bubble</span>
                  <label className="cw-cust-colour-picker">
                    <input type="color"
                      value={customBotBubble || '#1e1e2e'}
                      onChange={e => { setCustomBotBubble(e.target.value); localStorage.setItem('cw_bot_bubble', e.target.value) }}
                    />
                    <span className="cw-cust-colour-preview" style={{ background: customBotBubble || 'rgba(255,255,255,0.04)' }} />
                    <span className="cw-cust-colour-hex">{customBotBubble || 'default'}</span>
                  </label>
                  {customBotBubble && <button className="cw-cust-colour-clear" onClick={() => { setCustomBotBubble(''); localStorage.removeItem('cw_bot_bubble') }}>✕</button>}
                </div>

                <div className="cw-cust-colour-row">
                  <span className="cw-cust-colour-name">User bubble</span>
                  <label className="cw-cust-colour-picker">
                    <input type="color"
                      value={customUserBubble || '#7C6AF7'}
                      onChange={e => { setCustomUserBubble(e.target.value); localStorage.setItem('cw_usr_bubble', e.target.value) }}
                    />
                    <span className="cw-cust-colour-preview" style={{ background: customUserBubble || 'var(--cw-accent)' }} />
                    <span className="cw-cust-colour-hex">{customUserBubble || 'default'}</span>
                  </label>
                  {customUserBubble && <button className="cw-cust-colour-clear" onClick={() => { setCustomUserBubble(''); localStorage.removeItem('cw_usr_bubble') }}>✕</button>}
                </div>

                <div className="cw-cust-colour-row">
                  <span className="cw-cust-colour-name">Header Bg</span>
                  <label className="cw-cust-colour-picker">
                    <input type="color"
                      value={customHeaderBg || '#13131C'}
                      onChange={e => { setCustomHeaderBg(e.target.value); localStorage.setItem('cw_header_bg', e.target.value) }}
                    />
                    <span className="cw-cust-colour-preview" style={{ background: customHeaderBg || 'rgba(124,106,247,0.1)' }} />
                    <span className="cw-cust-colour-hex">{customHeaderBg || 'default'}</span>
                  </label>
                  {customHeaderBg && <button className="cw-cust-colour-clear" onClick={() => { setCustomHeaderBg(''); localStorage.removeItem('cw_header_bg') }}>✕</button>}
                </div>

                <div className="cw-cust-colour-row">
                  <span className="cw-cust-colour-name">Header Text</span>
                  <label className="cw-cust-colour-picker">
                    <input type="color"
                      value={customHeaderText || '#FFFFFF'}
                      onChange={e => { setCustomHeaderText(e.target.value); localStorage.setItem('cw_header_txt', e.target.value) }}
                    />
                    <span className="cw-cust-colour-preview" style={{ background: customHeaderText || '#FFFFFF' }} />
                    <span className="cw-cust-colour-hex">{customHeaderText || 'default'}</span>
                  </label>
                  {customHeaderText && <button className="cw-cust-colour-clear" onClick={() => { setCustomHeaderText(''); localStorage.removeItem('cw_header_txt') }}>✕</button>}
                </div>
              </div>
            </div>

            {/* ─ Bot Logo ─────────────────────────────────────── */}
            <div className="cw-cust-section">
              <p className="cw-cust-label">Bot Logo</p>
              {/* Upload */}
              <label className="cw-cust-upload">
                <input type="file" accept="image/*" onChange={handleLogoUpload} />
                <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M19 13v6H5v-6H3v6a2 2 0 002 2h14a2 2 0 002-2v-6h-2zm-7-9l-4 4h3v8h2V8h3l-4-4z"/></svg>
                Upload image
              </label>
              {/* Or URL */}
              <div className="cw-cust-logo-row">
                <input
                  className="cw-cust-input"
                  type="text"
                  placeholder="or paste URL…"
                  value={logoInput}
                  onChange={e => setLogoInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && applyLogo()}
                />
                <button className="cw-cust-apply" onClick={applyLogo}>Apply</button>
              </div>
              {customLogo && (
                <div className="cw-cust-logo-preview">
                  <img src={customLogo} alt="preview" />
                  <button onClick={() => { setCustomLogo(''); setLogoInput(''); localStorage.removeItem('cw_logo') }}>✕ Remove</button>
                </div>
              )}
            </div>

            <button className="cw-cust-reset" onClick={resetCustomizations}>↺ Reset all to defaults</button>
          </div>
        )}

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
