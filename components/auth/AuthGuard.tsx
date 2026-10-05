"use client";

import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { useRouter } from "next/navigation";

import { getCurrentAdministrator } from "@/lib/auth";
import type { Administrator } from "@/lib/auth";

type AuthGuardProps = {
  children: ReactNode;
};

export default function AuthGuard({ children }: AuthGuardProps) {
  const router = useRouter();

  const [administrator, setAdministrator] =
    useState<Administrator | null>(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    let mounted = true;

    const verifyAuthentication = async () => {
      try {
        const current = await getCurrentAdministrator();

        if (!mounted) return;

        setAdministrator(current);
        setChecking(false);
      } catch {
        if (!mounted) return;

        // getCurrentAdministrator throws when not authenticated
        router.replace("/login");
      }
    };

    void verifyAuthentication();

    return () => {
      mounted = false;
    };
  }, [router]);

  if (checking || !administrator) {
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
