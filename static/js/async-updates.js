/**
 * Async Real-Time Data Updates
 * Polling-based system for live data updates without WebSockets
 * Supports graceful fallback if async fails
 */

class AsyncDataUpdater {
    constructor(config = {}) {
        this.endpoints = {
            bookings: '/api/bookings/updates/',
            otp: '/api/otp/status/',
            dashboard: '/api/dashboard/stats/',
            subscribe: '/api/subscribe/updates/'
        };
        
        this.config = {
            pollingInterval: config.pollingInterval || 5000,  // 5 seconds
            maxRetries: config.maxRetries || 3,
            retryDelay: config.retryDelay || 1000,
            enableLogger: config.enableLogger || false,
            autoStart: config.autoStart || true,
            ...config
        };
        
        this.isRunning = false;
        this.retryCount = {};
        this.timers = {};
        this.callbacks = {};
        this.cache = {};
    }
    
    /**
     * Log messages for debugging
     */
    log(message, data = null) {
        if (!this.config.enableLogger) return;
        console.log(`[AsyncUpdater] ${message}`, data);
    }
    
    /**
     * Add callback for update type
     */
    onUpdate(updateType, callback) {
        if (!this.callbacks[updateType]) {
            this.callbacks[updateType] = [];
        }
        this.callbacks[updateType].push(callback);
        this.log(`Callback registered for: ${updateType}`);
    }
    
    /**
     * Remove callback
     */
    offUpdate(updateType, callback) {
        if (this.callbacks[updateType]) {
            this.callbacks[updateType] = this.callbacks[updateType].filter(cb => cb !== callback);
        }
    }
    
    /**
     * Trigger callbacks
     */
    triggerCallbacks(updateType, data) {
        const callbacks = this.callbacks[updateType] || [];
        callbacks.forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error(`Error in callback for ${updateType}:`, error);
            }
        });
    }
    
    /**
     * Fetch with retry logic
     */
    async fetchWithRetry(url, maxRetries = this.config.maxRetries) {
        let lastError;
        
        for (let i = 0; i < maxRetries; i++) {
            try {
                const response = await fetch(url, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    cache: 'no-cache'
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const data = await response.json();
                this.retryCount[url] = 0;
                return data;
            } catch (error) {
                lastError = error;
                this.log(`Fetch attempt ${i + 1} failed for ${url}`, error.message);
                
                if (i < maxRetries - 1) {
                    await new Promise(resolve => 
                        setTimeout(resolve, this.config.retryDelay * (i + 1))
                    );
                }
            }
        }
        
        throw lastError;
    }
    
    /**
     * Start polling for booking updates
     */
    startBookingUpdates() {
        if (this.timers.bookings) return;
        
        const poll = async () => {
            try {
                const data = await this.fetchWithRetry(this.endpoints.bookings);
                
                if (data.success) {
                    // Check if data changed
                    const cacheKey = 'bookings';
                    const dataHash = JSON.stringify(data.stats);
                    
                    if (this.cache[cacheKey] !== dataHash) {
                        this.cache[cacheKey] = dataHash;
                        this.triggerCallbacks('bookings', data.stats);
                        this.log('Booking update received', data.stats);
                    }
                }
            } catch (error) {
                console.error('Booking update failed:', error);
                this.triggerCallbacks('bookings:error', error);
            }
            
            this.timers.bookings = setTimeout(poll, this.config.pollingInterval);
        };
        
        poll();
        this.log('Booking updates started');
    }
    
    /**
     * Start polling for OTP status
     */
    startOTPUpdates() {
        if (this.timers.otp) return;
        
        const poll = async () => {
            try {
                const data = await this.fetchWithRetry(this.endpoints.otp);
                
                if (data.success) {
                    const cacheKey = 'otp';
                    const dataHash = JSON.stringify(data.otp_stats);
                    
                    if (this.cache[cacheKey] !== dataHash) {
                        this.cache[cacheKey] = dataHash;
                        this.triggerCallbacks('otp', data.otp_stats);
                        this.log('OTP update received', data.otp_stats);
                    }
                }
            } catch (error) {
                console.error('OTP update failed:', error);
                this.triggerCallbacks('otp:error', error);
            }
            
            this.timers.otp = setTimeout(poll, this.config.pollingInterval);
        };
        
        poll();
        this.log('OTP updates started');
    }
    
    /**
     * Start polling for dashboard statistics
     */
    startDashboardUpdates() {
        if (this.timers.dashboard) return;
        
        const poll = async () => {
            try {
                const data = await this.fetchWithRetry(this.endpoints.dashboard);
                
                if (data.success) {
                    const cacheKey = 'dashboard';
                    const dataHash = JSON.stringify(data);
                    
                    if (this.cache[cacheKey] !== dataHash) {
                        this.cache[cacheKey] = dataHash;
                        this.triggerCallbacks('dashboard', data);
                        this.log('Dashboard update received');
                    }
                }
            } catch (error) {
                console.error('Dashboard update failed:', error);
                this.triggerCallbacks('dashboard:error', error);
            }
            
            this.timers.dashboard = setTimeout(poll, this.config.pollingInterval);
        };
        
        poll();
        this.log('Dashboard updates started');
    }
    
    /**
     * Update specific booking status
     */
    async getBookingDetail(bookingId) {
        try {
            const url = `/api/booking/${bookingId}/details/`;
            return await this.fetchWithRetry(url);
        } catch (error) {
            console.error(`Failed to get booking ${bookingId} details:`, error);
            throw error;
        }
    }
    
    /**
     * Check OTP verification status
     */
    async checkOTPStatus(email) {
        try {
            const url = `/api/otp/${encodeURIComponent(email)}/status/`;
            return await this.fetchWithRetry(url);
        } catch (error) {
            console.error(`Failed to get OTP status for ${email}:`, error);
            throw error;
        }
    }
    
    /**
     * Stop specific update type
     */
    stop(updateType = 'all') {
        if (updateType === 'all') {
            Object.keys(this.timers).forEach(key => {
                clearTimeout(this.timers[key]);
                delete this.timers[key];
            });
            this.log('All updates stopped');
        } else {
            if (this.timers[updateType]) {
                clearTimeout(this.timers[updateType]);
                delete this.timers[updateType];
                this.log(`${updateType} updates stopped`);
            }
        }
    }
    
    /**
     * Start all updates
     */
    startAll() {
        this.startBookingUpdates();
        this.startOTPUpdates();
        this.startDashboardUpdates();
        this.isRunning = true;
    }
    
    /**
     * Get current cache value
     */
    getCache(key) {
        return this.cache[key] || null;
    }
    
    /**
     * Clear cache
     */
    clearCache() {
        this.cache = {};
        this.log('Cache cleared');
    }
}

