"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

// Sanitize URL: removes trailing slashes to prevent double slashes like '//api/auth/login'
const RAW_API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
const API_URL = RAW_API_URL.replace(/\/+$/, "");

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (
    event: FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();
    console.log("LOGIN FORM SUBMITTED to:", `${API_URL}/backend/app/api/auth/login`);

    if (loading) {
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `${API_URL}/backend/app/api/auth/login`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
          body: JSON.stringify({
            email: email.trim(),
            password,
          }),
        }
      );

      let data: any = null;

      try {
        data = await response.json();
      } catch {
        data = null;
      }

      if (!response.ok) {
        setError(
          data?.detail ||
            "Unable to sign in. Please check your email and password."
        );
        return;
      }

      // Store token in localStorage as a backup for cross-domain requests
      if (data?.access_token) {
        localStorage.setItem("mines_admin_token", data.access_token);
      }

      router.push("/dashboard");
      router.refresh();
    } catch (err) {
      console.error("Login request failed:", err);
      setError(
        "Unable to connect to the server. Please check your connection and try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-white flex items-center justify-center px-5 py-10">
      <div className="w-full max-w-[430px]">
        <div className="rounded-[22px] border border-[#E5EAF0] bg-white p-7 shadow-[0_18px_50px_rgba(23,33,43,0.07)]">
          <div className="mb-6">
            <h2 className="text-[19px] font-extrabold text-[#17212B]">
              Welcome back
            </h2>

            <p className="mt-1.5 text-[12px] text-[#6B7785]">
              Sign in to access the admin panel.
            </p>
          </div>

          {/* ERROR ALERT */}
          {error && (
            <div className="mb-5 rounded-[12px] border border-[#EF4444]/20 bg-[#EF4444]/5 px-3.5 py-3">
              <p className="text-[11px] font-semibold leading-5 text-[#EF4444]">
                {error}
              </p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* EMAIL */}
            <div>
              <label
                htmlFor="email"
                className="mb-2 block text-[11px] font-bold text-[#17212B]"
              >
                Email address
              </label>

              <div className="relative">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5">
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    className="text-[#98A2B3]"
                  >
                    <rect
                      x="3"
                      y="5"
                      width="18"
                      height="14"
                      rx="2"
                    />
                    <path d="m3 7 9 6 9-6" />
                  </svg>
                </div>

                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(event) =>
                    setEmail(event.target.value)
                  }
                  placeholder="admin@example.com"
                  required
                  className="h-[46px] w-full rounded-[12px] border border-[#E5EAF0] bg-[#F7F9FB] pl-10 pr-3.5 text-[12px] font-medium text-[#17212B] outline-none transition placeholder:text-[#98A2B3] focus:border-[#229ED9] focus:bg-white focus:ring-4 focus:ring-[#229ED9]/10"
                />
              </div>
            </div>

            {/* PASSWORD */}
            <div>
              <div className="mb-2 flex items-center justify-between">
                <label
                  htmlFor="password"
                  className="block text-[11px] font-bold text-[#17212B]"
                >
                  Password
                </label>

                <button
                  type="button"
                  className="text-[10px] font-bold text-[#229ED9] transition hover:text-[#168AC0]"
                >
                  Forgot password?
                </button>
              </div>

              <div className="relative">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5">
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    className="text-[#98A2B3]"
                  >
                    <rect
                      x="4"
                      y="10"
                      width="16"
                      height="10"
                      rx="2"
                    />
                    <path d="M8 10V7a4 4 0 0 1 8 0v3" />
                  </svg>
                </div>

                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  value={password}
                  onChange={(event) =>
                    setPassword(event.target.value)
                  }
                  placeholder="Enter your password"
                  required
                  className="h-[46px] w-full rounded-[12px] border border-[#E5EAF0] bg-[#F7F9FB] pl-10 pr-11 text-[12px] font-medium text-[#17212B] outline-none transition placeholder:text-[#98A2B3] focus:border-[#229ED9] focus:bg-white focus:ring-4 focus:ring-[#229ED9]/10"
                />

                <button
                  type="button"
                  onClick={() => setShowPassword((current) => !current)}
                  className="absolute inset-y-0 right-0 flex items-center px-3.5 text-[#98A2B3] transition hover:text-[#229ED9]"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M3 3l18 18" />
                      <path d="M10.6 10.6a2 2 0 0 0 2.8 2.8" />
                      <path d="M9.9 4.2A10.8 10.8 0 0 1 12 4c5.5 0 9 5.5 9 8s-3.5 8-9 8a9.7 9.7 0 0 1-4.4-1.1" />
                      <path d="M6.6 6.6C4.3 8.2 3 10.3 3 12c0 1.1 1.1 2.9 3 4.8" />
                    </svg>
                  ) : (
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M2.5 12s3.5-7 9.5-7 9.5 7 9.5 7-3.5 7-9.5 7-9.5-7Z" />
                      <circle cx="12" cy="12" r="2.5" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            {/* REMEMBER */}
            <div className="flex items-center justify-between">
              <label className="flex cursor-pointer items-center gap-2">
                <input
                  type="checkbox"
                  className="h-3.5 w-3.5 rounded border-[#D7DEE7] text-[#229ED9] focus:ring-[#229ED9]/20"
                />
                <span className="text-[10px] font-medium text-[#6B7785]">
                  Keep me signed in
                </span>
              </label>
            </div>

            {/* SUBMIT */}
            <button
              type="submit"
              disabled={loading}
              className="flex h-[46px] w-full items-center justify-center rounded-[12px] bg-[#229ED9] text-[12px] font-extrabold text-white shadow-[0_10px_24px_rgba(34,158,217,0.18)] transition hover:bg-[#168AC0] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                  Signing in...
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  Sign in
                  <svg
                    width="15"
                    height="15"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M5 12h14" />
                    <path d="m13 6 6 6-6 6" />
                  </svg>
                </span>
              )}
            </button>
          </form>
        </div>

        <div className="mt-6 text-center">
          <p className="text-[10px] font-medium text-[#98A2B3]">
            Mines Signal System
          </p>

          <p className="mt-1 text-[9px] text-[#B0B8C2]">
            Secure administrator access
          </p>
        </div>
      </div>
    </main>
  );
}