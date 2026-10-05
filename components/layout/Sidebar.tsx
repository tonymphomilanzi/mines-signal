"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type IconProps = {
  size?: number;
};

const icons = {
  dashboard: ({ size = 19 }: IconProps) => (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
    >
      <rect
        x="3"
        y="3"
        width="7"
        height="7"
        rx="1.5"
        stroke="currentColor"
        strokeWidth="2"
      />
      <rect
        x="14"
        y="3"
        width="7"
        height="7"
        rx="1.5"
        stroke="currentColor"
        strokeWidth="2"
      />
      <rect
        x="3"
        y="14"
        width="7"
        height="7"
        rx="1.5"
        stroke="currentColor"
        strokeWidth="2"
      />
      <rect
        x="14"
        y="14"
        width="7"
        height="7"
        rx="1.5"
        stroke="currentColor"
        strokeWidth="2"
      />
    </svg>
  ),

  signal: ({ size = 19 }: IconProps) => (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
    >
      <path
        d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9L12 3z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
      <path
        d="M19 16l.8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8L19 16z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  ),

  plus: ({ size = 19 }: IconProps) => (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
    >
      <path
        d="M12 5v14M5 12h14"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  ),

  results: ({ size = 19 }: IconProps) => (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
    >
      <path
        d="M5 4v16M5 20h16"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <path
        d="M9 16l3-4 3 2 4-6"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  ),

  telegram: ({ size = 19 }: IconProps) => (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
    >
      <path
        d="M21.4 3.6L18.1 20c-.25 1.15-.92 1.43-1.86.9l-5.15-3.8-2.49 2.4c-.28.28-.52.52-1.07.52l.38-5.25 9.56-8.64c.42-.38-.09-.59-.65-.21L5 13.04.02 11.48c-1.08-.34-1.1-1.08.23-1.6L19.72 2.1c.9-.33 1.69.21 1.68 1.5Z"
        fill="currentColor"
      />
    </svg>
  ),

  autoPublisher: ({ size = 19 }: IconProps) => (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
    >
      <rect
        x="4"
        y="5"
        width="16"
        height="14"
        rx="2.5"
        stroke="currentColor"
        strokeWidth="1.8"
      />
      <path
        d="M8 9h8M8 13h5"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
      <path
        d="M17.5 15.5l1 1M19.5 16.5l-1 1"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
      <circle
        cx="17"
        cy="15"
        r="2.5"
        stroke="currentColor"
        strokeWidth="1.5"
      />
    </svg>
  ),

  analytics: ({ size = 19 }: IconProps) => (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
    >
      <path
        d="M4 19V5M4 19h17"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <path
        d="M8 16l3-4 3 2 5-7"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  ),

  model: ({ size = 19 }: IconProps) => (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
    >
      <circle
        cx="12"
        cy="12"
        r="3"
        stroke="currentColor"
        strokeWidth="2"
      />
      <circle
        cx="5"
        cy="7"
        r="2"
        stroke="currentColor"
        strokeWidth="1.7"
      />
      <circle
        cx="19"
        cy="7"
        r="2"
        stroke="currentColor"
        strokeWidth="1.7"
      />
      <circle
        cx="5"
        cy="17"
        r="2"
        stroke="currentColor"
        strokeWidth="1.7"
      />
      <circle
        cx="19"
        cy="17"
        r="2"
        stroke="currentColor"
        strokeWidth="1.7"
      />
      <path
        d="M7 8.5l2.5 1.8M17 8.5l-2.5 1.8M7 15.5l2.5-1.8M17 15.5l-2.5-1.8"
        stroke="currentColor"
        strokeWidth="1.5"
      />
    </svg>
  ),

  settings: ({ size = 19 }: IconProps) => (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
    >
      <path
        d="M12 15.2a3.2 3.2 0 100-6.4 3.2 3.2 0 000 6.4z"
        stroke="currentColor"
        strokeWidth="1.8"
      />
      <path
        d="M19.4 15a1.7 1.7 0 00.34 1.87l.06.06-1.9 1.9-.06-.06a1.7 1.7 0 00-1.87-.34 1.7 1.7 0 00-1.03 1.56v.09h-2.68v-.09a1.7 1.7 0 00-1.03-1.56 1.7 1.7 0 00-1.87.34l-.06.06-1.9-1.9.06-.06A1.7 1.7 0 007.8 15a1.7 1.7 0 00-1.56-1.03h-.09v-2.68h.09A1.7 1.7 0 007.8 10.3a1.7 1.7 0 00-.34-1.87L7.4 8.37l1.9-1.9.06.06a1.7 1.7 0 001.87.34 1.7 1.7 0 001.03-1.56v-.09h2.68v.09a1.7 1.7 0 001.03 1.56 1.7 1.7 0 001.87-.34l.06-.06 1.9 1.9-.06.06A1.7 1.7 0 0019.4 10.3a1.7 1.7 0 001.56 1.03h.09v2.68h-.09A1.7 1.7 0 0019.4 15z"
        stroke="currentColor"
        strokeWidth="1.3"
        strokeLinejoin="round"
      />
    </svg>
  ),
};

const sections = [
  {
    title: "Overview",
    items: [
      {
        label: "Dashboard",
        href: "/dashboard",
        icon: icons.dashboard,
      },
    ],
  },
  {
    title: "Signals",
    items: [
      {
        label: "Signals",
        href: "/signals",
        icon: icons.signal,
      },
      // {
      //   label: "Create Signal",
      //   href: "/signals/create",
      //   icon: icons.plus,
      // },
      {
        label: "Signal Results",
        href: "/results",
        icon: icons.results,
      },
    ],
  },
  {
    title: "System Intelligence",
    items: [
      {
        label: "Telegram",
        href: "/telegram",
        icon: icons.telegram,
      },
      {
        label: "Auto Publisher",
        href: "/telegram/auto-publisher",
        icon: icons.autoPublisher,
      },
      {
        label: "Performance",
        href: "/performance",
        icon: icons.analytics,
      },
      {
        label: "Models",
        href: "/models",
        icon: icons.model,
      },
      {
        label: "Adminstrators",
        href: "/adminstrators",
        icon: icons.settings,
      },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="admin-sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-brand-mark">
          <svg
            viewBox="0 0 24 24"
            fill="none"
          >
            <path
              d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Z"
              fill="currentColor"
            />
            <path
              d="M19 15l.7 2.3L22 18l-2.3.7L19 21l-.7-2.3L16 18l2.3-.7L19 15Z"
              fill="currentColor"
              opacity=".75"
            />
          </svg>
        </div>

        <div className="sidebar-brand-text">
          <div className="sidebar-brand-title">
            MINES SIGNAL
          </div>

          <div className="sidebar-brand-subtitle">
            ADMIN SYSTEM
          </div>
        </div>
      </div>

      <nav className="sidebar-navigation">
        {sections.map((section) => (
          <div
            className="sidebar-section"
            key={section.title}
          >
            <div className="sidebar-section-title">
              {section.title}
            </div>

            {section.items.map((item) => {
              const isActive =
                pathname === item.href ||
                (item.href !== "/dashboard" &&
                  pathname.startsWith(
                    `${item.href}/`
                  ));

              const Icon = item.icon;

              return (
                <Link
                  href={item.href}
                  key={item.href}
                  className={`sidebar-nav-item ${
                    isActive ? "active" : ""
                  }`}
                  title={item.label}
                >
                  <span className="sidebar-nav-icon">
                    <Icon />
                  </span>

                  <span className="sidebar-nav-label">
                    {item.label}
                  </span>
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-system-status">
          <span className="sidebar-status-dot" />

          <div className="sidebar-status-content">
            <div className="sidebar-status-title">
              System Online
            </div>

            <div className="sidebar-status-subtitle">
              All services operational
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
 
