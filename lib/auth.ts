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

export async function getCurrentAdministrator(): Promise<Administrator> {
  const response = await fetch(
    `${API_URL}/api/auth/me`,
    {
      method: "GET",
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
  const response = await fetch(
    `${API_URL}/api/auth/logout`,
    {
      method: "POST",
      credentials: "include",
    }
  );

  if (!response.ok) {
    throw new Error(
      "Unable to log out."
    );
  }
}