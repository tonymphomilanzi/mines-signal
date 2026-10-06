"use client";

import { useEffect, useState } from "react";
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

export default function AdminShell({ children }: AdminShellProps) {
  const router = useRouter();

  const [administrator, setAdministrator] = useState<Administrator | null>(null);
  const [loadingAdministrator, setLoadingAdministrator] = useState(true);
  const [logoutLoading, setLogoutLoading] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  useEffect(() => {
    let mounted = true;

    const loadAdministrator = async () => {
      try {
        const currentAdministrator = await getCurrentAdministrator();

        if (mounted) {
          setAdministrator(currentAdministrator);
        }
      } catch (error) {
        console.error("Failed to load administrator:", error);

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

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth > 900) {
        setMobileSidebarOpen(false);
      }
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const handleMenuClick = () => {
    if (window.innerWidth <= 900) {
      setMobileSidebarOpen((current) => !current);
      return;
    }

    setSidebarCollapsed((current) => !current);
  };

  const handleLogout = async () => {
    if (logoutLoading) return;
    setLogoutLoading(true);

    try {
      await logoutAdministrator();
    } catch (error) {
      console.error("Logout failed:", error);
    } finally {
      router.replace("/login");
      router.refresh();
    }
  };

  // Prevent flashing or premature redirect while checking auth
  if (loadingAdministrator) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#F7F9FB]">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-3 border-[#229ED9]/20 border-t-[#229ED9]" />
          <p className="text-[12px] font-bold text-[#6B7785]">Loading admin panel...</p>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`admin-shell ${
        sidebarCollapsed ? "sidebar-collapsed" : ""
      } ${mobileSidebarOpen ? "mobile-sidebar-open" : ""}`}
    >
      <Sidebar />

      <div
        className="mobile-sidebar-overlay"
        onClick={() => setMobileSidebarOpen(false)}
      />

      <main className="admin-main">
        <Topbar
          onMenuClick={handleMenuClick}
          administrator={administrator}
          onLogout={handleLogout}
          logoutLoading={logoutLoading}
        />

        <section className="admin-content">{children}</section>
      </main>
    </div>
  );
}