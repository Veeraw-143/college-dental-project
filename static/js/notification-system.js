/* ========================================
   MODERN NOTIFICATION SYSTEM - JavaScript
   Clean, accessible, timed notifications
   ======================================== */

class NotificationSystem {
    constructor(options = {}) {
        this.container = null;
        this.notifications = [];
        this.defaultDuration = options.duration || 4000; // 4 seconds
        this.maxNotifications = options.maxNotifications || 5;
        this.position = options.position || 'top-right'; // top-left, top-right, top-center
        
        this.icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };
        
        this.titles = {
            success: 'Success',
            error: 'Error',
            warning: 'Warning',
            info: 'Info'
        };
        
        this.init();
    }
    
    // Initialize container
    init() {
        if (document.getElementById('notification-container')) {
            this.container = document.getElementById('notification-container');
        } else {
            this.container = document.createElement('div');
            this.container.id = 'notification-container';
            this.container.setAttribute('role', 'region');
            this.container.setAttribute('aria-label', 'Notifications');
            this.container.setAttribute('aria-live', 'polite');
            this.container.setAttribute('aria-atomic', 'false');
            document.body.appendChild(this.container);
        }
        
        // Apply position class
        this.container.classList.remove('top-left', 'top-center', 'top-right');
        this.container.classList.add(this.position);
    }
    
    // Show notification
    show(message, type = 'info', title = '', options = {}) {
        // Use type-specific title if not provided
        if (!title && this.titles[type]) {
            title = this.titles[type];
        }
        
        // Merge with default options
        const config = {
            duration: options.duration !== undefined ? options.duration : this.defaultDuration,
            closeable: options.closeable !== undefined ? options.closeable : true,
        };
        
        // Limit notifications
        if (this.notifications.length >= this.maxNotifications) {
            this.notifications[0].remove();
            this.notifications.shift();
        }
        
        // Create notification element
        const notification = this.createNotificationElement(message, type, title, config);
        
        // Add to DOM
        this.container.appendChild(notification);
        this.notifications.push({
            element: notification,
            type: type,
            timeout: null,
            remove: () => this.removeNotification(notification)
        });
        
        // Trigger animation (reflow for animation)
        notification.offsetHeight;
        
        // Auto dismiss if duration > 0
        if (config.duration > 0) {
            if (notification.notificationObj) {
                notification.notificationObj.timeout = setTimeout(() => {
                    this.removeNotification(notification);
                }, config.duration);
            }
        }
        
        return notification;
    }
    
    // Create notification element
    createNotificationElement(message, type, title, config) {
        const div = document.createElement('div');
        div.className = `notification ${type}`;
        div.setAttribute('role', 'alert');
        div.setAttribute('aria-live', 'assertive');
        
        const icon = this.icons[type] || '•';
        
        div.innerHTML = `
            <div class="notification-icon" aria-hidden="true">${icon}</div>
            <div class="notification-content">
                ${title ? `<div class="notification-title">${this.escapeHtml(title)}</div>` : ''}
                <div class="notification-message">${this.escapeHtml(message)}</div>
            </div>
            ${config.closeable ? `<button class="notification-close" aria-label="Close notification" type="button">✕</button>` : ''}
            <div class="notification-progress active" style="animation-duration: ${config.duration}ms;"></div>
        `;
        
        // Store reference to this notification
        const notificationObj = {
            element: div,
            type: type,
            timeout: null,
            config: config
        };
        div.notificationObj = notificationObj;
        
        // Close button event
        if (config.closeable) {
            const closeBtn = div.querySelector('.notification-close');
            closeBtn.addEventListener('click', () => {
                this.removeNotification(div);
            });
        }
        
        // Clear timeout on hover (keep visible while reading)
        div.addEventListener('mouseenter', () => {
            if (notificationObj.timeout) {
                clearTimeout(notificationObj.timeout);
            }
            const progress = div.querySelector('.notification-progress');
            if (progress) {
                progress.style.animationPlayState = 'paused';
            }
        });
        
        // Resume timeout on mouse leave
        div.addEventListener('mouseleave', () => {
            if (config.duration > 0) {
                const progress = div.querySelector('.notification-progress');
                if (progress) {
                    progress.style.animationPlayState = 'running';
                }
                notificationObj.timeout = setTimeout(() => {
                    this.removeNotification(div);
                }, config.duration);
            }
        });
        
        return div;
    }
    
    // Remove notification
    removeNotification(notification) {
        notification.classList.add('exiting');
        
        setTimeout(() => {
            if (notification.notificationObj && notification.notificationObj.timeout) {
                clearTimeout(notification.notificationObj.timeout);
            }
            
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
            
            // Remove from tracking array
            this.notifications = this.notifications.filter(n => n.element !== notification);
        }, 300); // Match animation duration
    }
    
    // Success notification
    success(message, title = '', options = {}) {
        return this.show(message, 'success', title || 'Success', options);
    }
    
    // Error notification
    error(message, title = '', options = {}) {
        return this.show(message, 'error', title || 'Error', options);
    }
    
    // Warning notification
    warning(message, title = '', options = {}) {
        return this.show(message, 'warning', title || 'Warning', options);
    }
    
    // Info notification
    info(message, title = '', options = {}) {
        return this.show(message, 'info', title || 'Info', options);
    }
    
    // Close all notifications
    closeAll() {
        const notificationsCopy = [...this.notifications];
        notificationsCopy.forEach(n => {
            this.removeNotification(n.element);
        });
    }
    
    // Escape HTML to prevent XSS
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return String(text).replace(/[&<>"']/g, m => map[m]);
    }
}

// Initialize global notification system
let Notify = null;

document.addEventListener('DOMContentLoaded', () => {
    // Create global notification instance
    Notify = new NotificationSystem({
        duration: 4000,
        maxNotifications: 5,
        position: 'top-right'
    });
    
    // Make available globally
    window.Notify = Notify;
});

// Helper functions for backward compatibility
function showNotification(message, type = 'info', title = '', duration = 5000) {
    if (Notify) {
        return Notify.show(message, type, title, { duration });
    }
}

function showSuccess(message, title = '') {
    if (Notify) {
        return Notify.success(message, title);
    }
}

function showError(message, title = '') {
    if (Notify) {
        return Notify.error(message, title);
    }
}

function showWarning(message, title = '') {
    if (Notify) {
        return Notify.warning(message, title);
    }
}

function showInfo(message, title = '') {
    if (Notify) {
        return Notify.info(message, title);
    }
}

// Make helper functions globally available
window.showNotification = showNotification;
window.showSuccess = showSuccess;
window.showError = showError;
window.showWarning = showWarning;
window.showInfo = showInfo;
