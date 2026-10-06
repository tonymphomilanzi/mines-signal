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

// Helper to retrieve the token from localStorage or cookies
function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;

  // 1. Try localStorage
  const localToken = localStorage.getItem("access_token");
  if (localToken) return localToken;

  // 2. Try cookies
  const cookies = document.cookie.split("; ");
  for (const cookie of cookies) {
    const [name, value] = cookie.split("=");
    if (name === "access_token" || name === "token") {
      return value;
    }
  }

  return null;
}

export async function getCurrentAdministrator(): Promise<Administrator> {
  const token = getAuthToken();

  const response = await fetch(
    `${API_URL}/api/auth/me`,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      credentials: "include",
      cache: "no-store",
    }
  );

  if (!response.ok) {
    throw new Error(
      "Unable to load administrator session."
    );
  }

  return response.json();
}

export async function logoutAdministrator(): Promise<void> {
  const token = getAuthToken();

  try {
    await fetch(
      `${API_URL}/api/auth/logout`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: "include",
      }
    );
  } finally {
    // Clear credentials on logout
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      document.cookie = "access_token=; path=/; max-age=0;";
      document.cookie = "token=; path=/; max-age=0;";
    }
  }
}