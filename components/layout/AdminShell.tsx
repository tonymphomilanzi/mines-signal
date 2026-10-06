"use client";

import {
  useEffect,
  useState,
} from "react";

import { useRouter } from "next/navigation";

import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

import {
  getCurrentAdministrator,
  logoutAdministrator,
  type Administrator,
} from "@/lib/auth";

type AdminShellProps = {
  children: React.ReactNode;
};

export default function AdminShell({
  children,
}: AdminShellProps) {
  const router = useRouter();

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

  const [
    sidebarCollapsed,
    setSidebarCollapsed,
  ] = useState(false);

  const [
    mobileSidebarOpen,
    setMobileSidebarOpen,
  ] = useState(false);

  // ------------------------------------------------------------
  // LOAD CURRENT ADMINISTRATOR
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

    return () =>
      window.removeEventListener(
        "resize",
        handleResize
      );
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
      <Sidebar />

      <div
        className="mobile-sidebar-overlay"
        onClick={() =>
          setMobileSidebarOpen(false)
        }
      />

      <main className="admin-main">
        <Topbar
  onMenuClick={handleMenuClick}
  administrator={administrator}
  onLogout={handleLogout}
  logoutLoading={logoutLoading}
/>

        <section className="admin-content">
          {children}
        </section>
      </main>
    </div>
  );
}