// Authentication Utilities

/**
 * Checks if the user is currently authenticated (has a token).
 * Redirects to login page if validation fails and redirectUrl is provided.
 */
function checkAuth(redirectUrl = 'login.html') {
    const token = sessionStorage.getItem("access_token");
    if (!token) {
        if (redirectUrl) window.location.href = redirectUrl;
        return false;
    }
    return true;
}

/**
 * Perform login and store tokens.
 * @param {string} username 
 * @param {string} password 
 * @returns {Promise<void>}
 */
async function loginUser(username, password) {
    // Fallback to current origin (relative) for Nginx proxy, or localhost for local testing
    const baseUrl = window.API_BASE_URL || "";
    console.log("Attempting login to:", baseUrl);

    // Use JSON-based login endpoint to avoid form parsing conflicts
    const response = await fetch(`${baseUrl}/auth/login-json`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
        let msg = "Login failed";
        try {
            const errorData = await response.json();
            msg = errorData.detail || JSON.stringify(errorData) || msg;
        } catch (err) {
            try {
                const text = await response.text();
                msg = text || msg;
            } catch (ignore) { }
        }
        throw new Error(msg);
    }

    const data = await response.json();
    sessionStorage.setItem("access_token", data.access_token);
    sessionStorage.setItem("user_id", data.id); // Assuming backend returns ID
    sessionStorage.setItem("token_type", data.token_type);
}

/**
 * Logout the user by clearing session and redirecting.
 */
function logoutUser() {
    sessionStorage.clear();
    window.location.href = "login.html";
}

/**
 * Get HTTP headers for authenticated requests.
 * @returns {Object} Headers object with Authorization
 */
function getAuthHeaders() {
    const token = sessionStorage.getItem("access_token");
    if (!token) return {};
    return { Authorization: `Bearer ${token}` };
}

/**
 * Fetch wrapper that automatically adds Auth headers.
 * @param {string} url 
 * @param {Object} options 
 */
async function fetchWithAuth(url, options = {}) {
    options.headers = options.headers || {};

    // Add Auth header
    const authHeaders = getAuthHeaders();
    Object.assign(options.headers, authHeaders);

    // Default to JSON content type if body exists and not specified
    if (options.body && !options.headers["Content-Type"]) {
        // Simple check; logic can be expanded if needed
        options.headers["Content-Type"] = "application/json";
    }

    const response = await fetch(url, options);

    // Handle 401 Unauthorized globally
    if (response.status === 401) {
        console.warn("Unauthorized request, redirecting to login...");
        logoutUser();
    }

    return response;
}
