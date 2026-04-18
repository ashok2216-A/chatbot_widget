import { useState, useRef } from 'react';

// ─── ICONS ────────────────────────────────────────────────────────────────────
const ICONS = {
  send:     <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>,
  check:    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>,
  close:    <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>,
  star:     <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21 12 17.27z"/>,
  info:     <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>,
  mail:     <path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/>,
  calendar: <path d="M17 12h-5v5h5v-5zM16 1v2H8V1H6v2H5c-1.11 0-1.99.9-1.99 2L3 19c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2h-1V1h-2zm3 18H5V8h14v11z"/>,
  user:     <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>,
  search:   <path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>,
  warning:  <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>,
  link:     <path d="M3.9 12c0-1.71 1.39-3.1 3.1-3.1h4V7H7c-2.76 0-5 2.24-5 5s2.24 5 5 5h4v-1.9H7c-1.71 0-3.1-1.39-3.1-3.1zM8 13h8v-2H8v2zm9-6h-4v1.9h4c1.71 0 3.1 1.39 3.1 3.1s-1.39 3.1-3.1 3.1h-4V17h4c2.76 0 5-2.24 5-5s-2.24-5-5-5z"/>,
  phone:    <path d="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z"/>,
  download: <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>,
  play:     <path d="M8 5v14l11-7z"/>,
  music:    <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>,
  image:    <path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/>,
  edit:     <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>,
  trash:    <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>,
  settings: <path d="M19.14,12.94c0.04-0.3,0.06-0.61,0.06-0.94c0-0.32-0.02-0.64-0.07-0.94l2.03-1.58c0.18-0.14,0.23-0.41,0.12-0.61 l-1.92-3.32c-0.12-0.22-0.37-0.29-0.59-0.22l-2.39,0.96c-0.5-0.38-1.03-0.7-1.62-0.94L14.4,2.81c-0.04-0.24-0.24-0.41-0.48-0.41 h-3.84c-0.24,0-0.43,0.17-0.47,0.41L9.25,5.35C8.66,5.59,8.12,5.92,7.63,6.29L5.24,5.33c-0.22-0.08-0.47,0-0.59,0.22L2.74,8.87 C2.62,9.08,2.66,9.34,2.86,9.48l2.03,1.58C4.84,11.36,4.8,11.69,4.8,12s0.02,0.64,0.07,0.94l-2.03,1.58 c-0.18,0.14-0.23,0.41-0.12,0.61l1.92,3.32c0.12,0.22,0.37,0.29,0.59,0.22l2.39-0.96c0.5,0.38,1.03,0.7,1.62,0.94l0.36,2.54 c0.05,0.24,0.24,0.41,0.48,0.41h3.84c0.24,0,0.44-0.17,0.47-0.41l0.36-2.54c0.59-0.24,1.13-0.56,1.62-0.94l2.39,0.96 c0.22,0.08,0.47,0,0.59-0.22l1.92-3.32c0.12-0.22,0.07-0.47-0.12-0.61L19.14,12.94z M12,15.6c-1.98,0-3.6-1.62-3.6-3.6 s1.62-3.6,3.6-3.6s3.6,1.62,3.6,3.6S13.98,15.6,12,15.6z"/>,
};

function SvgIcon({ name, size = 18, className = '' }) {
  const path = ICONS[name] || ICONS.star;
  return (
    <svg className={`a2ui-icon ${className}`} width={size} height={size} viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
      {path}
    </svg>
  );
}

// ─── LAYOUT COMPONENTS ───────────────────────────────────────────────────────

export function A2Row({ children = [], align = 'center', justify = 'start', gap = 8, renderNode }) {
  const justifyMap = { start: 'flex-start', center: 'center', end: 'flex-end', spaceBetween: 'space-between', spaceAround: 'space-around' };
  const alignMap = { start: 'flex-start', center: 'center', end: 'flex-end', stretch: 'stretch', baseline: 'baseline' };
  return (
    <div className="a2ui-row" style={{ display: 'flex', flexDirection: 'row', alignItems: alignMap[align] || 'center', justifyContent: justifyMap[justify] || 'flex-start', gap, flexWrap: 'wrap' }}>
      {children.map((child, i) => <div key={i}>{renderNode(child)}</div>)}
    </div>
  );
}

export function A2Column({ children = [], align = 'stretch', gap = 10, renderNode }) {
  const alignMap = { start: 'flex-start', center: 'center', end: 'flex-end', stretch: 'stretch' };
  return (
    <div className="a2ui-column" style={{ display: 'flex', flexDirection: 'column', alignItems: alignMap[align] || 'stretch', gap }}>
      {children.map((child, i) => renderNode(child, i))}
    </div>
  );
}

export function A2Card({ children = [], title, elevated = false, renderNode }) {
  return (
    <div className={`a2ui-card-v3 ${elevated ? 'elevated' : ''}`}>
      {title && <div className="a2ui-card-title">{title}</div>}
      <div className="a2ui-card-body">
        {children.map((child, i) => renderNode(child, i))}
      </div>
    </div>
  );
}

