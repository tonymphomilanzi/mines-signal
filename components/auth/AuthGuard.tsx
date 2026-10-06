"use client";

import {
  ReactNode,
  useEffect,
  useState,
} from "react";
import { useRouter } from "next/navigation";

import {
  getCurrentAdministrator,
  getStoredAdministrator,
  Administrator,
} from "@/lib/auth";

type AuthGuardProps = {
  children: ReactNode;
};

export default function AuthGuard({
  children,
}: AuthGuardProps) {
  const router = useRouter();

  const [administrator, setAdministrator] =
    useState<Administrator | null>(
      getStoredAdministrator()
    );

  const [checking, setChecking] =
    useState(!administrator);

  useEffect(() => {
    let mounted = true;

    const verifyAuthentication = async () => {
      try {
        const current = await getCurrentAdministrator();

        if (!mounted) {
          return;
        }

        if (!current) {
          router.replace("/login");
          return;
        }

        setAdministrator(current);
        setChecking(false);
      } catch {
        if (!mounted) return;
        router.replace("/login");
      }
    };

    verifyAuthentication();

    return () => {
      mounted = false;
    };
  }, [router]);

  if (checking && !administrator) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="flex items-center gap-3">
          <span className="h-5 w-5 animate-spin rounded-full border-2 border-[#229ED9]/30 border-t-[#229ED9]" />
          <span className="text-[12px] font-semibold text-[#6B7785]">
            Checking authentication...
          </span>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}