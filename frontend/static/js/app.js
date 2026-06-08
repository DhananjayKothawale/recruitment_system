// ============================================================
// frontend/static/js/app.js
// PURPOSE: Shared JavaScript utilities used across ALL pages.
//
// WHAT'S IN HERE:
// 1. API helper functions (so we don't repeat fetch() everywhere)
// 2. Auth helpers (save/read JWT token)
// 3. Toast notification system
// 4. Dark/Light mode toggle
// 5. Utility functions
// ============================================================

// ---- API BASE URL ----
// Change this if your backend runs on a different port
const API_BASE = "http://localhost:8000";

// ============================================================
// AUTH HELPERS
// JWT token is stored in localStorage (browser storage)
// ============================================================

const Auth = {
    // Save token after login
    setToken(token) {
        localStorage.setItem("access_token", token);
    },

    // Get saved token
    getToken() {
        return localStorage.getItem("access_token");
    },

    // Save user info after login
    setUser(user) {
        localStorage.setItem("user_info", JSON.stringify(user));
    },

    // Get saved user info
    getUser() {
        const info = localStorage.getItem("user_info");
        return info ? JSON.parse(info) : null;
    },

    // Check if user is logged in
    isLoggedIn() {
        return !!this.getToken();
    },

    // Clear everything on logout
    logout() {
        localStorage.removeItem("access_token");
        localStorage.removeItem("user_info");
        window.location.href = "/login";
    },

    // Redirect to login if not authenticated
    requireAuth() {
        if (!this.isLoggedIn()) {
            window.location.href = "/login";
            return false;
        }
        return true;
    },

    // Require a specific role
    requireRole(role) {
        const user = this.getUser();
        if (!user || user.role !== role) {
            Toast.show("Access denied. Insufficient permissions.", "error");
            setTimeout(() => window.location.href = "/dashboard", 1500);
            return false;
        }
        return true;
    }
};

// ============================================================
// API HELPER
// Wraps fetch() so we always include the JWT token
// and handle errors consistently
// ============================================================

const API = {
    // GET request
    async get(endpoint) {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: "GET",
            headers: this._headers(),
        });
        return this._handle(response);
    },

    // POST request with JSON body
    async post(endpoint, data) {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: "POST",
            headers: this._headers(),
            body: JSON.stringify(data),
        });
        return this._handle(response);
    },

    // POST with form data (for login - uses OAuth2PasswordRequestForm)
    async postForm(endpoint, formData) {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: "POST",
            headers: {
                // Don't set Content-Type for FormData - browser does it automatically
                ...(Auth.getToken() && { "Authorization": `Bearer ${Auth.getToken()}` }),
            },
            body: formData,
        });
        return this._handle(response);
    },

    // POST with file upload
    async uploadFile(endpoint, file) {
        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: "POST",
            headers: {
                ...(Auth.getToken() && { "Authorization": `Bearer ${Auth.getToken()}` }),
            },
            body: formData,
        });
        return this._handle(response);
    },

    // PUT request
    async put(endpoint, data) {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: "PUT",
            headers: this._headers(),
            body: JSON.stringify(data),
        });
        return this._handle(response);
    },

    // DELETE request
    async delete(endpoint) {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: "DELETE",
            headers: this._headers(),
        });
        return this._handle(response);
    },

    // Build headers with JWT token
    _headers() {
        const headers = { "Content-Type": "application/json" };
        const token = Auth.getToken();
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }
        return headers;
    },

    // Handle response - throw error if not OK
    async _handle(response) {
        if (response.status === 401) {
            Auth.logout();
            return;
        }
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "Something went wrong");
        }
        return data;
    }
};

// ============================================================
// TOAST NOTIFICATIONS
// Small pop-up messages (success/error/info)
// ============================================================

const Toast = {
    container: null,

    init() {
        if (!this.container) {
            this.container = document.createElement("div");
            this.container.className = "toast-container";
            document.body.appendChild(this.container);
        }
    },

    show(message, type = "info", duration = 3000) {
        this.init();

        const icons = { success: "✅", error: "❌", info: "ℹ️" };
        const toast = document.createElement("div");
        toast.className = `toast ${type}`;
        toast.innerHTML = `<span>${icons[type]}</span><span>${message}</span>`;

        this.container.appendChild(toast);

        // Auto-remove after duration
        setTimeout(() => {
            toast.style.opacity = "0";
            toast.style.transform = "translateX(100%)";
            toast.style.transition = "all 0.3s ease";
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
};

// ============================================================
// DARK / LIGHT MODE
// ============================================================

const Theme = {
    init() {
        // Load saved preference (default: light)
        const saved = localStorage.getItem("theme") || "light";
        this.apply(saved);
    },

    toggle() {
        const current = document.documentElement.getAttribute("data-theme");
        const next = current === "dark" ? "light" : "dark";
        this.apply(next);
    },

    apply(theme) {
        document.documentElement.setAttribute("data-theme", theme);
        localStorage.setItem("theme", theme);
        // Update toggle button emoji
        const btn = document.getElementById("theme-toggle");
        if (btn) btn.textContent = theme === "dark" ? "☀️" : "🌙";
    }
};

// ============================================================
// UTILITY FUNCTIONS
// ============================================================

// Format a number to show score color
function getScoreColor(score) {
    if (score >= 80) return "score-excellent";
    if (score >= 60) return "score-good";
    if (score >= 40) return "score-average";
    return "score-poor";
}

// Render a score bar HTML
function renderScoreBar(score, label = "") {
    const colorClass = getScoreColor(score);
    return `
        <div class="score-bar-container">
            ${label ? `<span style="font-size:0.8rem;color:var(--text-secondary);width:120px">${label}</span>` : ""}
            <div class="score-bar">
                <div class="score-bar-fill ${colorClass}" style="width:${score}%"></div>
            </div>
            <span class="score-value ${colorClass}">${score.toFixed(0)}%</span>
        </div>
    `;
}

// Format date to readable string
function formatDate(dateStr) {
    if (!dateStr) return "N/A";
    return new Date(dateStr).toLocaleDateString("en-IN", {
        day: "numeric", month: "short", year: "numeric"
    });
}

// Show loading spinner in a container
function showLoading(container) {
    container.innerHTML = `<div style="padding:40px;text-align:center"><div class="spinner"></div><p style="color:var(--text-secondary);margin-top:12px">Loading...</p></div>`;
}

// Fill user info in header
function initUserHeader() {
    const user = Auth.getUser();
    if (!user) return;
    const nameEl = document.getElementById("user-name");
    const roleEl = document.getElementById("user-role");
    if (nameEl) nameEl.textContent = user.full_name || user.email;
    if (roleEl) roleEl.textContent = user.role?.charAt(0).toUpperCase() + user.role?.slice(1);
}

// ============================================================
// INIT ON PAGE LOAD
// ============================================================
document.addEventListener("DOMContentLoaded", () => {
    Theme.init();
    initUserHeader();

    // Theme toggle button
    const themeBtn = document.getElementById("theme-toggle");
    if (themeBtn) themeBtn.addEventListener("click", () => Theme.toggle());

    // Logout button
    const logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn) logoutBtn.addEventListener("click", () => Auth.logout());

    // Mark active nav item
    const currentPath = window.location.pathname;
    document.querySelectorAll(".nav-item").forEach(item => {
        if (item.getAttribute("href") === currentPath) {
            item.classList.add("active");
        }
    });
});
