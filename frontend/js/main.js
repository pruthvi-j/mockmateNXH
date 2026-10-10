/**
 * NextHire - Main Frontend Application Logic
 * Shared utilities, API client, and toast notifications.
 */

const API_BASE = '/api';

const NextHire = {
  /**
   * Display a sleek futuristic toast notification.
   */
  showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.style.cssText = `
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 9999;
        display: flex;
        flex-direction: column;
        gap: 10px;
        pointer-events: none;
      `;
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    const colors = {
      info: { border: '#00e5ff', bg: 'rgba(6, 14, 34, 0.9)', color: '#00e5ff' },
      success: { border: '#00f5a0', bg: 'rgba(6, 24, 20, 0.9)', color: '#00f5a0' },
      error: { border: '#ff3366', bg: 'rgba(30, 8, 16, 0.9)', color: '#ff6685' },
      warning: { border: '#ffb703', bg: 'rgba(28, 20, 6, 0.9)', color: '#ffb703' }
    };
    const c = colors[type] || colors.info;

    toast.style.cssText = `
      padding: 12px 20px;
      border-radius: 10px;
      background: ${c.bg};
      border: 1px solid ${c.border};
      color: #ffffff;
      font-size: 0.9rem;
      backdrop-filter: blur(12px);
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
      opacity: 0;
      transform: translateY(12px);
      transition: all 0.3s ease;
      pointer-events: auto;
      max-width: 380px;
      line-height: 1.4;
    `;
    toast.innerHTML = `<strong style="color:${c.color}; text-transform:uppercase; font-size:0.75rem; letter-spacing:0.5px; display:block; margin-bottom:2px;">[${type.toUpperCase()}]</strong> ${message}`;

    container.appendChild(toast);
    requestAnimationFrame(() => {
      toast.style.opacity = '1';
      toast.style.transform = 'translateY(0)';
    });

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 350);
    }, 3800);
  },

  /**
   * Check backend server health.
   */
  async checkHealth() {
    try {
      const res = await fetch(`${API_BASE}/health`);
      return await res.json();
    } catch (e) {
      console.warn('Backend offline or unreachable:', e);
      return null;
    }
  },

  /**
   * Validates if email follows the strict Gmail format (username@gmail.com).
   * Domain must be exactly 'gmail.com'. No whitespace allowed.
   */
  isValidGmail(email) {
    if (!email || typeof email !== 'string') return false;
    const trimmed = email.trim();
    if (trimmed !== email || /\s/.test(trimmed)) return false;
    const gmailRegex = /^[a-zA-Z0-9._%+-]+@gmail\.com$/i;
    return gmailRegex.test(trimmed);
  },

  /**
   * Updates real-time visual validation indicators (green tick / red outline & popup message).
   */
  validateGmailInput(inputElement, iconElement, msgElement) {
    if (!inputElement) return false;
    const value = inputElement.value;

    if (!value || value.trim() === '') {
      inputElement.classList.remove('is-valid', 'is-invalid');
      if (iconElement) {
        iconElement.className = 'validation-icon';
        iconElement.style.display = 'none';
        iconElement.innerHTML = '';
      }
      if (msgElement) {
        msgElement.className = 'validation-message';
        msgElement.style.display = 'none';
        msgElement.innerHTML = '';
      }
      return false;
    }

    const valid = NextHire.isValidGmail(value);
    if (valid) {
      inputElement.classList.remove('is-invalid');
      inputElement.classList.add('is-valid');
      if (iconElement) {
        iconElement.className = 'validation-icon valid';
        iconElement.innerHTML = '<i class="fas fa-check-circle"></i>';
        iconElement.style.display = 'inline-flex';
      }
      if (msgElement) {
        msgElement.className = 'validation-message valid';
        msgElement.innerHTML = '<i class="fas fa-check"></i> Valid Gmail ID';
        msgElement.style.display = 'flex';
      }
    } else {
      inputElement.classList.remove('is-valid');
      inputElement.classList.add('is-invalid');
      if (iconElement) {
        iconElement.className = 'validation-icon invalid';
        iconElement.innerHTML = '<i class="fas fa-exclamation-circle"></i>';
        iconElement.style.display = 'inline-flex';
      }
      if (msgElement) {
        msgElement.className = 'validation-message invalid';
        msgElement.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Your email ID is invalid. Please enter a valid Gmail ID.';
        msgElement.style.display = 'flex';
      }
    }
    return valid;
  }
};

window.NextHire = NextHire;

// Initialize Gmail Validation Listeners on Document Ready
document.addEventListener('DOMContentLoaded', () => {
  // Login Form setup
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    const input = document.getElementById('usernameOrEmail');
    const icon = document.getElementById('emailValidationIcon');
    const msg = document.getElementById('emailValidationMsg');

    if (input) {
      ['input', 'blur', 'keyup', 'change'].forEach(evt => {
        input.addEventListener(evt, () => {
          NextHire.validateGmailInput(input, icon, msg);
        });
      });
    }

    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      e.stopPropagation();

      const emailVal = input ? input.value : '';
      const isValid = NextHire.validateGmailInput(input, icon, msg);

      if (!isValid) {
        NextHire.showToast('Your email ID is invalid. Please enter a valid Gmail ID.', 'error');
        return false;
      }

      const passwordInput = document.getElementById('password');
      const passwordVal = passwordInput ? passwordInput.value : '';

      try {
        const response = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            usernameOrEmail: emailVal,
            password: passwordVal
          })
        });

        const data = await response.json();
        if (response.ok && data.success) {
          NextHire.showToast('Login successful! Redirecting...', 'success');
          setTimeout(() => {
            window.location.href = data.redirect || '/dashboard';
          }, 800);
        } else {
          NextHire.showToast(data.error || 'Authentication failed.', 'error');
        }
      } catch (err) {
        console.error('Login submit error:', err);
        // Fallback for offline/mock navigation
        window.location.href = '/dashboard';
      }
    });
  }

  // Register Form setup
  const registerForm = document.getElementById('registerForm');
  if (registerForm) {
    const input = document.getElementById('email');
    const icon = document.getElementById('emailValidationIcon');
    const msg = document.getElementById('emailValidationMsg');

    if (input) {
      ['input', 'blur', 'keyup', 'change'].forEach(evt => {
        input.addEventListener(evt, () => {
          NextHire.validateGmailInput(input, icon, msg);
        });
      });
    }

    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      e.stopPropagation();

      const emailVal = input ? input.value : '';
      const isValid = NextHire.validateGmailInput(input, icon, msg);

      if (!isValid) {
        NextHire.showToast('Your email ID is invalid. Please enter a valid Gmail ID.', 'error');
        return false;
      }

      const usernameInput = document.getElementById('username');
      const passwordInput = document.getElementById('password');
      const targetRoleInput = document.getElementById('targetRole');

      try {
        const response = await fetch('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username: usernameInput ? usernameInput.value : '',
            email: emailVal,
            password: passwordInput ? passwordInput.value : '',
            target_role: targetRoleInput ? targetRoleInput.value : ''
          })
        });

        const data = await response.json();
        if (response.ok && data.success) {
          NextHire.showToast('Registration successful! Redirecting to login...', 'success');
          setTimeout(() => {
            window.location.href = data.redirect || '/login';
          }, 800);
        } else {
          NextHire.showToast(data.error || 'Registration failed.', 'error');
        }
      } catch (err) {
        console.error('Register submit error:', err);
        // Fallback for offline/mock navigation
        window.location.href = '/login';
      }
    });
  }
});

