import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

// Expose the ChatWidget globally
window.ChatWidget = {
  /**
   * Initializes the chat widget with a custom configuration.
   * @param {Object} config - Configuration object.
   * @param {string} [config.id='root'] - The ID of the container element.
   * @param {string} [config.apiUrl] - The backend endpoint (/chat).
   * @param {string} [config.botName] - Display name of the bot.
   * @param {string} [config.welcomeMessage] - Initial message shown to the user.
   */
  init: (config = {}) => {
    const containerId = config.id || 'root'
    let container = document.getElementById(containerId)
    
    // Auto-create mounting point if it doesn't exist
    if (!container) {
      container = document.createElement('div')
      container.id = containerId
      document.body.appendChild(container)
    }

    ReactDOM.createRoot(container).render(
      <React.StrictMode>
        <App config={config} />
      </React.StrictMode>,
    )
  }
}
