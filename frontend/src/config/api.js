// API Configuration
const getApiBaseUrl = () => {
  // Check for environment variable first (production)
  if (import.meta.env.PUBLIC_API_URL) {
    console.log('Using PUBLIC_API_URL:', import.meta.env.PUBLIC_API_URL);
    return import.meta.env.PUBLIC_API_URL;
  }
  
  // Fallback
  console.log('Using localhost API URL');
  return 'http://localhost:8000';
};

export const API_BASE_URL = getApiBaseUrl();
console.log('Final API_BASE_URL:', API_BASE_URL);

// Helper function to get auth token
const getAuthToken = () => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('auth_token');
  }
  return null;
};

// API request helper with authentication
export const apiRequest = async (endpoint, options = {}) => {
  const token = getAuthToken();
  
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...options.headers,
    },
    ...options,
  };

  if (options.body && typeof options.body !== 'string') {
    config.body = JSON.stringify(options.body);
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(errorData.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
};