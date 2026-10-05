"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import Link from "next/link";

import AdminShell from "@/components/layout/AdminShell";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

// ============================================================
// TYPES
// ============================================================

type AutoPostStatus =
  | "DRAFT"
  | "QUEUED"
  | "PUBLISHING"
  | "PUBLISHED"
  | "FAILED"
  | "CANCELLED";

type AutoPostContentType =
  | "MESSAGE"
  | "LINK"
  | "VIDEO"
  | "IMAGE";

interface AutoPost {
  id: string;
  title: string;
  content_type: AutoPostContentType;
  message: string | null;
  link_url: string | null;
  media_url: string | null;
  caption: string | null;
  status: AutoPostStatus;
  is_active: boolean;
  scheduled_at: string | null;
  published_at: string | null;
  telegram_message_id: number | null;
  channel_id: string | null;
  channel_username: string | null;
  attempts: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

interface Statistics {
  total: number;
  draft: number;
  queued: number;
  publishing: number;
  published: number;
  failed: number;
  cancelled: number;
  active: number;
  next_scheduled_at: string | null;
}

interface AutoPostListResponse {
  items: AutoPost[];
  total: number;
}

// ============================================================
// ICONS
// ============================================================

const icons = {
  plus: (
    <svg
      width="17"
      height="17"
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

  refresh: (
    <svg
      width="15"
      height="15"
      viewBox="0 0 24 24"
      fill="none"
    >
      <path
        d="M20 11a8.1 8.1 0 00-14.8-4.5L4 9"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M4 4v5h5"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M4 13a8.1 8.1 0 0014.8 4.5L20 15"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M20 20v-5h-5"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  ),

  calendar: (
    <svg
      width="17"
      height="17"
      viewBox="0 0 24 24"
      fill="none"
    >
      <rect
        x="3"
        y="5"
        width="18"
        height="16"
        rx="2"
        stroke="currentColor"
        strokeWidth="1.8"
      />
      <path
        d="M16 3v4M8 3v4M3 10h18"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  ),

  clock: (
    <svg
      width="17"
      height="17"
      viewBox="0 0 24 24"
      fill="none"
    >
      <circle
        cx="12"
        cy="12"
        r="8.5"
        stroke="currentColor"
        strokeWidth="1.8"
      />
      <path
        d="M12 7v5l3 2"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  ),

  check: (
    <svg
      width="17"
      height="17"
      viewBox="0 0 24 24"
      fill="none"
    >
      <path
        d="M5 12.5l4.5 4.5L19 7.5"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  ),

  alert: (
    <svg
      width="17"
      height="17"
      viewBox="0 0 24 24"
      fill="none"
    >
      <path
        d="M12 4l9 16H3L12 4z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
      <path
        d="M12 9v5"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
      <circle
        cx="12"
        cy="17"
        r="1"
        fill="currentColor"
      />
    </svg>
  ),

  message: (
    <svg
      width="17"
      height="17"
      viewBox="0 0 24 24"
      fill="none"
    >
      <path
        d="M5 5h14a2 2 0 012 2v9a2 2 0 01-2 2H9l-4 3v-3a2 2 0 01-2-2V7a2 2 0 012-2z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
    </svg>
  ),

  arrow: (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
    >
      <path
        d="M5 12h13M13 6l6 6-6 6"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  ),
};

// ============================================================
// PAGE
// ============================================================

export default function AutoPublisherDashboardPage() {
  const [statistics, setStatistics] =
    useState<Statistics | null>(null);

  const [posts, setPosts] =
    useState<AutoPost[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  const [lastUpdated, setLastUpdated] =
    useState<Date | null>(null);

  // ==========================================================
  // LOAD DATA
  // ==========================================================

  const loadDashboard = useCallback(
    async () => {
      try {
        setLoading(true);
        setError(null);

        const [
          statisticsResponse,
          postsResponse,
        ] = await Promise.all([
          fetch(
            `${API_URL}/api/telegram/auto-posts/statistics`,
            {
              method: "GET",
              credentials: "include",
              cache: "no-store",
            }
          ),

          fetch(
            `${API_URL}/api/telegram/auto-posts?limit=10`,
            {
              method: "GET",
              credentials: "include",
              cache: "no-store",
            }
          ),
        ]);

        if (
          !statisticsResponse.ok ||
          !postsResponse.ok
        ) {
          let message =
            "Unable to load Auto Publisher dashboard.";

          const failedResponse =
            !statisticsResponse.ok
              ? statisticsResponse
              : postsResponse;

          try {
            const body =
              await failedResponse.json();

            if (
              body?.detail &&
              typeof body.detail === "string"
            ) {
              message = body.detail;
            }
          } catch {
            // Ignore JSON parsing errors.
          }

          throw new Error(message);
        }

        const statisticsData =
          (await statisticsResponse.json()) as Statistics;

        const postsData =
          (await postsResponse.json()) as
            | AutoPostListResponse
            | AutoPost[];

        setStatistics(statisticsData);

        setPosts(
          Array.isArray(postsData)
            ? postsData
            : postsData.items ?? []
        );

        setLastUpdated(new Date());
      } catch (error) {
        setError(
          error instanceof Error
            ? error.message
            : "Unable to load Auto Publisher dashboard."
        );
      } finally {
        setLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  // ==========================================================
  // HELPERS
  // ==========================================================

  const formatDate = (
    value: string | null
  ) => {
    if (!value) {
      return "—";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return "—";
    }

    return new Intl.DateTimeFormat(
      undefined,
      {
        dateStyle: "medium",
        timeStyle: "short",
      }
    ).format(date);
  };

  const formatTime = (
    value: string | null
  ) => {
    if (!value) {
      return "—";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return "—";
    }

    return new Intl.DateTimeFormat(
      undefined,
      {
        hour: "numeric",
        minute: "2-digit",
      }
    ).format(date);
  };

  const getStatusLabel = (
    status: AutoPostStatus
  ) => {
    switch (status) {
      case "DRAFT":
        return "Draft";

      case "QUEUED":
        return "Queued";

      case "PUBLISHING":
        return "Publishing";

      case "PUBLISHED":
        return "Published";

      case "FAILED":
        return "Failed";

      case "CANCELLED":
        return "Cancelled";

      default:
        return status;
    }
  };

  const getStatusClasses = (
    status: AutoPostStatus
  ) => {
    switch (status) {
      case "PUBLISHED":
        return "bg-[#EAF8F0] text-[#16804A]";

      case "QUEUED":
        return "bg-[#EAF6FC] text-[#229ED9]";

      case "PUBLISHING":
        return "bg-[#F1EEFF] text-[#6B5DD3]";

      case "FAILED":
        return "bg-[#FFF0F0] text-[#D92D20]";

      case "CANCELLED":
        return "bg-[#F2F4F7] text-[#667085]";

      case "DRAFT":
      default:
        return "bg-[#F2F4F7] text-[#667085]";
    }
  };

  const getTypeLabel = (
    type: AutoPostContentType
  ) => {
    switch (type) {
      case "MESSAGE":
        return "Message";

      case "LINK":
        return "Link";

      case "VIDEO":
        return "Video";

      case "IMAGE":
        return "Image";

      default:
        return type;
    }
  };

  const getTypeClasses = (
    type: AutoPostContentType
  ) => {
    switch (type) {
      case "VIDEO":
        return "bg-[#F1EEFF] text-[#6B5DD3]";

      case "IMAGE":
        return "bg-[#FFF7E6] text-[#B7791F]";

      case "LINK":
        return "bg-[#EAF6FC] text-[#229ED9]";

      case "MESSAGE":
      default:
        return "bg-[#EAF8F0] text-[#16804A]";
    }
  };

  // ==========================================================
  // STATS
  // ==========================================================

  const stats = useMemo(
    () => [
      {
        label: "Queued",
        value: loading
          ? "—"
          : String(statistics?.queued ?? 0),
        description:
          "Waiting to be published",
        icon: icons.clock,
        iconClass:
          "bg-[#EAF6FC] text-[#229ED9]",
      },

      {
        label: "Published",
        value: loading
          ? "—"
          : String(statistics?.published ?? 0),
        description:
          "Successfully delivered",
        icon: icons.check,
        iconClass:
          "bg-[#EAF8F0] text-[#16804A]",
      },

      {
        label: "Failed",
        value: loading
          ? "—"
          : String(statistics?.failed ?? 0),
        description:
          "Need attention",
        icon: icons.alert,
        iconClass:
          "bg-[#FFF0F0] text-[#D92D20]",
      },

      {
        label: "Total Posts",
        value: loading
          ? "—"
          : String(statistics?.total ?? 0),
        description:
          "All auto publisher content",
        icon: icons.message,
        iconClass:
          "bg-[#F1EEFF] text-[#6B5DD3]",
      },
    ],
    [loading, statistics]
  );

  // ==========================================================
  // QUEUED POSTS
  // ==========================================================

  const queuedPosts = useMemo(
    () =>
      posts
        .filter(
          (post) =>
            post.status === "QUEUED" ||
            post.status === "PUBLISHING"
        )
        .sort((a, b) => {
          const first =
            a.scheduled_at
              ? new Date(
                  a.scheduled_at
                ).getTime()
              : Number.MAX_SAFE_INTEGER;

          const second =
            b.scheduled_at
              ? new Date(
                  b.scheduled_at
                ).getTime()
              : Number.MAX_SAFE_INTEGER;

          return first - second;
        })
        .slice(0, 5),
    [posts]
  );

  // ==========================================================
  // RECENT POSTS
  // ==========================================================

  const recentPosts = useMemo(
    () =>
      posts
        .filter(
          (post) =>
            post.status === "PUBLISHED" ||
            post.status === "FAILED"
        )
        .sort((a, b) => {
          const first =
            a.published_at ||
            a.updated_at;

          const second =
            b.published_at ||
            b.updated_at;

          return (
            new Date(second).getTime() -
            new Date(first).getTime()
          );
        })
        .slice(0, 5),
    [posts]
  );

  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <AdminShell>
      <div>
        {/* =====================================================
            PAGE HEADER
        ====================================================== */}

        <div className="mb-7">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h1 className="text-[26px] font-extrabold tracking-[-0.5px] text-[#17212B]">
                Auto Publisher
              </h1>

              <p className="mt-1.5 text-[13px] text-[#6B7785]">
                Automatically publish messages, links,
                videos and images to Telegram.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={loadDashboard}
                disabled={loading}
                className="inline-flex items-center gap-2 rounded-[10px] border border-[#E0E6EC] bg-white px-3.5 py-2.5 text-[11px] font-bold text-[#52606D] shadow-[0_4px_15px_rgba(23,33,43,0.025)] transition hover:bg-[#F8FAFC] disabled:cursor-not-allowed disabled:opacity-50"
              >
                {icons.refresh}
                Refresh
              </button>

              <Link
                href="/telegram/auto-publisher/create"
                className="inline-flex items-center gap-2 rounded-[10px] bg-[#229ED9] px-3.5 py-2.5 text-[11px] font-bold text-white shadow-[0_6px_18px_rgba(34,158,217,0.18)] transition hover:bg-[#168FC8]"
              >
                {icons.plus}
                Create Post
              </Link>
            </div>
          </div>

          {lastUpdated && !loading && (
            <p className="mt-2 text-[10px] text-[#98A2B3]">
              Last updated{" "}
              {formatTime(
                lastUpdated.toISOString()
              )}
            </p>
          )}
        </div>

        {/* =====================================================
            ERROR
        ====================================================== */}

        {error && (
          <div className="mb-5 rounded-[16px] border border-[#F5C2C7] bg-[#FFF5F5] px-5 py-4">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-[12px] font-bold text-[#B42318]">
                  Auto Publisher unavailable
                </p>

                <p className="mt-1 text-[11px] text-[#D92D20]">
                  {error}
                </p>
              </div>

              <button
                type="button"
                onClick={loadDashboard}
                className="rounded-[10px] border border-[#F0A6A6] bg-white px-3 py-2 text-[11px] font-bold text-[#B42318]"
              >
                Retry
              </button>
            </div>
          </div>
        )}

        {/* =====================================================
            SYSTEM STATUS
        ====================================================== */}

        <div className="mb-5 rounded-[20px] border border-[#E5EAF0] bg-white p-5 shadow-[0_8px_25px_rgba(23,33,43,0.035)]">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-full bg-[#EAF8F0] text-[#16804A]">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#16804A] opacity-30" />
                  <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-[#16804A]" />
                </span>
              </div>

              <div>
                <p className="text-[13px] font-extrabold text-[#17212B]">
                  Auto Publishing System
                </p>

                <p className="mt-0.5 text-[11px] text-[#6B7785]">
                  Background publisher is configured
                  to process one post every 20 minutes.
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-5">
              <div>
                <p className="text-[9px] font-bold uppercase tracking-[0.3px] text-[#98A2B3]">
                  Interval
                </p>

                <p className="mt-1 text-[12px] font-extrabold text-[#17212B]">
                  20 minutes
                </p>
              </div>

              <div>
                <p className="text-[9px] font-bold uppercase tracking-[0.3px] text-[#98A2B3]">
                  Active
                </p>

                <p className="mt-1 inline-flex items-center gap-1.5 text-[12px] font-extrabold text-[#16804A]">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#16804A]" />
                  {loading
                    ? "Checking..."
                    : (statistics?.active ?? 0) > 0
                    ? "Yes"
                    : "No"}
                </p>
              </div>

              <div>
                <p className="text-[9px] font-bold uppercase tracking-[0.3px] text-[#98A2B3]">
                  Next Publish
                </p>

                <p className="mt-1 text-[12px] font-extrabold text-[#17212B]">
                  {loading
                    ? "—"
                    : formatDate(
                        statistics?.next_scheduled_at ??
                          null
                      )}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* =====================================================
            SUMMARY
        ====================================================== */}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="rounded-[18px] border border-[#E5EAF0] bg-white p-5 shadow-[0_8px_25px_rgba(23,33,43,0.035)]"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-[11px] font-bold text-[#6B7785]">
                    {stat.label}
                  </p>

                  <p className="mt-3 text-[25px] font-extrabold text-[#17212B]">
                    {stat.value}
                  </p>

                  <p className="mt-1 text-[10px] text-[#98A2B3]">
                    {stat.description}
                  </p>
                </div>

                <div
                  className={`flex h-9 w-9 items-center justify-center rounded-[10px] ${stat.iconClass}`}
                >
                  {stat.icon}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* =====================================================
            MAIN CONTENT
        ====================================================== */}

        <div className="mt-5 grid grid-cols-1 gap-5 xl:grid-cols-[1.35fr_0.65fr]">
          {/* ===================================================
              QUEUE
          ==================================================== */}

          <div className="rounded-[20px] border border-[#E5EAF0] bg-white p-6 shadow-[0_8px_25px_rgba(23,33,43,0.035)]">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-[16px] font-extrabold text-[#17212B]">
                  Publishing Queue
                </h2>

                <p className="mt-1 text-[12px] text-[#6B7785]">
                  Posts waiting for automatic publishing.
                </p>
              </div>

              <Link
                href="/telegram/auto-publisher/queue"
                className="inline-flex items-center gap-1.5 text-[11px] font-bold text-[#229ED9]"
              >
                View Queue
                {icons.arrow}
              </Link>
            </div>

            {loading && (
              <div className="mt-6 flex min-h-[190px] items-center justify-center rounded-[14px] border border-dashed border-[#DCE3EA] bg-[#FAFBFC]">
                <div className="text-center">
                  <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-[#EAF6FC] text-[#229ED9]">
                    <span className="animate-pulse">
                      ✦
                    </span>
                  </div>

                  <p className="mt-3 text-[12px] font-bold text-[#17212B]">
                    Loading queue
                  </p>

                  <p className="mt-1 text-[10px] text-[#98A2B3]">
                    Fetching scheduled content.
                  </p>
                </div>
              </div>
            )}

            {!loading &&
              !error &&
              queuedPosts.length === 0 && (
                <div className="mt-6 flex min-h-[190px] items-center justify-center rounded-[14px] border border-dashed border-[#DCE3EA] bg-[#FAFBFC]">
                  <div className="text-center">
                    <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-[#EAF6FC] text-[#229ED9]">
                      {icons.calendar}
                    </div>

                    <p className="mt-3 text-[12px] font-bold text-[#17212B]">
                      Queue is empty
                    </p>

                    <p className="mt-1 text-[10px] text-[#98A2B3]">
                      Create and queue content to
                      start automatic publishing.
                    </p>

                    <Link
                      href="/telegram/auto-publisher/create"
                      className="mt-4 inline-flex items-center gap-1.5 text-[11px] font-bold text-[#229ED9]"
                    >
                      Create Post
                      {icons.arrow}
                    </Link>
                  </div>
                </div>
              )}

            {!loading &&
              !error &&
              queuedPosts.length > 0 && (
                <div className="mt-5 space-y-3">
                  {queuedPosts.map((post) => (
                    <Link
                      href={`/telegram/auto-publisher/${post.id}`}
                      key={post.id}
                      className="block rounded-[14px] border border-[#E8EDF2] bg-[#FAFBFC] p-4 transition hover:border-[#D6EAF4] hover:bg-[#F8FCFE]"
                    >
                      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="truncate text-[12px] font-extrabold text-[#17212B]">
                              {post.title}
                            </p>

                            <span
                              className={`rounded-full px-2.5 py-1 text-[9px] font-extrabold ${getTypeClasses(
                                post.content_type
                              )}`}
                            >
                              {getTypeLabel(
                                post.content_type
                              )}
                            </span>

                            <span
                              className={`rounded-full px-2.5 py-1 text-[9px] font-extrabold ${getStatusClasses(
                                post.status
                              )}`}
                            >
                              {getStatusLabel(
                                post.status
                              )}
                            </span>
                          </div>

                          <p className="mt-1.5 truncate text-[10px] text-[#6B7785]">
                            {post.message ||
                              post.caption ||
                              post.link_url ||
                              "No preview available."}
                          </p>
                        </div>

                        <div className="flex shrink-0 items-center gap-6">
                          <div>
                            <p className="text-[9px] font-bold uppercase tracking-[0.3px] text-[#98A2B3]">
                              Scheduled
                            </p>

                            <p className="mt-0.5 text-[11px] font-semibold text-[#6B7785]">
                              {formatDate(
                                post.scheduled_at
                              )}
                            </p>
                          </div>

                          <span className="text-[#98A2B3]">
                            {icons.arrow}
                          </span>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
          </div>

          {/* ===================================================
              QUICK ACTIONS
          ==================================================== */}

          <div className="rounded-[20px] border border-[#E5EAF0] bg-white p-6 shadow-[0_8px_25px_rgba(23,33,43,0.035)]">
            <div>
              <h2 className="text-[16px] font-extrabold text-[#17212B]">
                Quick Actions
              </h2>

              <p className="mt-1 text-[12px] text-[#6B7785]">
                Manage your automated Telegram content.
              </p>
            </div>

            <div className="mt-5 space-y-3">
              <Link
                href="/telegram/auto-publisher/create"
                className="group flex items-center justify-between rounded-[14px] border border-[#E8EDF2] bg-[#FAFBFC] p-4 transition hover:border-[#D6EAF4] hover:bg-[#F8FCFE]"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-[10px] bg-[#EAF6FC] text-[#229ED9]">
                    {icons.plus}
                  </div>

                  <div>
                    <p className="text-[11px] font-extrabold text-[#17212B]">
                      Create Post
                    </p>

                    <p className="mt-0.5 text-[10px] text-[#98A2B3]">
                      Add new automated content
                    </p>
                  </div>
                </div>

                <span className="text-[#98A2B3] transition group-hover:text-[#229ED9]">
                  {icons.arrow}
                </span>
              </Link>

              <Link
                href="/telegram/auto-publisher/queue"
                className="group flex items-center justify-between rounded-[14px] border border-[#E8EDF2] bg-[#FAFBFC] p-4 transition hover:border-[#D6EAF4] hover:bg-[#F8FCFE]"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-[10px] bg-[#F1EEFF] text-[#6B5DD3]">
                    {icons.calendar}
                  </div>

                  <div>
                    <p className="text-[11px] font-extrabold text-[#17212B]">
                      Content Queue
                    </p>

                    <p className="mt-0.5 text-[10px] text-[#98A2B3]">
                      Manage scheduled posts
                    </p>
                  </div>
                </div>

                <span className="text-[#98A2B3] transition group-hover:text-[#229ED9]">
                  {icons.arrow}
                </span>
              </Link>

              <Link
                href="/telegram/auto-publisher/history"
                className="group flex items-center justify-between rounded-[14px] border border-[#E8EDF2] bg-[#FAFBFC] p-4 transition hover:border-[#D6EAF4] hover:bg-[#F8FCFE]"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-[10px] bg-[#EAF8F0] text-[#16804A]">
                    {icons.check}
                  </div>

                  <div>
                    <p className="text-[11px] font-extrabold text-[#17212B]">
                      Publishing History
                    </p>

                    <p className="mt-0.5 text-[10px] text-[#98A2B3]">
                      Review previous publications
                    </p>
                  </div>
                </div>

                <span className="text-[#98A2B3] transition group-hover:text-[#229ED9]">
                  {icons.arrow}
                </span>
              </Link>
            </div>
          </div>
        </div>

        {/* =====================================================
            RECENT ACTIVITY
        ====================================================== */}

        <div className="mt-5 rounded-[20px] border border-[#E5EAF0] bg-white p-6 shadow-[0_8px_25px_rgba(23,33,43,0.035)]">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-[16px] font-extrabold text-[#17212B]">
                Recent Publishing Activity
              </h2>

              <p className="mt-1 text-[12px] text-[#6B7785]">
                Latest automatically processed content.
              </p>
            </div>

            <Link
              href="/telegram/auto-publisher/history"
              className="inline-flex items-center gap-1.5 text-[11px] font-bold text-[#229ED9]"
            >
              View History
              {icons.arrow}
            </Link>
          </div>

          {loading && (
            <div className="mt-6 flex min-h-[160px] items-center justify-center rounded-[14px] border border-dashed border-[#DCE3EA] bg-[#FAFBFC]">
              <p className="text-[11px] font-semibold text-[#98A2B3]">
                Loading activity...
              </p>
            </div>
          )}

          {!loading &&
            !error &&
            recentPosts.length === 0 && (
              <div className="mt-6 flex min-h-[160px] items-center justify-center rounded-[14px] border border-dashed border-[#DCE3EA] bg-[#FAFBFC]">
                <div className="text-center">
                  <p className="text-[12px] font-bold text-[#17212B]">
                    No publishing activity
                  </p>

                  <p className="mt-1 text-[10px] text-[#98A2B3]">
                    Published and failed posts will
                    appear here.
                  </p>
                </div>
              </div>
            )}

          {!loading &&
            !error &&
            recentPosts.length > 0 && (
              <div className="mt-5 overflow-x-auto">
                <div className="min-w-[720px]">
                  <div className="grid grid-cols-[1.6fr_0.7fr_0.8fr_1.1fr] gap-4 border-b border-[#EEF1F4] px-3 pb-3">
                    <p className="text-[9px] font-bold uppercase tracking-[0.3px] text-[#98A2B3]">
                      Content
                    </p>

                    <p className="text-[9px] font-bold uppercase tracking-[0.3px] text-[#98A2B3]">
                      Type
                    </p>

                    <p className="text-[9px] font-bold uppercase tracking-[0.3px] text-[#98A2B3]">
                      Status
                    </p>

                    <p className="text-right text-[9px] font-bold uppercase tracking-[0.3px] text-[#98A2B3]">
                      Published
                    </p>
                  </div>

                  <div className="divide-y divide-[#EEF1F4]">
                    {recentPosts.map((post) => (
                      <Link
                        href={`/telegram/auto-publisher/${post.id}`}
                        key={post.id}
                        className="grid grid-cols-[1.6fr_0.7fr_0.8fr_1.1fr] gap-4 px-3 py-4 transition hover:bg-[#FAFBFC]"
                      >
                        <div className="min-w-0">
                          <p className="truncate text-[11px] font-extrabold text-[#17212B]">
                            {post.title}
                          </p>

                          {post.telegram_message_id && (
                            <p className="mt-0.5 text-[9px] text-[#98A2B3]">
                              Telegram message #
                              {post.telegram_message_id}
                            </p>
                          )}
                        </div>

                        <div>
                          <span
                            className={`inline-flex rounded-full px-2.5 py-1 text-[9px] font-extrabold ${getTypeClasses(
                              post.content_type
                            )}`}
                          >
                            {getTypeLabel(
                              post.content_type
                            )}
                          </span>
                        </div>

                        <div>
                          <span
                            className={`inline-flex rounded-full px-2.5 py-1 text-[9px] font-extrabold ${getStatusClasses(
                              post.status
                            )}`}
                          >
                            {getStatusLabel(
                              post.status
                            )}
                          </span>
                        </div>

                        <p className="text-right text-[10px] font-semibold text-[#6B7785]">
                          {formatDate(
                            post.published_at ||
                              post.updated_at
                          )}
                        </p>
                      </Link>
                    ))}
                  </div>
                </div>
              </div>
            )}
        </div>
      </div>
    </AdminShell>
  );
}
 
