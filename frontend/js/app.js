const API_URL = CONFIG.API_URL; // Loaded from config.js

// --- State ---
let currentUser = JSON.parse(localStorage.getItem('user')) || null;
let currentToken = localStorage.getItem('token') || null;
let currentGroup = null;

// --- Auth Helpers ---
const headers = () => {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${currentUser?.id}` // Using ID as token based on our mock auth
    };
};

const checkAuth = () => {
    if (!currentUser && !window.location.pathname.endsWith('index.html')) {
        window.location.href = 'index.html';
    }
};

// --- API Client ---
const api = {
    login: async (email, password) => {
        const res = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ username: email, password: password })
        });
        if (!res.ok) throw await res.json();
        return res.json();
    },

    signup: async (email, password) => {
        const res = await fetch(`${API_URL}/auth/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        if (!res.ok) throw await res.json();
        return res.json();
    },

    getGroups: async () => {
        const res = await fetch(`${API_URL}/groups`, { headers: headers() });
        if (!res.ok) throw await res.json();
        return res.json();
    },

    createGroup: async (title, days) => {
        const res = await fetch(`${API_URL}/groups`, {
            method: 'POST',
            headers: headers(),
            body: JSON.stringify({ title, expires_in_days: parseInt(days) })
        });
        if (!res.ok) throw await res.json();
        return res.json();
    },

    joinGroup: async (code) => {
        const res = await fetch(`${API_URL}/groups/join`, {
            method: 'POST',
            headers: headers(),
            body: JSON.stringify({ code })
        });
        if (!res.ok) throw await res.json();
        return res.json();
    },

    getGroupDetails: async (id) => {
        const res = await fetch(`${API_URL}/groups/${id}`, { headers: headers() });
        if (!res.ok) throw await res.json();
        return res.json();
    },

    extendGroup: async (id, days) => {
        const res = await fetch(`${API_URL}/groups/${id}/extend`, {
            method: 'POST',
            headers: headers(),
            body: JSON.stringify({ extend_days: parseInt(days) })
        });
        if (!res.ok) throw await res.json();
        return res.json();
    },

    getPhotos: async (groupId) => {
        const res = await fetch(`${API_URL}/photos/groups/${groupId}`, { headers: headers() });
        if (!res.ok) throw await res.json();
        return res.json();
    },

    getSignedUrls: async (photoIds) => {
        const res = await fetch(`${API_URL}/photos/signed-urls`, {
            method: 'POST',
            headers: headers(),
            body: JSON.stringify({ photo_ids: photoIds, expires_in_seconds: 3600 })
        });
        if (!res.ok) throw await res.json();
        return res.json();
    },

    uploadPhoto: async (groupId, file) => {
        const formData = new FormData();
        formData.append('group_id', groupId);
        formData.append('file', file);

        const res = await fetch(`${API_URL}/photos/upload`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${currentUser?.id}` }, // No Content-Type for FormData
            body: formData
        });
        if (!res.ok) throw await res.json();
        return res.json();
    }
};

// --- UI Helpers ---
const showToast = (msg, type = 'info') => {
    // Basic alert for now, can enhance
    alert(msg);
};

// --- Exports (for attaching to window) ---
window.app = {
    api,
    state: { currentUser, currentGroup },
    login: async (e) => {
        e.preventDefault();
        const email = e.target.email.value;
        const password = e.target.password.value;
        try {
            const data = await api.login(email, password);
            // Mock Auth wraps user in user field? No, oauth returns token
            // Our mock auth login returns { access_token, token_type, user: {...} }
            // Let's assume standard oauth response + user data

            // Adjust based on actual backend auth response
            // Looking at auth.py/login_for_access_token:
            // returns {"access_token": user.id, "token_type": "bearer", "user": ...}

            localStorage.setItem('token', data.access_token);
            localStorage.setItem('user', JSON.stringify(data.user));
            window.location.href = 'dashboard.html';
        } catch (err) {
            showToast(err?.detail || err?.message || "Login failed", 'error');
        }
    },
    logout: () => {
        localStorage.clear();
        window.location.href = 'index.html';
    }
};
