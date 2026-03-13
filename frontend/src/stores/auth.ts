/**
 * API request utility
 */

// API base URL
const API_BASE_URL = import.meta.env.PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Make an authenticated API request.
 * @param endpoint - API endpoint path (e.g. "/people")
 * @param options - Fetch options
 * @param getToken - Clerk session token getter (from useAuth().getToken)
 */
export async function apiRequest(
  endpoint: string,
  options: RequestInit = {},
  getToken?: () => Promise<string | null>
) {
  let token = null;
  if (getToken) {
    token = await getToken();
  }

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers as Record<string, string>,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    if (typeof window !== 'undefined') {
      window.location.href = '/sign-in';
    }
    throw new Error('Authentication required');
  }

  return response;
}
