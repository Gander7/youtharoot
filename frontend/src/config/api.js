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