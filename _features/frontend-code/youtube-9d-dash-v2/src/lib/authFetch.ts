const TOKEN_KEY = 'yt_dash_token';
const REMEMBER_KEY = 'yt_dash_remember_user';

export function getAuthToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setAuthToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearAuthToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export function getRememberedUser(): string | null {
  return localStorage.getItem(REMEMBER_KEY);
}

export function setRememberedUser(username: string): void {
  localStorage.setItem(REMEMBER_KEY, username);
}

export function clearRememberedUser(): void {
  localStorage.removeItem(REMEMBER_KEY);
}

export function getAuthHeaders(): Record<string, string> {
  const token = getAuthToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export function handle401(response: Response): void {
  if (response.status === 401) {
    clearAuthToken();
    window.location.href = '/dash/login';
  }
}
