/**
 * Utility mixin for common Vue component functionality
 * Provides helper methods and computed properties used across components
 */
export default {
  methods: {
    /**
     * Format date to locale string
     * @param {Date|string} date - Date to format
     * @returns {string} Formatted date string
     */
    formatDate(date) {
      if (!date) return '';
      const dateObj = date instanceof Date ? date : new Date(date);
      return dateObj.toLocaleDateString();
    },

    /**
     * Format date and time to locale string
     * @param {Date|string} datetime - DateTime to format
     * @returns {string} Formatted datetime string
     */
    formatDateTime(datetime) {
      if (!datetime) return '';
      const dateObj = datetime instanceof Date ? datetime : new Date(datetime);
      return dateObj.toLocaleString();
    },

    /**
     * Truncate text to specified length
     * @param {string} text - Text to truncate
     * @param {number} length - Maximum length (default: 50)
     * @returns {string} Truncated text with ellipsis if needed
     */
    truncateText(text, length = 50) {
      if (!text) return '';
      return text.length > length ? text.substring(0, length) + '...' : text;
    },

    /**
     * Validate email format
     * @param {string} email - Email to validate
     * @returns {boolean} True if valid email format
     */
    isValidEmail(email) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return emailRegex.test(email);
    },

    /**
     * Validate URL format
     * @param {string} url - URL to validate
     * @returns {boolean} True if valid URL format
     */
    isValidUrl(url) {
      try {
        new URL(url);
        return true;
      } catch {
        return false;
      }
    },

    /**
     * Deep clone an object
     * @param {any} obj - Object to clone
     * @returns {any} Deep cloned object
     */
    deepClone(obj) {
      return JSON.parse(JSON.stringify(obj));
    },

    /**
     * Debounce function execution
     * @param {Function} func - Function to debounce
     * @param {number} delay - Delay in milliseconds
     * @returns {Function} Debounced function
     */
    debounce(func, delay) {
      let timeoutId;
      return (...args) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
      };
    },

    /**
     * Show success notification
     * @param {string} message - Success message
     */
    showSuccess(message) {
      // Using Carbon Design System notification pattern
      this.$root.$emit('notification', {
        type: 'success',
        title: this.$t('success'),
        message: message,
        timeout: 3000
      });
    },

    /**
     * Show error notification
     * @param {string} message - Error message
     */
    showError(message) {
      this.$root.$emit('notification', {
        type: 'error',
        title: this.$t('error'),
        message: message,
        timeout: 5000
      });
    },

    /**
     * Show info notification
     * @param {string} message - Info message
     */
    showInfo(message) {
      this.$root.$emit('notification', {
        type: 'info',
        title: this.$t('info'),
        message: message,
        timeout: 4000
      });
    },

    /**
     * Convert bytes to human readable format
     * @param {number} bytes - Number of bytes
     * @returns {string} Human readable size
     */
    formatBytes(bytes) {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
  },

  computed: {
    /**
     * Check if current environment is development
     * @returns {boolean} True if in development mode
     */
    isDevelopment() {
      return process.env.NODE_ENV === 'development';
    },

    /**
     * Get current timestamp
     * @returns {number} Current timestamp
     */
    currentTimestamp() {
      return Date.now();
    }
  }
};
