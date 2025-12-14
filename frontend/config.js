const CONFIG = {
    // Check if we are in a browser environment that supports window.env (classic approach)
    // or just default to localhost if not set.
    // For Vercel/Netlify, we often inject these during build or via a script tag.
    API_URL: 'https://tripshare-9pif.onrender.com'
};

// Allow overriding via global object if needed (e.g. env.js injected at runtime)
if (window.env && window.env.API_URL) {
    CONFIG.API_URL = window.env.API_URL;
}
