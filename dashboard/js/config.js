// API Configuration
// In production, Nginx serves both frontend and proxies backend on same port (80).
// Using window.location.origin ensures requests go to the correct host/port.
window.API_BASE_URL = window.location.origin;

console.log("Config loaded, API_BASE_URL:", window.API_BASE_URL);
