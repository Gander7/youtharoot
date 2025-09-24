// API Configuration
const API_BASE_URL = import.meta.env.PUBLIC_API_URL || 
  (typeof window !== 'undefined' && window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : 'https://your-app-name.up.railway.app');

export { API_BASE_URL };