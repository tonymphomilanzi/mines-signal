"use client";

import {
  useEffect,
  useRef,
  useState,
} from "react";

import { useRouter } from "next/navigation";

import type { Administrator } from "@/lib/auth";

type TopbarProps = {
  onMenuClick: () => void;
  administrator: Administrator | null;
  onLogout: () => void;
  logoutLoading?: boolean;
};

export default function Topbar({
  onMenuClick,
  administrator,
  onLogout,
  logoutLoading = false,
}: TopbarProps) {
  const router = useRouter();

  const profileRef =
    useRef<HTMLDivElement>(null);

  const [profileOpen, setProfileOpen] =
    useState(false);

  const firstName =
    administrator?.first_name?.trim() ||
    "Admin";

  const lastName =
    administrator?.last_name?.trim() || "";

  const fullName =
    `${firstName} ${lastName}`.trim();

  const initials =
    `${firstName.charAt(0)}${lastName.charAt(0)}`
      .toUpperCase();

  const role =
    administrator?.role ===
    "SUPER_ADMINISTRATOR"
      ? "Super Administrator"
      : administrator?.role ||
        "Administrator";

  // ------------------------------------------------------------
  // CLOSE DROPDOWN WHEN CLICKING OUTSIDE
  // ------------------------------------------------------------

  useEffect(() => {
    const handleClickOutside = (
      event: MouseEvent
    ) => {
      if (
        profileRef.current &&
        !profileRef.current.contains(
          event.target as Node
        )
      ) {
        setProfileOpen(false);
      }
    };

    document.addEventListener(
      "mousedown",
      handleClickOutside
    );

    return () => {
      document.removeEventListener(
        "mousedown",
        handleClickOutside
      );
    };
  }, []);

  // ------------------------------------------------------------
  // ESCAPE KEY
  // ------------------------------------------------------------

  useEffect(() => {
    const handleEscape = (
      event: KeyboardEvent
    ) => {
      if (event.key === "Escape") {
        setProfileOpen(false);
      }
    };

    document.addEventListener(
      "keydown",
      handleEscape
    );

    return () => {
      document.removeEventListener(
        "keydown",
        handleEscape
      );
    };
  }, []);

  // ------------------------------------------------------------
  // NAVIGATION
  // ------------------------------------------------------------

  const handleProfile = () => {
    setProfileOpen(false);
    router.push("/profile");
  };

  const handleSettings = () => {
    setProfileOpen(false);
    router.push("/settings");
  };

  const handleLogout = () => {
    if (logoutLoading) {
      return;
    }

    setProfileOpen(false);
    onLogout();
  };

  // ------------------------------------------------------------
  // BUILD
  // ------------------------------------------------------------

  return (
    <header className="admin-topbar">
      <div className="topbar-left">
        <button
          type="button"
          className="topbar-menu-button"
          onClick={onMenuClick}
          aria-label="Toggle sidebar"
        >
          <svg
            width="19"
            height="19"
            viewBox="0 0 24 24"
            fill="none"
          >
            <path
              d="M4 7h16M4 12h16M4 17h16"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        </button>

        <div>
          <div className="topbar-title">
            Mines Signal System
          </div>

          <div className="topbar-subtitle">
            Signal management and Telegram publishing
          </div>
        </div>
      </div>

      <div className="topbar-spacer" />

      <div className="topbar-actions">
        <button
          type="button"
          className="topbar-icon-button"
          aria-label="Notifications"
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
          >
            <path
              d="M18 9a6 6 0 00-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9ZM10 21h4"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>

          <span className="topbar-notification-dot" />
        </button>

        {/* PROFILE */}
        <div
          ref={profileRef}
          className="topbar-profile-wrapper"
        >
          <button
            type="button"
            className="topbar-profile"
            onClick={() =>
              setProfileOpen(
                (current) => !current
              )
            }
            aria-expanded={profileOpen}
            aria-haspopup="menu"
          >
            <div className="topbar-avatar">
              {initials}
            </div>

            <div className="topbar-profile-info">
              <div className="topbar-profile-name">
                {fullName}
              </div>

              <div className="topbar-profile-role">
                {role}
              </div>
            </div>

            <svg
              className={`topbar-profile-chevron ${
                profileOpen
                  ? "profile-chevron-open"
                  : ""
              }`}
              width="15"
              height="15"
              viewBox="0 0 24 24"
              fill="none"
            >
              <path
                d="m6 9 6 6 6-6"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>

          {/* DROPDOWN */}
          {profileOpen && (
            <div
              className="topbar-profile-dropdown"
              role="menu"
            >
              <div className="profile-dropdown-header">
                <div className="profile-dropdown-avatar">
                  {initials}
                </div>

                <div>
                  <div className="profile-dropdown-name">
                    {fullName}
                  </div>

                  <div className="profile-dropdown-email">
                    {administrator?.email ||
                      ""}
                  </div>
                </div>
              </div>

              <div className="profile-dropdown-divider" />

              <button
                type="button"
                className="profile-dropdown-item"
                onClick={handleProfile}
                role="menuitem"
              >
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <path
                    d="M20 21a8 8 0 0 0-16 0"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                  />
                  <circle
                    cx="12"
                    cy="7"
                    r="4"
                    stroke="currentColor"
                    strokeWidth="1.8"
                  />
                </svg>

                <span>Profile</span>
              </button>

              <button
                type="button"
                className="profile-dropdown-item"
                onClick={handleSettings}
                role="menuitem"
              >
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <path
                    d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z"
                    stroke="currentColor"
                    strokeWidth="1.8"
                  />
                  <path
                    d="M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06-1.8 1.8-.06-.06a1.7 1.7 0 0 0-1.88-.34 1.7 1.7 0 0 0-1.04 1.56v.1h-2.55v-.1a1.7 1.7 0 0 0-1.04-1.56 1.7 1.7 0 0 0-1.88.34l-.06.06-1.8-1.8.06-.06A1.7 1.7 0 0 0 8.1 15a1.7 1.7 0 0 0-1.56-1.04h-.1v-2.55h.1A1.7 1.7 0 0 0 8.1 10.37a1.7 1.7 0 0 0-.34-1.88L7.7 8.43l1.8-1.8.06.06a1.7 1.7 0 0 0 1.88.34 1.7 1.7 0 0 0 1.04-1.56v-.1h2.55v.1a1.7 1.7 0 0 0 1.04 1.56 1.7 1.7 0 0 0 1.88-.34l.06-.06 1.8 1.8-.06.06a1.7 1.7 0 0 0-.34 1.88 1.7 1.7 0 0 0 1.56 1.04h.1v2.55h-.1A1.7 1.7 0 0 0 19.4 15Z"
                    stroke="currentColor"
                    strokeWidth="1.3"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>

                <span>Settings</span>
              </button>

              <div className="profile-dropdown-divider" />

              <button
                type="button"
                className="profile-dropdown-item profile-dropdown-logout"
                onClick={handleLogout}
                disabled={logoutLoading}
                role="menuitem"
              >
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <path
                    d="M9 5H5a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h4"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                  />
                  <path
                    d="M13 16l4-4-4-4M17 12H9"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>

                <span>
                  {logoutLoading
                    ? "Signing out..."
                    : "Logout"}
                </span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}