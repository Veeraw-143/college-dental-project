/**
 * Chatbot Widget - Floating chat interface for Surabi Dental Care
 * Features: Multi-language support (EN, TA, HI), light/dark theme, message history
 */

(function() {
  'use strict';

  // Configuration
  const CONFIG = {
    apiEndpoint: '/api/chatbot-message/',
    defaultLanguage: 'en',
    messageTimeout: 20000, // 20 seconds - matches backend timeout
  };

  // Translations
  const TRANSLATIONS = {
    en: {
      title: 'Dental Care Assistant',
      placeholder: 'Ask a question...',
      send: 'Send',
      close: 'Close',
      language: 'Language',
      loading: 'Thinking...',
      error: 'Sorry, I encountered an error. Please try again.',
      offline: 'Chatbot service is offline. Please contact us directly.',
      welcome: "Hi! I'm your dental care assistant. How can I help you today?",
    },
    ta: {
      title: 'பல் பராமரிப்பு உதவி',
      placeholder: 'ஒரு கேள்வி கேளுங்கள்...',
      send: 'அனுப்பவும்',
      close: 'மூடவும்',
      language: 'மொழி',
      loading: 'சிந்தனை...',
      error: 'மன்னிக்கவும், எனக்கு ஒரு பிழை ஏற்பட்டது. மீண்டும் முயற்சி செய்யவும்.',
      offline: 'சேட்வட் சேவை இணையத்தில் இல்லை. நம்மை நேரடியாக தொடர்பு கொள்ளவும்.',
      welcome: "வணக்கம்! நான் உங்கள் பல் பராமரிப்பு உதவி. நான் உங்களுக்கு எப்போதைக்கு உதவலாம்?",
    },
    hi: {
      title: 'दंत देखभाल सहायक',
      placeholder: 'एक सवाल पूछें...',
      send: 'भेजें',
      close: 'बंद करें',
      language: 'भाषा',
      loading: 'विचार...',
      error: 'क्षमा करें, मुझे एक त्रुटि का सामना करना पड़ा। कृपया दोबारा कोशिश करें।',
      offline: 'चैटबॉट सेवा ऑफ़लाइन है। कृपया हमसे सीधे संपर्क करें।',
      welcome: "नमस्ते! मैं आपका दंत देखभाल सहायक हूं। मैं आपकी कैसे मदद कर सकता हूं?",
    }
  };

  // Initialize chatbot widget
  function initChatbot() {
    // Check if widget already initialized
    if (document.getElementById('chatbot-widget')) {
      return;
    }

    // Create widget HTML
    const widget = createWidgetHTML();
    document.body.appendChild(widget);

    // Get widget elements
    const toggleBtn = document.getElementById('chatbot-toggle');
    const closeBtn = document.getElementById('chatbot-close');
    const container = document.getElementById('chatbot-container');
    const form = document.getElementById('chatbot-form');
    const input = document.getElementById('chatbot-input');
    const langSelector = document.getElementById('chatbot-language');
    const messagesDiv = document.getElementById('chatbot-messages');

    // Get current language from localStorage or browser preference
    let currentLanguage = localStorage.getItem('chatbotLanguage') || getPreferredLanguage();
    langSelector.value = currentLanguage;

    // Event listeners
    toggleBtn.addEventListener('click', () => {
      container.classList.toggle('active');
      if (container.classList.contains('active')) {
        input.focus();
        // Show welcome message if chat is empty
        if (messagesDiv.children.length === 1) {
          addMessage(TRANSLATIONS[currentLanguage].welcome, 'bot');
        }
      }
    });

    closeBtn.addEventListener('click', () => {
      container.classList.remove('active');
    });

    langSelector.addEventListener('change', (e) => {
      currentLanguage = e.target.value;
      localStorage.setItem('chatbotLanguage', currentLanguage);
      // Update placeholder
      input.placeholder = TRANSLATIONS[currentLanguage].placeholder;
    });

    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const message = input.value.trim();
      if (!message) return;

      // Add user message to chat
      addMessage(message, 'user');
      input.value = '';

      // Send to backend
      sendMessage(message, currentLanguage, (response) => {
        if (response.success) {
          addMessage(response.message, 'bot');
          
          // Check if there's an action/redirect
          if (response.action === 'redirect' && response.redirect_url) {
            handleAutoRedirect(response.redirect_url, response.auto_redirect_delay || 3000);
          }
        } else {
          if (response.error === 'Chatbot service not running') {
            addMessage(TRANSLATIONS[currentLanguage].offline, 'bot');
          } else {
            addMessage(response.message || TRANSLATIONS[currentLanguage].error, 'bot');
          }
        }
      });

      // Show loading state
      const loadingMsg = TRANSLATIONS[currentLanguage].loading;
      addMessage(loadingMsg, 'bot loading');
    });

    // Apply theme
    applyTheme();
    document.addEventListener('theme-changed', applyTheme);
  }

  // Create widget HTML structure
  function createWidgetHTML() {
    const wrapper = document.createElement('div');
    wrapper.id = 'chatbot-widget';
    wrapper.innerHTML = `
      <div id="chatbot-container" class="chatbot-container">
        <div class="chatbot-header">
          <h3 class="chatbot-title" id="chatbot-title">${TRANSLATIONS.en.title}</h3>
          <div class="chatbot-header-controls">
            <select id="chatbot-language" class="chatbot-language">
              <option value="en">English</option>
              <option value="ta">Tamil</option>
              <option value="hi">Hindi</option>
            </select>
            <button id="chatbot-close" class="chatbot-close" title="Close">&times;</button>
          </div>
        </div>

        <div id="chatbot-messages" class="chatbot-messages"></div>

        <form id="chatbot-form" class="chatbot-form">
          <input
            type="text"
            id="chatbot-input"
            class="chatbot-input"
            placeholder="${TRANSLATIONS.en.placeholder}"
            autocomplete="off"
          />
          <button type="submit" class="chatbot-send">${TRANSLATIONS.en.send}</button>
        </form>
      </div>

      <button id="chatbot-toggle" class="chatbot-toggle" title="Open Chat">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
      </button>
    `;
    return wrapper;
  }

  // Add message to chat
  function addMessage(text, sender) {
    const messagesDiv = document.getElementById('chatbot-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chatbot-message chatbot-${sender}`;

    if (sender.includes('loading')) {
      messageDiv.innerHTML = `
        <div class="chatbot-message-text">
          <div class="chatbot-loading">
            <span></span><span></span><span></span>
          </div>
        </div>
      `;
      messageDiv.id = 'chatbot-loading';
    } else {
      messageDiv.innerHTML = `<div class="chatbot-message-text">${escapeHtml(text)}</div>`;
    }

    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  }

  // Send message to backend
  function sendMessage(message, language, callback) {
    const loadingMsg = document.getElementById('chatbot-loading');
    
    fetch(CONFIG.apiEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
      },
      body: JSON.stringify({
        message: message,
        language: language,
      }),
    })
      .then((response) => {
        // Remove loading message
        if (loadingMsg) loadingMsg.remove();

        if (!response.ok) {
          // Handle HTTP errors
          if (response.status === 403) {
            throw new Error('Permission denied - Chatbot service unavailable');
          } else if (response.status === 503) {
            throw new Error('Chatbot service is offline. Please try again later.');
          } else if (response.status === 504) {
            throw new Error('Chatbot response timeout. Please try again.');
          } else {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
        }
        return response.json();
      })
      .then((data) => {
        // Check if response has success flag
        if (data.success === true) {
          callback({
            success: true,
            message: data.message || data.response || 'No response',
            language: data.language || language,
            mode: data.mode || 'ai',
            action: data.action,
            redirect_url: data.redirect_url,
            auto_redirect_delay: data.auto_redirect_delay
          });
        } else if (data.error) {
          // Error response from server
          callback({
            success: false,
            message: data.message || data.error || TRANSLATIONS[language].error,
            error: data.error
          });
        } else if (data.message) {
          // Success response
          callback({
            success: true,
            message: data.message,
            language: data.language || language
          });
        } else {
          throw new Error('Invalid response format');
        }
      })
      .catch((error) => {
        // Remove loading message
        if (loadingMsg) loadingMsg.remove();

        console.error('Chatbot error:', error);
        
        // Provide helpful fallback message
        const errorMessages = {
          en: 'I\'m having trouble connecting. Please contact us at +91-9123-456-789 or try again in a moment.',
          ta: 'நان் இணைக்கப் பிரச்சினை உள்ளது. +91-9123-456-789 என்ற எண்ணில் தொலைபேசி செய்யவும் அல்லது சிறிது நேரத்தில் மீண்டும் முயற்சி செய்யவும்.',
          hi: 'मुझे कनेक्ट करने में परेशानी हो रही है। कृपया +91-9123-456-789 पर कॉल करें या कुछ समय बाद फिर से कोशिश करें।'
        };
        
        callback({
          success: false,
          message: errorMessages[language] || errorMessages['en'],
          error: error.message,
        });
      });
  }

  // Handle auto-redirect to different pages
  function handleAutoRedirect(redirectUrl, delayMs) {
    const messagesDiv = document.getElementById('chatbot-messages');
    
    // Create a countdown message
    const countdownDiv = document.createElement('div');
    countdownDiv.className = 'chatbot-message chatbot-bot redirect-countdown';
    
    let secondsLeft = Math.ceil(delayMs / 1000);
    const updateCountdown = () => {
      countdownDiv.innerHTML = `
        <div class="chatbot-message-text">
          <small style="color: #666; opacity: 0.8;">Redirecting to page in ${secondsLeft} second${secondsLeft !== 1 ? 's' : ''}...</small>
        </div>
      `;
    };
    
    updateCountdown();
    messagesDiv.appendChild(countdownDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    // Update countdown every second
    const countdownInterval = setInterval(() => {
      secondsLeft--;
      if (secondsLeft > 0) {
        updateCountdown();
      } else {
        clearInterval(countdownInterval);
        // Redirect after delay
        setTimeout(() => {
          window.location.href = redirectUrl;
        }, 500);
      }
    }, 1000);
  }

  // Get preferred language from browser
  function getPreferredLanguage() {
    const lang = navigator.language || navigator.userLanguage;
    if (lang.startsWith('ta')) return 'ta';
    if (lang.startsWith('hi')) return 'hi';
    return 'en';
  }

  // Escape HTML to prevent XSS
  function escapeHtml(text) {
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;',
    };
    return text.replace(/[&<>"']/g, (m) => map[m]);
  }

  // Apply theme (light/dark)
  function applyTheme() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark' ||
                   document.body.classList.contains('dark-theme');
    const widget = document.getElementById('chatbot-widget');
    if (widget) {
      if (isDark) {
        widget.classList.add('dark-theme');
      } else {
        widget.classList.remove('dark-theme');
      }
    }
  }

  // Add styles to page
  function addStyles() {
    const style = document.createElement('style');
    style.textContent = `
      /* Chatbot Widget Styles */
      #chatbot-widget {
        --primary-color: #2fa4a9;
        --bg-light: #ffffff;
        --text-dark: #333333;
        --border-color: #e0e0e0;
        --bot-bg: #f0f0f0;
        --user-bg: #e8f4f8;
      }

      #chatbot-widget.dark-theme {
        --bg-light: #2a2a2a;
        --text-dark: #ffffff;
        --border-color: #444444;
        --bot-bg: #3a3a3a;
        --user-bg: #1a4d52;
      }

      .chatbot-toggle {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 56px;
        height: 56px;
        border-radius: 50%;
        background-color: var(--primary-color);
        color: white;
        border: none;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 999;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0;
      }

      .chatbot-toggle:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
      }

      .chatbot-toggle:active {
        transform: scale(0.95);
      }

      .chatbot-container {
        position: fixed;
        bottom: 90px;
        right: 20px;
        width: 380px;
        height: 500px;
        background-color: var(--bg-light);
        border-radius: 12px;
        box-shadow: 0 5px 40px rgba(0, 0, 0, 0.16);
        display: flex;
        flex-direction: column;
        z-index: 998;
        opacity: 0;
        transform: translateY(20px);
        pointer-events: none;
        transition: all 0.3s ease;
      }

      .chatbot-container.active {
        opacity: 1;
        transform: translateY(0);
        pointer-events: all;
      }

      .chatbot-header {
        background-color: var(--primary-color);
        color: white;
        padding: 16px;
        border-radius: 12px 12px 0 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .chatbot-title {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
      }

      .chatbot-header-controls {
        display: flex;
        gap: 8px;
        align-items: center;
      }

      .chatbot-language {
        padding: 4px 8px;
        border: none;
        border-radius: 4px;
        background-color: rgba(255, 255, 255, 0.2);
        color: white;
        cursor: pointer;
        font-size: 12px;
      }

      .chatbot-language option {
        background-color: var(--bg-light);
        color: var(--text-dark);
      }

      .chatbot-close {
        background: none;
        border: none;
        color: white;
        font-size: 24px;
        cursor: pointer;
        padding: 0;
        width: 28px;
        height: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: transform 0.2s;
      }

      .chatbot-close:hover {
        transform: scale(1.2);
      }

      .chatbot-messages {
        flex: 1;
        overflow-y: auto;
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 12px;
        background-color: var(--bg-light);
      }

      .chatbot-message {
        display: flex;
        animation: messageSlide 0.3s ease;
      }

      @keyframes messageSlide {
        from {
          opacity: 0;
          transform: translateY(10px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      .chatbot-user {
        justify-content: flex-end;
      }

      .chatbot-bot {
        justify-content: flex-start;
      }

      .chatbot-message-text {
        max-width: 75%;
        padding: 10px 14px;
        border-radius: 8px;
        word-wrap: break-word;
        line-height: 1.4;
        font-size: 14px;
      }

      .chatbot-user .chatbot-message-text {
        background-color: var(--user-bg);
        color: var(--text-dark);
      }

      .chatbot-bot .chatbot-message-text {
        background-color: var(--bot-bg);
        color: var(--text-dark);
      }

      .chatbot-loading {
        display: flex;
        gap: 4px;
        align-items: center;
      }

      .chatbot-loading span {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: var(--primary-color);
        animation: loading 1.4s ease-in-out infinite;
      }

      .chatbot-loading span:nth-child(2) {
        animation-delay: 0.2s;
      }

      .chatbot-loading span:nth-child(3) {
        animation-delay: 0.4s;
      }

      @keyframes loading {
        0%, 80%, 100% {
          opacity: 0.3;
        }
        40% {
          opacity: 1;
        }
      }

      .chatbot-form {
        display: flex;
        gap: 8px;
        padding: 12px;
        border-top: 1px solid var(--border-color);
        background-color: var(--bg-light);
        border-radius: 0 0 12px 12px;
      }

      .chatbot-input {
        flex: 1;
        border: 1px solid var(--border-color);
        border-radius: 6px;
        padding: 10px 12px;
        font-size: 14px;
        background-color: var(--bg-light);
        color: var(--text-dark);
        outline: none;
        transition: border-color 0.2s;
      }

      .chatbot-input:focus {
        border-color: var(--primary-color);
      }

      .chatbot-input::placeholder {
        color: #999;
      }

      .chatbot-send {
        background-color: var(--primary-color);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 10px 16px;
        cursor: pointer;
        font-size: 14px;
        font-weight: 600;
        transition: background-color 0.2s;
      }

      .chatbot-send:hover {
        background-color: #2a8a8f;
      }

      .chatbot-send:active {
        transform: scale(0.95);
      }

      /* Mobile responsive */
      @media (max-width: 480px) {
        .chatbot-container {
          width: 100vw;
          height: 60vh;
          bottom: 0;
          right: 0;
          border-radius: 12px 12px 0 0;
        }

        .chatbot-toggle {
          bottom: 16px;
          right: 16px;
        }

        .chatbot-message-text {
          max-width: 85%;
        }
      }

      /* Scrollbar styling */
      .chatbot-messages::-webkit-scrollbar {
        width: 6px;
      }

      .chatbot-messages::-webkit-scrollbar-track {
        background: transparent;
      }

      .chatbot-messages::-webkit-scrollbar-thumb {
        background: var(--border-color);
        border-radius: 3px;
      }

      .chatbot-messages::-webkit-scrollbar-thumb:hover {
        background: #999;
      }
    `;
    document.head.appendChild(style);
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      addStyles();
      initChatbot();
    });
  } else {
    addStyles();
    initChatbot();
  }
})();
