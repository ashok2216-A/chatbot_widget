window.ChatWidget = {
    init: function (config) {
        const API_URL = config.apiUrl || "http://localhost:8000/chat";
        const BOT_NAME = config.botName || "AI Assistant";
        const WELCOME_MSG = config.welcomeMessage || "Hello! How can I help you today?";

        // Inject Styles
        const style = document.createElement('style');
        style.innerHTML = `
            @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Syne:wght@500;600;700;800&display=swap');

            :root {
                --cw-bg:          #0C0C12;
                --cw-surface:     #13131C;
                --cw-surface-2:   #1A1A26;
                --cw-border:      rgba(255,255,255,0.07);
                --cw-border-hi:   rgba(255,255,255,0.13);
                --cw-accent:      #7C6AF7;
                --cw-accent-glow: rgba(124,106,247,0.32);
                --cw-teal:        #2DD4BF;
                --cw-text:        #DDDDF0;
                --cw-text-muted:  #55556A;
                --cw-mono:        'DM Mono', monospace;
                --cw-font:        'Syne', system-ui, sans-serif;
            }

            #cw-container {
                position: fixed;
                bottom: 28px;
                right: 28px;
                font-family: var(--cw-font);
                z-index: 999999;
                display: flex;
                flex-direction: column;
                align-items: flex-end;
            }

            /* ── Toggle ── */
            #cw-toggle {
                width: 58px;
                height: 58px;
                border-radius: 16px;
                background: var(--cw-bg);
                border: 1px solid var(--cw-border-hi);
                color: var(--cw-accent);
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow:
                    0 0 0 1px rgba(124,106,247,0.12),
                    0 8px 32px rgba(0,0,0,0.55),
                    0 0 56px var(--cw-accent-glow);
                transition:
                    transform 0.35s cubic-bezier(0.34,1.56,0.64,1),
                    box-shadow 0.3s ease,
                    opacity 0.25s ease;
                position: relative;
                overflow: hidden;
            }

            #cw-toggle::after {
                content: '';
                position: absolute;
                inset: 0;
                background: radial-gradient(circle at 35% 35%, rgba(124,106,247,0.14), transparent 65%);
                pointer-events: none;
            }

            #cw-toggle:hover {
                transform: translateY(-3px) scale(1.05);
                box-shadow:
                    0 0 0 1px rgba(124,106,247,0.28),
                    0 16px 40px rgba(0,0,0,0.65),
                    0 0 80px var(--cw-accent-glow);
            }

            #cw-toggle svg {
                width: 24px;
                height: 24px;
                fill: var(--cw-accent);
                position: relative;
                z-index: 1;
                transition: transform 0.3s ease;
            }

            .cw-open #cw-toggle {
                transform: scale(0.8) translateY(4px);
                opacity: 0;
                pointer-events: none;
            }

            /* ── Window ── */
            #cw-window {
                position: absolute;
                bottom: 76px;
                right: 0;
                width: 380px;
                height: 600px;
                max-height: calc(100vh - 120px);
                max-width: calc(100vw - 40px);
                background: var(--cw-bg);
                border: 1px solid var(--cw-border);
                border-radius: 22px;
                box-shadow:
                    0 0 0 1px rgba(124,106,247,0.07),
                    0 40px 80px rgba(0,0,0,0.75),
                    inset 0 1px 0 rgba(255,255,255,0.04);
                display: flex;
                flex-direction: column;
                overflow: hidden;
                transform-origin: bottom right;
                transform: scale(0.8) translateY(20px);
                opacity: 0;
                pointer-events: none;
                transition: transform 0.4s cubic-bezier(0.16,1,0.3,1), opacity 0.3s ease;
            }

            .cw-open #cw-window {
                transform: scale(1) translateY(0);
                opacity: 1;
                pointer-events: all;
            }

            /* ── Header ── */
            #cw-header {
                padding: 18px 20px;
                color: white;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-shrink: 0;
                border-bottom: 1px solid var(--cw-border);
                background: linear-gradient(160deg, rgba(124,106,247,0.1) 0%, transparent 60%);
                position: relative;
            }

            #cw-header::after {
                content: '';
                position: absolute;
                top: 0; left: 0; right: 0;
                height: 1px;
                background: linear-gradient(90deg, transparent, rgba(124,106,247,0.5), rgba(45,212,191,0.3), transparent);
            }

            .cw-header-title {
                display: flex;
                align-items: center;
                gap: 12px;
            }

            .cw-avatar {
                width: 42px;
                height: 42px;
                border-radius: 12px;
                background: var(--cw-surface-2);
                border: 1px solid var(--cw-border-hi);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 20px;
                position: relative;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            }

            .cw-avatar::after {
                content: '';
                position: absolute;
                bottom: -2px;
                right: -2px;
                width: 10px;
                height: 10px;
                background: var(--cw-teal);
                border: 2px solid var(--cw-bg);
                border-radius: 50%;
                box-shadow: 0 0 8px rgba(45,212,191,0.6);
            }

            .cw-info h3 {
                margin: 0;
                font-size: 14px;
                font-weight: 700;
                color: var(--cw-text);
                letter-spacing: 0.01em;
                line-height: 1.2;
            }

            .cw-info p {
                margin: 3px 0 0;
                font-family: var(--cw-mono);
                font-size: 10.5px;
                color: var(--cw-teal);
                letter-spacing: 0.04em;
            }

            #cw-close {
                background: var(--cw-surface-2);
                border: 1px solid var(--cw-border);
                color: var(--cw-text-muted);
                cursor: pointer;
                width: 30px;
                height: 30px;
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s ease;
            }

            #cw-close:hover {
                background: rgba(255,255,255,0.06);
                border-color: var(--cw-border-hi);
                color: var(--cw-text);
                transform: rotate(90deg);
            }

            /* ── Messages ── */
            #cw-messages {
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                display: flex;
                flex-direction: column;
                gap: 12px;
                scroll-behavior: smooth;
            }

            #cw-messages::-webkit-scrollbar { width: 3px; }
            #cw-messages::-webkit-scrollbar-track { background: transparent; }
            #cw-messages::-webkit-scrollbar-thumb { background: var(--cw-border-hi); border-radius: 10px; }

            .cw-message {
                max-width: 85%;
                padding: 12px 16px;
                border-radius: 18px;
                font-size: 13.5px;
                line-height: 1.6;
                animation: cw-msg-enter 0.4s cubic-bezier(0.16,1,0.3,1) forwards;
                opacity: 0;
                transform: translateY(10px);
                word-wrap: break-word;
            }

            @keyframes cw-msg-enter {
                to { opacity: 1; transform: translateY(0); }
            }

            .cw-message.bot {
                background: var(--cw-surface);
                color: var(--cw-text);
                align-self: flex-start;
                border-bottom-left-radius: 4px;
                border: 1px solid var(--cw-border);
            }

            .cw-message.user {
                background: linear-gradient(135deg, #7C6AF7, #5B4FE0);
                color: rgba(255,255,255,0.95);
                align-self: flex-end;
                border-bottom-right-radius: 4px;
                box-shadow: 0 4px 20px rgba(124,106,247,0.35);
            }

            /* ── Loading ── */
            .cw-message.loading {
                display: flex;
                gap: 6px;
                align-items: center;
                padding: 16px 20px;
            }

            .cw-dot {
                width: 6px;
                height: 6px;
                background: var(--cw-accent);
                border-radius: 50%;
                animation: cw-typing 1.2s infinite ease-in-out both;
            }

            .cw-dot:nth-child(1) { animation-delay: 0s; }
            .cw-dot:nth-child(2) { animation-delay: 0.15s; }
            .cw-dot:nth-child(3) { animation-delay: 0.3s; }

            @keyframes cw-typing {
                0%, 60%, 100% { transform: translateY(0); opacity: 0.3; }
                30% { transform: translateY(-5px); opacity: 1; }
            }

            /* ── Input ── */
            #cw-input-area {
                padding: 16px;
                background: rgba(12,12,18,0.8);
                border-top: 1px solid var(--cw-border);
                flex-shrink: 0;
            }

            .cw-input-wrapper {
                display: flex;
                align-items: center;
                background: var(--cw-surface);
                border: 1px solid var(--cw-border-hi);
                border-radius: 14px;
                padding: 5px 5px 5px 16px;
                transition: border-color 0.25s ease, box-shadow 0.25s ease;
            }

            .cw-input-wrapper:focus-within {
                border-color: rgba(124,106,247,0.5);
                box-shadow: 0 0 0 3px rgba(124,106,247,0.1);
            }

            #cw-input {
                flex: 1;
                border: none;
                background: transparent;
                padding: 10px 0;
                font-size: 13.5px;
                font-family: var(--cw-font);
                color: var(--cw-text);
                outline: none;
            }

            #cw-input::placeholder { color: var(--cw-text-muted); }

            #cw-send {
                background: var(--cw-accent);
                color: white;
                border: none;
                width: 38px;
                height: 38px;
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: transform 0.2s cubic-bezier(0.34,1.56,0.64,1), box-shadow 0.2s ease;
                box-shadow: 0 4px 14px rgba(124,106,247,0.4);
                flex-shrink: 0;
            }

            #cw-send:hover {
                transform: scale(1.1);
                box-shadow: 0 6px 20px rgba(124,106,247,0.55);
            }

            #cw-send:active { transform: scale(0.94); }

            #cw-send:disabled {
                background: var(--cw-surface-2);
                box-shadow: none;
                cursor: not-allowed;
                transform: none;
            }

            #cw-send svg {
                width: 18px;
                height: 18px;
                fill: white;
                margin-left: 2px;
            }

            #cw-send:disabled svg { fill: var(--cw-text-muted); }

            .cw-footer {
                text-align: center;
                font-family: var(--cw-mono);
                font-size: 10px;
                color: var(--cw-text-muted);
                margin-top: 10px;
                margin-bottom: -2px;
                letter-spacing: 0.04em;
            }
        `;
        document.head.appendChild(style);

        // Inject DOM
        const container = document.createElement("div");
        container.id = "cw-container";

        container.innerHTML = `
            <div id="cw-window">
                <div id="cw-header">
                    <div class="cw-header-title">
                        <div class="cw-avatar">
                            <img src="my_logo.png" alt="Bot Logo" style="width: 100%; height: 100%; object-fit: cover; border-radius: inherit;">
                        </div>
                        <div class="cw-info">
                            <h3>${BOT_NAME}</h3>
                            <p>Online & Ready</p>
                        </div>
                    </div>
                    <button id="cw-close" aria-label="Close chat">
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M13 1L1 13M1 1L13 13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </button>
                </div>
                <div id="cw-messages"></div>
                <div id="cw-input-area">
                    <div class="cw-input-wrapper">
                        <input type="text" id="cw-input" placeholder="Type your message..." autocomplete="off"/>
                        <button id="cw-send" aria-label="Send message">
                            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                            </svg>
                        </button>
                    </div>
                    <div class="cw-footer">⚡ Built by Ashok</div>
                </div>
            </div>
            <button id="cw-toggle" aria-label="Open chat">
                <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
                </svg>
            </button>
        `;

        document.body.appendChild(container);

        // Logic
        const toggleBtn = document.getElementById("cw-toggle");
        const closeBtn = document.getElementById("cw-close");
        const windowEl = document.getElementById("cw-window");
        const input = document.getElementById("cw-input");
        const sendBtn = document.getElementById("cw-send");
        const messages = document.getElementById("cw-messages");

        let isOpen = false;
        
        // Generate a random mathematical token when the page loads, so memory persists dynamically but wipes on refresh
        const sessionId = "sess_" + Math.random().toString(36).substring(2, 12);

        const toggleWidget = () => {
            isOpen = !isOpen;
            if (isOpen) {
                container.classList.add('cw-open');
                if (messages.children.length === 0) {
                    addMessage(WELCOME_MSG, "bot");
                }
                setTimeout(() => input.focus(), 300);
            } else {
                container.classList.remove('cw-open');
            }
        };

        toggleBtn.addEventListener('click', toggleWidget);
        closeBtn.addEventListener('click', toggleWidget);

        const appendDOM = (el) => {
            messages.appendChild(el);
            messages.scrollTop = messages.scrollHeight;
        };

        const addMessage = (text, sender) => {
            const div = document.createElement("div");
            div.className = "cw-message " + sender;
            div.innerText = text;
            appendDOM(div);
            return div;
        };

        const addLoading = () => {
            const div = document.createElement("div");
            div.className = "cw-message bot loading";
            div.innerHTML = '<div class="cw-dot"></div><div class="cw-dot"></div><div class="cw-dot"></div>';
            appendDOM(div);
            return div;
        };

        const handleSend = async () => {
            const message = input.value.trim();
            if (!message) return;

            addMessage(message, "user");
            input.value = "";
            input.disabled = true;
            sendBtn.disabled = true;

            const loadingEl = addLoading();

            try {
                const res = await fetch(API_URL, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message: message, session_id: sessionId })
                });

                if (!res.ok) throw new Error("Network response was not ok");

                const data = await res.json();
                messages.removeChild(loadingEl);
                addMessage(data.reply || "I'm having trouble thinking right now.", "bot");

            } catch (err) {
                messages.removeChild(loadingEl);
                addMessage("Oops! Servers seem to be down or unreachable. Try again later.", "bot");
            } finally {
                input.disabled = false;
                sendBtn.disabled = false;
                input.focus();
            }
        };

        sendBtn.addEventListener('click', handleSend);
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleSend();
            }
        });
    }
};