/**
 * Global instance for easy access
 */
window.asyncUpdater = null;

/**
 * Initialize async updater on DOM ready
 */
document.addEventListener('DOMContentLoaded', function() {
    // Create global updater instance
    window.asyncUpdater = new AsyncDataUpdater({
        pollingInterval: 5000,  // 5 seconds
        enableLogger: false,    // Set to true for debugging
        autoStart: true
    });
    
    // Only auto-start on admin pages
    const isAdminPage = document.body.classList.contains('admin-page') || 
                       window.location.pathname.includes('/admin');
    
    if (isAdminPage) {
        // Start updates on admin pages
        setTimeout(() => {
            window.asyncUpdater.startAll();
        }, 1000);
    }
});

/**
 * Helper function to update UI element with data
 */
function updateElement(elementId, data, formatter = null) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const value = formatter ? formatter(data) : data;
    
    // Fade out, update, fade in
    element.style.opacity = '0.5';
    element.innerHTML = value;
    
    setTimeout(() => {
        element.style.opacity = '1';
        element.style.transition = 'opacity 0.3s ease';
    }, 50);
}

/**
 * Example usage in HTML:
 * 
 * <div id="pending-count">0</div>
 * 
 * <script>
 * window.asyncUpdater.onUpdate('bookings', function(stats) {
 *     updateElement('pending-count', stats.pending);
 * });
 * </script>
 */

/**
 * Real-time OTP verification check
 */
async function checkAndUpdateOTPFields(emailInput) {
    const email = emailInput.value.trim();
    if (!email) return;
    
    try {
        const data = await window.asyncUpdater.checkOTPStatus(email);
        
        if (data.is_verified) {
            // Email is already verified
            const otpSection = document.getElementById('otp-section');
            if (otpSection) {
                otpSection.style.opacity = '0.5';
                otpSection.innerHTML = '<div style="color: #4caf50; padding: 15px; background: #e8f5e9; border-radius: 6px;">✓ Email already verified</div>';
                document.getElementById('otp_verified').value = 'true';
            }
        }
    } catch (error) {
        console.info('OTP check: ', error.message);  // Soft fail
    }
}

/**
 * Poll for booking status after submission
 */
function pollBookingStatus(bookingId, maxAttempts = 30) {
    let attempts = 0;
    
    const pollInterval = setInterval(async () => {
        attempts++;
        
        if (attempts > maxAttempts) {
            clearInterval(pollInterval);
            return;
        }
        
        try {
            const data = await window.asyncUpdater.getBookingDetail(bookingId);
            
            if (data.success) {
                const booking = data.booking;
                
                // Update UI based on status
                if (booking.status === 'accepted') {
                    clearInterval(pollInterval);
                    showNotification('✓ Your appointment has been accepted!', 'success');
                } else if (booking.status === 'rejected') {
                    clearInterval(pollInterval);
                    showNotification('✗ Your appointment was not available', 'error');
                }
            }
        } catch (error) {
            // Silently fail if booking not found
        }
    }, 3000);  // Poll every 3 seconds
}

/**
 * Show notification helper
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 6px;
        background: ${type === 'success' ? '#4caf50' : type === 'error' ? '#f44336' : '#2196f3'};
        color: white;
        z-index: 5000;
        animation: slideIn 0.3s ease;
    `;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 4000);
}