export function A2List({ children = [], ordered = false, renderNode }) {
  const Tag = ordered ? 'ol' : 'ul';
  return (
    <Tag className="a2ui-list">
      {children.map((child, i) => (
        <li key={i} className="a2ui-list-item">{renderNode(child)}</li>
      ))}
    </Tag>
  );
}

// ─── CONTENT COMPONENTS ──────────────────────────────────────────────────────

export function A2Text({ value = '', variant = 'body' }) {
  const tagMap = { heading: 'h3', subheading: 'h4', body: 'p', caption: 'span', label: 'span', code: 'code' };
  const Tag = tagMap[variant] || 'p';
  return <Tag className={`a2ui-text a2ui-text-${variant}`}>{value}</Tag>;
}

export function A2Image({ src, alt = 'Image', width, height, rounded = true, className = '' }) {
  const [error, setError] = useState(false);
  
  if (error || !src) return (
    <div className={`a2ui-image-error-compact ${rounded ? 'rounded' : ''}`} style={{ width: width || 40, height: height || 40 }}>
      <SvgIcon name="image" size={16} />
    </div>
  );

  return (
    <img
      className={`a2ui-image ${rounded ? 'rounded' : ''} ${className}`}
      src={src}
      alt={alt}
      style={{ width: width || '100%', height: height || 'auto', objectFit: 'contain' }}
      onError={() => setError(true)}
    />
  );
}

export function A2Icon({ name = 'star', size = 20, color }) {
  return (
    <span className="a2ui-icon-wrap" style={color ? { color } : {}}>
      <SvgIcon name={name} size={size} />
    </span>
  );
}

export function A2Video({ src, poster }) {
  return (
    <div className="a2ui-video-wrap">
      <video className="a2ui-video" controls poster={poster} preload="metadata">
        <source src={src} />
        Your browser does not support video.
      </video>
    </div>
  );
}

export function A2AudioPlayer({ src, title = 'Audio' }) {
  const audioRef = useRef(null);
  const [playing, setPlaying] = useState(false);

  const toggle = () => {
    if (playing) { audioRef.current.pause(); setPlaying(false); }
    else { audioRef.current.play(); setPlaying(true); }
  };

  return (
    <div className="a2ui-audio">
      <audio ref={audioRef} src={src} onEnded={() => setPlaying(false)} />
      <button className="a2ui-audio-btn" onClick={toggle}>
        <SvgIcon name={playing ? 'close' : 'play'} size={16} />
      </button>
      <div className="a2ui-audio-info">
        <SvgIcon name="music" size={14} />
        <span>{title}</span>
      </div>
    </div>
  );
}

export function A2Content({ html = '' }) {
  // Basic sanitization: strip script tags
  const safe = html.replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, '');
  return <div className="a2ui-content" dangerouslySetInnerHTML={{ __html: safe }} />;
}

export function A2Divider({ label }) {
  return (
    <div className="a2ui-divider">
      {label && <span className="a2ui-divider-label">{label}</span>}
    </div>
  );
}

// ─── INPUT COMPONENTS ────────────────────────────────────────────────────────

export function A2Button({ label = 'Action', message, variant = 'primary', icon, onCommand }) {
  return (
    <button
      className={`a2ui-btn a2ui-btn-v3 ${variant}`}
      onClick={() => message && onCommand(message)}
    >
      {icon && <SvgIcon name={icon} size={14} className="btn-icon" />}
      {label}
    </button>
  );
}

export function A2CheckBox({ label = 'Option', checked: initialChecked = false, submit_label = 'Confirm', message_on, message_off, onCommand }) {
  const [checked, setChecked] = useState(!!initialChecked);
  
  const submit = () => {
    const msg = checked ? message_on : message_off;
    if (msg) onCommand(msg);
  };
  
  return (
    <div className="a2ui-textfield-row" style={{ alignItems: 'center' }}>
      <label className="a2ui-checkbox" style={{ flex: 1, cursor: 'pointer' }}>
        <div className={`a2ui-checkbox-box ${checked ? 'checked' : ''}`} onClick={() => setChecked(!checked)}>
          {checked && <SvgIcon name="check" size={12} />}
        </div>
        <span className="a2ui-checkbox-label" onClick={() => setChecked(!checked)}>{label}</span>
      </label>
      <button className="a2ui-btn a2ui-btn-v3 primary sm" onClick={submit}>{submit_label}</button>
    </div>
  );
}

