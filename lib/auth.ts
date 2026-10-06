export interface Administrator {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  role: string;
  status: string;
  is_active: boolean;
  last_login_at: string | null;
}

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

// 1. Get Token from localStorage or Cookies
export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;

  const localToken = localStorage.getItem("access_token");
  if (localToken) return localToken;

  const cookies = document.cookie.split("; ");
  for (const cookie of cookies) {
    const [name, value] = cookie.split("=");
    if (
      name === "mines_admin_token" ||
      name === "access_token" ||
      name === "token"
    ) {
      return value;
    }
  }

  return null;
}

// 2. Get stored admin from localStorage (fixes the TypeScript build error)
export function getStoredAdministrator(): Administrator | null {
  if (typeof window === "undefined") return null;
  try {
    const item =
      localStorage.getItem("administrator") ||
      localStorage.getItem("admin");
    return item ? JSON.parse(item) : null;
  } catch {
    return null;
  }
}

// 3. Fetch fresh administrator data from backend
export async function getCurrentAdministrator(): Promise<Administrator | null> {
  const token = getAuthToken();

  if (!token) {
    return null;
  }

  try {
    const response = await fetch(`${API_URL}/api/auth/me`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      credentials: "include",
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    const data = (await response.json()) as Administrator;

    // Cache the admin in localStorage for instant rendering
    if (typeof window !== "undefined") {
      localStorage.setItem("administrator", JSON.stringify(data));
    }

    return data;
  } catch {
    return null;
  }
}

// 4. Logout and clean up
export async function logoutAdministrator(): Promise<void> {
  const token = getAuthToken();

  try {
    await fetch(`${API_URL}/api/auth/logout`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      credentials: "include",
    });
  } finally {
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      localStorage.removeItem("administrator");
      localStorage.removeItem("admin");
      document.cookie = "mines_admin_token=; path=/; max-age=0;";
      document.cookie = "access_token=; path=/; max-age=0;";
      document.cookie = "token=; path=/; max-age=0;";
    }
  }
}