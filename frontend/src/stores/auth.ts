/**
 * Authentication state management using nanostores
 */
import { atom, map } from 'nanostores';

// Type definitions
export interface User {
  id: number;
  username: string;
  role: string;
  created_at: string;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
}

// Auth state store
export const authStore = map<AuthState>({
  isAuthenticated: false,
  user: null,
  token: null,
});

// Loading state for auth operations
export const authLoading = atom(false);

// Error state for auth operations
export const authError = atom<string | null>(null);

// API base URL
const API_BASE_URL = import.meta.env.PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Initialize auth state from localStorage on app start
 */
export function initAuth() {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('auth_token');
    const userStr = localStorage.getItem('auth_user');
    
    if (token && userStr) {
      try {
        const user = JSON.parse(userStr);
        authStore.set({
          isAuthenticated: true,
          user,
          token,
        });
      } catch (error) {
        // Invalid data in localStorage, clear it
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
      }
    }
  }
}

/**
 * Login with username and password
 */
export async function login(username: string, password: string): Promise<boolean> {
  authLoading.set(true);
  authError.set(null);

  try {
    const response = await fetch(`${API_BASE_URL}/users/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Login failed');
    }

    const data = await response.json();
    
    // Store auth data
    const authState: AuthState = {
      isAuthenticated: true,
      user: data.user,
      token: data.access_token,
    };
    
    authStore.set(authState);
    
    // Persist to localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', data.access_token);
      localStorage.setItem('auth_user', JSON.stringify(data.user));
    }
    
    return true;
  } catch (error) {
    authError.set(error instanceof Error ? error.message : 'Login failed');
    return false;
  } finally {
    authLoading.set(false);
  }
}

/**
 * Logout and clear auth state
 */
export function logout() {
  authStore.set({
    isAuthenticated: false,
    user: null,
    token: null,
  });
  
  // Clear localStorage
  if (typeof window !== 'undefined') {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
  }
}

/**
 * Get authorization headers for API requests
 */
export function getAuthHeaders(): HeadersInit {
  const state = authStore.get();
  if (state.token) {
    return {
      'Authorization': `Bearer ${state.token}`,
      'Content-Type': 'application/json',
    };
  }
  return {
    'Content-Type': 'application/json',
  };
}

/**
 * Make an authenticated API request
 * @param endpoint - API endpoint to call
 * @param options - Fetch options
 * @param getToken - Optional function to get Clerk session token
 */
export async function apiRequest(
  endpoint: string, 
  options: RequestInit = {},
  getToken?: () => Promise<string | null>
) {
  // Get Clerk token if getToken function is provided
  let token = null;
  if (getToken) {
    console.debug('🔐 Calling getToken()...');
    token = await getToken();
    console.debug('🔐 Token received:', token ? `${token.substring(0, 20)}...` : 'null');
  }

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers as Record<string, string>,
  };

  // Add Bearer token if available
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
    console.debug('🔐 Authorization header added');
  } else {
    console.log('🔐 No token available, sending request without auth');
  }

  console.debug(`🔐 Making request to: ${API_BASE_URL}${endpoint}`);
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  console.debug(`🔐 Response status: ${response.status}`);

  // If we get 401, redirect to sign-in
  if (response.status === 401) {
    console.error('🔐 401 Unauthorized - Authentication failed!');
    if (typeof window !== 'undefined') {
      window.location.href = '/sign-in';
    }
    throw new Error('Authentication required');
  }

  return response;
}