export function A2TextField({ label, placeholder = 'Type here…', value: initialValue = '', multiline = false, submit_label = 'Save', onCommand }) {
  const [value, setValue] = useState(initialValue);
  const submit = () => {
    if (value.trim()) {
      onCommand(`${label ? label + ': ' : ''}${value.trim()}`);
    }
  };
  return (
    <div className="a2ui-textfield">
      {label && <span className="a2ui-input-label">{label}</span>}
      <div className={`a2ui-textfield-row ${multiline ? 'multiline-row' : ''}`}>
        {multiline ? (
          <textarea
            className="a2ui-input a2ui-textarea"
            placeholder={placeholder}
            value={value}
            onChange={e => setValue(e.target.value)}
            rows={4}
          />
        ) : (
          <input
            className="a2ui-input"
            type="text"
            placeholder={placeholder}
            value={value}
            onChange={e => setValue(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && submit()}
          />
        )}
        <button className="a2ui-btn a2ui-btn-v3 primary sm" onClick={submit}>{submit_label}</button>
      </div>
    </div>
  );
}

export function A2Slider({ label, min = 0, max = 100, value: initial = 50, step = 1, submit_label = 'Confirm', onCommand }) {
  const [value, setValue] = useState(initial);
  return (
    <div className="a2ui-slider">
      {label && <span className="a2ui-input-label">{label}</span>}
      <div className="a2ui-slider-row">
        <input
          className="a2ui-slider-input"
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={e => setValue(Number(e.target.value))}
        />
        <span className="a2ui-slider-val">{value}</span>
      </div>
      <button className="a2ui-btn a2ui-btn-v3 primary sm" onClick={() => onCommand(`${label ? label + ': ' : ''}${value}`)}>
        {submit_label}
      </button>
    </div>
  );
}

export function A2DateTimeInput({ label, submit_label = 'Confirm', onCommand }) {
  const [value, setValue] = useState('');
  const submit = () => {
    if (value) onCommand(`${label ? label + ': ' : ''}${value}`);
  };
  return (
    <div className="a2ui-datetimeinput">
      {label && <span className="a2ui-input-label">{label}</span>}
      <div className="a2ui-textfield-row">
        <input
          className="a2ui-input"
          type="datetime-local"
          value={value}
          onChange={e => setValue(e.target.value)}
        />
        <button className="a2ui-btn a2ui-btn-v3 primary sm" onClick={submit}>{submit_label}</button>
      </div>
    </div>
  );
}

export function A2ChoicePicker({ label, options = [], multi = false, submit_label = 'Select', onCommand }) {
  const [selected, setSelected] = useState(multi ? [] : null);

  const toggle = (opt) => {
    if (multi) {
      setSelected(prev => prev.includes(opt) ? prev.filter(x => x !== opt) : [...prev, opt]);
    } else {
      setSelected(opt);
      // Intentionally removed auto-send, requiring the submit button
    }
  };

  const submitPicker = () => {
    if (multi && selected.length) onCommand(`${label ? label + ': ' : ''}${selected.join(', ')}`);
    else if (!multi && selected) onCommand(`${label ? label + ': ' : ''}${selected}`);
  };

  return (
    <div className="a2ui-choicepicker">
      {label && <span className="a2ui-input-label">{label}</span>}
      <div className="a2ui-choice-options">
        {options.map((opt, i) => {
          const isSelected = multi ? selected.includes(opt) : selected === opt;
          return (
            <button
              key={i}
              className={`a2ui-choice-opt ${isSelected ? 'selected' : ''}`}
              onClick={() => toggle(opt)}
            >
              {opt}
            </button>
          );
        })}
      </div>
      
      {/* Show submit button only if a choice has been made */}
      {((multi && selected.length > 0) || (!multi && selected)) && (
        <button className="a2ui-btn a2ui-btn-v3 primary sm" style={{ marginTop: 8 }} onClick={submitPicker}>
          {submit_label} {multi ? `(${selected.length})` : ''}
        </button>
      )}
    </div>
  );
}

// ─── NAVIGATION COMPONENTS ───────────────────────────────────────────────────

export function A2Tabs({ tabs = [], renderNode }) {
  const [active, setActive] = useState(0);
  if (!tabs.length) return null;
  return (
    <div className="a2ui-tabs">
      <div className="a2ui-tabs-bar">
        {tabs.map((tab, i) => (
          <button
            key={i}
            className={`a2ui-tab-btn ${active === i ? 'active' : ''}`}
            onClick={() => setActive(i)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="a2ui-tab-content">
        {(tabs[active]?.children || []).map((child, i) => renderNode(child, i))}
      </div>
    </div>
  );
}

export function A2Modal({ title, children = [], close_message = 'Close', open: initialOpen = true, renderNode, onCommand }) {
  const [open, setOpen] = useState(initialOpen);
  if (!open) return null;
  return (
    <div className="a2ui-modal-overlay" onClick={() => { setOpen(false); if (close_message) onCommand(close_message); }}>
      <div className="a2ui-modal" onClick={e => e.stopPropagation()}>
        <div className="a2ui-modal-header">
          <span className="a2ui-modal-title">{title}</span>
          <button className="a2ui-modal-close" onClick={() => { setOpen(false); if (close_message) onCommand(close_message); }}>
            <SvgIcon name="close" size={16} />
          </button>
        </div>
        <div className="a2ui-modal-body">
          {children.map((child, i) => renderNode(child, i))}
        </div>
      </div>
    </div>
  );
}

export function A2Navigation({ links = [], onCommand }) {
  return (
    <nav className="a2ui-navigation">
      {links.map((link, i) => (
        <button key={i} className="a2ui-nav-link" onClick={() => link.message && onCommand(link.message)}>
          {link.icon && <SvgIcon name={link.icon} size={14} />}
          {link.label}
        </button>
      ))}
    </nav>
  );
}
