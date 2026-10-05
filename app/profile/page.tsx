"use client";

import {
  useEffect,
  useState,
} from "react";

import { useRouter } from "next/navigation";

import Sidebar from "@/components/layout/Sidebar";
import Topbar from "@/components/layout/Topbar";

import {
  getCurrentAdministrator,
  logoutAdministrator,
  type Administrator,
} from "@/lib/auth";

export default function ProfilePage() {
  const router = useRouter();

  // ------------------------------------------------------------
  // ADMINISTRATOR
  // ------------------------------------------------------------

  const [
    administrator,
    setAdministrator,
  ] = useState<Administrator | null>(null);

  const [
    loadingAdministrator,
    setLoadingAdministrator,
  ] = useState(true);

  const [
    logoutLoading,
    setLogoutLoading,
  ] = useState(false);

  // ------------------------------------------------------------
  // SIDEBAR
  // ------------------------------------------------------------

  const [
    sidebarCollapsed,
    setSidebarCollapsed,
  ] = useState(false);

  const [
    mobileSidebarOpen,
    setMobileSidebarOpen,
  ] = useState(false);

  // ------------------------------------------------------------
  // LOAD ADMINISTRATOR
  // ------------------------------------------------------------

  useEffect(() => {
    let mounted = true;

    const loadAdministrator = async () => {
      try {
        const currentAdministrator =
          await getCurrentAdministrator();

        if (mounted) {
          setAdministrator(
            currentAdministrator
          );
        }
      } catch (error) {
        console.error(
          "Failed to load administrator:",
          error
        );

        if (mounted) {
          router.replace("/login");
        }
      } finally {
        if (mounted) {
          setLoadingAdministrator(false);
        }
      }
    };

    loadAdministrator();

    return () => {
      mounted = false;
    };
  }, [router]);

  // ------------------------------------------------------------
  // RESPONSIVE SIDEBAR
  // ------------------------------------------------------------

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth > 900) {
        setMobileSidebarOpen(false);
      }
    };

    window.addEventListener(
      "resize",
      handleResize
    );

    return () => {
      window.removeEventListener(
        "resize",
        handleResize
      );
    };
  }, []);

  // ------------------------------------------------------------
  // MENU
  // ------------------------------------------------------------

  const handleMenuClick = () => {
    if (window.innerWidth <= 900) {
      setMobileSidebarOpen(
        (current) => !current
      );

      return;
    }

    setSidebarCollapsed(
      (current) => !current
    );
  };

  // ------------------------------------------------------------
  // LOGOUT
  // ------------------------------------------------------------

  const handleLogout = async () => {
    if (logoutLoading) {
      return;
    }

    setLogoutLoading(true);

    try {
      await logoutAdministrator();
    } catch (error) {
      console.error(
        "Logout failed:",
        error
      );
    } finally {
      router.replace("/login");
      router.refresh();
    }
  };

  // ------------------------------------------------------------
  // HELPERS
  // ------------------------------------------------------------

  const getInitials = () => {
    if (!administrator) {
      return "AD";
    }

    const first =
      administrator.first_name
        ?.charAt(0)
        .toUpperCase() || "";

    const last =
      administrator.last_name
        ?.charAt(0)
        .toUpperCase() || "";

    return `${first}${last}`;
  };

  const getRoleLabel = (
    role: string
  ) => {
    switch (role) {
      case "SUPER_ADMINISTRATOR":
        return "Super Administrator";

      case "ADMINISTRATOR":
        return "Administrator";

      case "MODERATOR":
        return "Moderator";

      case "SUPPORT":
        return "Support";

      default:
        return role;
    }
  };

  const getStatusLabel = (
    status: string
  ) => {
    switch (status) {
      case "ACTIVE":
        return "Active";

      case "INACTIVE":
        return "Inactive";

      case "PENDING":
        return "Pending";

      default:
        return status;
    }
  };

  const formatDate = (
    value: string | null
  ) => {
    if (!value) {
      return "Never";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return "—";
    }

    return date.toLocaleString(
      undefined,
      {
        dateStyle: "medium",
        timeStyle: "short",
      }
    );
  };

  // ------------------------------------------------------------
  // PAGE CONTENT
  // ------------------------------------------------------------

  const renderProfileContent = () => {
    // ----------------------------------------------------------
    // LOADING
    // ----------------------------------------------------------

    if (loadingAdministrator) {
      return (
        <div className="admin-page">

          <div className="admin-page-header">
            <div>
              <h1 className="admin-page-title">
                Administrator Profile
              </h1>

              <p className="admin-page-description">
                Manage your administrator account
                and account information.
              </p>
            </div>
          </div>

          <div className="profile-loading-card">
            <div className="profile-loading-spinner" />

            <p>
              Loading administrator profile...
            </p>
          </div>

        </div>
      );
    }

    // ----------------------------------------------------------
    // NO ADMINISTRATOR
    // ----------------------------------------------------------

    if (!administrator) {
      return (
        <div className="admin-page">

          <div className="admin-page-header">
            <div>
              <h1 className="admin-page-title">
                Administrator Profile
              </h1>

              <p className="admin-page-description">
                Manage your administrator account
                and account information.
              </p>
            </div>
          </div>

          <div className="profile-error-card">

            <div className="profile-error-icon">
              !
            </div>

            <div>
              <h3>
                Unable to load profile
              </h3>

              <p>
                Administrator information
                could not be loaded.
              </p>
            </div>

          </div>

        </div>
      );
    }

    // ----------------------------------------------------------
    // ADMIN DATA
    // ----------------------------------------------------------

    const fullName =
      `${administrator.first_name} ${administrator.last_name}`.trim();

    const role =
      getRoleLabel(
        administrator.role
      );

    const status =
      getStatusLabel(
        administrator.status
      );

    // ----------------------------------------------------------
    // PROFILE
    // ----------------------------------------------------------

    return (
      <div className="admin-page">

        {/* ====================================================
            PAGE HEADER
        ==================================================== */}

        <div className="admin-page-header">

          <div>
            <h1 className="admin-page-title">
              Administrator Profile
            </h1>

            <p className="admin-page-description">
              Manage your administrator account
              and account information.
            </p>
          </div>

        </div>

        {/* ====================================================
            PROFILE HERO
        ==================================================== */}

        <section className="profile-hero-card">

          <div className="profile-hero-avatar">
            {getInitials()}
          </div>

          <div className="profile-hero-content">

            <h2>
              {fullName}
            </h2>

            <p>
              {administrator.email}
            </p>

            <div className="profile-hero-meta">

              <span className="profile-role-badge">
                {role}
              </span>

              <span className="profile-status-badge">

                <span className="profile-status-dot" />

                {status}

              </span>

            </div>

          </div>

        </section>

        {/* ====================================================
            PERSONAL INFORMATION
        ==================================================== */}

        <section className="profile-section-card">

          <div className="profile-section-header">

            <div>
              <h2>
                Personal Information
              </h2>

              <p>
                Your basic administrator
                account information.
              </p>
            </div>

          </div>

          <div className="profile-info-grid">

            <div className="profile-info-item">

              <span className="profile-info-label">
                First Name
              </span>

              <span className="profile-info-value">
                {administrator.first_name}
              </span>

            </div>

            <div className="profile-info-item">

              <span className="profile-info-label">
                Last Name
              </span>

              <span className="profile-info-value">
                {administrator.last_name}
              </span>

            </div>

            <div className="profile-info-item profile-info-full">

              <span className="profile-info-label">
                Email Address
              </span>

              <span className="profile-info-value">
                {administrator.email}
              </span>

            </div>

          </div>

        </section>

        {/* ====================================================
            ADMINISTRATOR ACCOUNT
        ==================================================== */}

        <section className="profile-section-card">

          <div className="profile-section-header">

            <div>
              <h2>
                Administrator Account
              </h2>

              <p>
                Account role, status and
                activity information.
              </p>
            </div>

          </div>

          <div className="profile-account-grid">

            <div className="profile-account-item">

              <span className="profile-info-label">
                Role
              </span>

              <span className="profile-info-value">
                {role}
              </span>

            </div>

            <div className="profile-account-item">

              <span className="profile-info-label">
                Status
              </span>

              <span className="profile-info-value profile-active-value">

                <span className="profile-status-dot" />

                {status}

              </span>

            </div>

            <div className="profile-account-item">

              <span className="profile-info-label">
                Account Access
              </span>

              <span className="profile-info-value">
                {administrator.is_active
                  ? "Enabled"
                  : "Disabled"}
              </span>

            </div>

            <div className="profile-account-item">

              <span className="profile-info-label">
                Last Login
              </span>

              <span className="profile-info-value">
                {formatDate(
                  administrator.last_login_at
                )}
              </span>

            </div>

          </div>

        </section>

        {/* ====================================================
            SECURITY
        ==================================================== */}

        <section className="profile-section-card">

          <div className="profile-section-header">

            <div>
              <h2>
                Security
              </h2>

              <p>
                Manage your administrator
                account security.
              </p>
            </div>

          </div>

          <div className="profile-security-row">

            <div className="profile-security-icon">

              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
              >
                <rect
                  x="4"
                  y="10"
                  width="16"
                  height="10"
                  rx="2"
                  stroke="currentColor"
                  strokeWidth="1.8"
                />

                <path
                  d="M8 10V7a4 4 0 0 1 8 0v3"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                />
              </svg>

            </div>

            <div className="profile-security-content">

              <h3>
                Password
              </h3>

              <p>
                Your password is securely
                stored and protected.
              </p>

            </div>

            <button
              type="button"
              className="profile-secondary-button"
              disabled
            >
              Change Password
            </button>

          </div>

        </section>

      </div>
    );
  };

  // ------------------------------------------------------------
  // BUILD
  // ------------------------------------------------------------

  return (
    <div
      className={`admin-shell ${
        sidebarCollapsed
          ? "sidebar-collapsed"
          : ""
      } ${
        mobileSidebarOpen
          ? "mobile-sidebar-open"
          : ""
      }`}
    >

      {/* ======================================================
          SIDEBAR
      ====================================================== */}

      <Sidebar />

      {/* ======================================================
          MOBILE OVERLAY
      ====================================================== */}

      <div
        className="mobile-sidebar-overlay"
        onClick={() =>
          setMobileSidebarOpen(false)
        }
      />

      {/* ======================================================
          MAIN
      ====================================================== */}

      <main className="admin-main">

        {/* ====================================================
            TOPBAR
        ==================================================== */}

        <Topbar
          onMenuClick={handleMenuClick}
          administrator={administrator}
          onLogout={handleLogout}
          logoutLoading={logoutLoading}
        />

        {/* ====================================================
            CONTENT
        ==================================================== */}

        <section className="admin-content">
          {renderProfileContent()}
        </section>

      </main>

    </div>
  );
}