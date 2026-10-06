"use client";

import { useCallback, useEffect, useState } from "react";
import AdminShell from "@/components/layout/AdminShell";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

interface Signal {
  id: string;
  signal_number: string;
  game: string;
  board_size: number;
  mine_count: number;
  model_id: string | null;
  confidence: number | null;
  attempts: number;
  recommended_positions: number[];
  status: string;
  model_version: string | null;
  generated_at: string;
  published_at: string | null;
  confirmed_at: string | null;
  result_status: string | null;
}

interface DashboardData {
  signals_today: number;
  published: number;
  pending_results: number;
  telegram_status: string;
  recent_signals: Signal[];
  generated_at: string;
}

export default function DashboardPage() {
  const [dashboard, setDashboard] =
    useState<DashboardData | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  const loadDashboard = useCallback(
    async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch(
          `${API_URL}/api/dashboard`,
          {
            method: "GET",
            credentials: "include",
            cache: "no-store",
          }
        );

        if (!response.ok) {
          let message =
            "Unable to load dashboard.";

          try {
            const body =
              await response.json();

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

        const data =
          (await response.json()) as DashboardData;

        setDashboard(data);
      } catch (error) {
        setError(
          error instanceof Error
            ? error.message
            : "Unable to load dashboard."
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

  const formatDate = (
    value: string
  ) => {
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

  const getStatusLabel = (
    status: string
  ) => {
    switch (status) {
      case "DRAFT":
        return "Draft";

      case "ANALYZED":
        return "Analyzed";

      case "CONFIRMED":
        return "Confirmed";

      case "PUBLISHED":
        return "Published";

      case "RESULT_PENDING":
        return "Pending Result";

      case "SUCCESS":
        return "Success";

      case "FAILED":
        return "Failed";

      default:
        return status;
    }
  };

  const getStatusClasses = (
    status: string
  ) => {
    switch (status) {
      case "SUCCESS":
        return "bg-[#EAF8F0] text-[#16804A]";

      case "FAILED":
        return "bg-[#FFF0F0] text-[#D92D20]";

      case "RESULT_PENDING":
        return "bg-[#FFF7E6] text-[#B7791F]";

      case "PUBLISHED":
        return "bg-[#EAF6FC] text-[#229ED9]";

      case "CONFIRMED":
        return "bg-[#F1EEFF] text-[#6B5DD3]";

      case "ANALYZED":
        return "bg-[#F1EEFF] text-[#6B5DD3]";

      default:
        return "bg-[#F2F4F7] text-[#667085]";
    }
  };

  const stats = [
    {
      label: "Signals Today",
      value: loading
        ? "—"
        : String(
            dashboard?.signals_today ?? 0
          ),
    },
    {
      label: "Published",
      value: loading
        ? "—"
        : String(
            dashboard?.published ?? 0
          ),
    },
    {
      label: "Pending Results",
      value: loading
        ? "—"
        : String(
            dashboard?.pending_results ?? 0
          ),
    },
    {
      label: "Telegram",
      value: loading
        ? "—"
        : dashboard?.telegram_status ===
          "CONNECTED"
        ? "Connected"
        : "Offline",
    },
  ];

  return (
    <AdminShell>
      <div>
        {/* =====================================================
            PAGE HEADER
        ====================================================== */}

        <div className="mb-7">
          <h1 className="text-[26px] font-extrabold tracking-[-0.5px] text-[#17212B]">
            Dashboard
          </h1>

          <p className="mt-1.5 text-[13px] text-[#6B7785]">
            Overview of your Mines Signal System.
          </p>
        </div>

        {/* =====================================================
            ERROR
        ====================================================== */}

        {error && (
          <div className="mb-5 rounded-[16px] border border-[#F5C2C7] bg-[#FFF5F5] px-5 py-4">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-[12px] font-bold text-[#B42318]">
                  Dashboard unavailable
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
            SUMMARY
        ====================================================== */}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="rounded-[18px] border border-[#E5EAF0] bg-white p-5 shadow-[0_8px_25px_rgba(23,33,43,0.035)]"
            >
              <p className="text-[11px] font-bold text-[#6B7785]">
                {stat.label}
              </p>

              <p className="mt-3 text-[25px] font-extrabold text-[#17212B]">
                {stat.value}
              </p>
            </div>
          ))}
        </div>

        {/* =====================================================
            RECENT SIGNALS
        ====================================================== */}

        <div className="mt-5 rounded-[20px] border border-[#E5EAF0] bg-white p-6 shadow-[0_8px_25px_rgba(23,33,43,0.035)]">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-[16px] font-extrabold text-[#17212B]">
                Recent Signals
              </h2>

              <p className="mt-1 text-[12px] text-[#6B7785]">
                Your latest generated signals.
              </p>
            </div>

            {!loading &&
              dashboard &&
              dashboard.recent_signals.length > 0 && (
                <button
                  type="button"
                  onClick={loadDashboard}
                  className="text-[11px] font-bold text-[#229ED9]"
                >
                  Refresh
                </button>
              )}
          </div>

          {/* ===================================================
              LOADING
          ==================================================== */}

          {loading && (
            <div className="mt-8 flex min-h-[180px] items-center justify-center rounded-[14px] border border-dashed border-[#DCE3EA] bg-[#FAFBFC]">
              <div className="text-center">
                <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-[#EAF6FC] text-[#229ED9]">
                  <span className="animate-pulse">
                    ✦
                  </span>
                </div>

                <p className="mt-3 text-[12px] font-bold text-[#17212B]">
                  Loading signals
                </p>

                <p className="mt-1 text-[10px] text-[#98A2B3]">
                  Fetching the latest system activity.
                </p>
              </div>
            </div>
          )}

          {/* ===================================================
              EMPTY
          ==================================================== */}

          {!loading &&
            !error &&
            dashboard &&
            dashboard.recent_signals.length ===
              0 && (
              <div className="mt-8 flex min-h-[180px] items-center justify-center rounded-[14px] border border-dashed border-[#DCE3EA] bg-[#FAFBFC]">
                <div className="text-center">
                  <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-[#EAF6FC] text-[#229ED9]">
                    ✦
                  </div>

                  <p className="mt-3 text-[12px] font-bold text-[#17212B]">
                    No signals yet
                  </p>

                  <p className="mt-1 text-[10px] text-[#98A2B3]">
                    Create your first signal to
                    get started.
                  </p>
                </div>
              </div>
            )}

          {/* ===================================================
              SIGNAL LIST
          ==================================================== */}

          {!loading &&
            !error &&
            dashboard &&
            dashboard.recent_signals.length >
              0 && (
              <div className="mt-6 space-y-3">
                {dashboard.recent_signals.map(
                  (signal) => (
                    <div
                      key={signal.id}
                      className="rounded-[14px] border border-[#E8EDF2] bg-[#FAFBFC] p-4"
                    >
                      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                        {/* -----------------------------------
                            SIGNAL INFO
                        ------------------------------------ */}

                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="text-[12px] font-extrabold text-[#17212B]">
                              {signal.signal_number}
                            </span>

                            <span
                              className={`rounded-full px-2.5 py-1 text-[9px] font-extrabold ${getStatusClasses(
                                signal.status
                              )}`}
                            >
                              {getStatusLabel(
                                signal.status
                              )}
                            </span>
                          </div>

                          <p className="mt-1 text-[11px] text-[#6B7785]">
                            {signal.game}
                          </p>
                        </div>

                        {/* -----------------------------------
                            CONFIGURATION
                        ------------------------------------ */}

                        <div className="grid grid-cols-2 gap-x-8 gap-y-2 sm:grid-cols-4 lg:min-w-[430px]">
                          <div>
                            <p className="text-[9px] font-bold uppercase tracking-[0.3px] text-[#98A2B3]">
                              Board
                            </p>

                            <p className="mt-0.5 text-[11px] font-bold text-[#17212B]">
                              {signal.board_size} ×{" "}
                              {signal.board_size}
                            </p>
                          </div>

                          <div>
                            <p className="text-[9px] font-bold uppercase tracking-[0.3px] text-[#98A2B3]">
                              Mines
                            </p>

                            <p className="mt-0.5 text-[11px] font-bold text-[#17212B]">
                              {signal.mine_count}
                            </p>
                          </div>

                          <div>
                            <p className="text-[9px] font-bold uppercase tracking-[0.3px] text-[#98A2B3]">
                              Confidence
                            </p>

                            <p className="mt-0.5 text-[11px] font-bold text-[#17212B]">
                              {signal.confidence !==
                              null
                                ? `${signal.confidence}%`
                                : "—"}
                            </p>
                          </div>

                          <div>
                            <p className="text-[9px] font-bold uppercase tracking-[0.3px] text-[#98A2B3]">
                              Attempts
                            </p>

                            <p className="mt-0.5 text-[11px] font-bold text-[#17212B]">
                              {signal.attempts}
                            </p>
                          </div>
                        </div>

                        {/* -----------------------------------
                            DATE
                        ------------------------------------ */}

                        <div className="lg:min-w-[155px] lg:text-right">
                          <p className="text-[9px] font-bold uppercase tracking-[0.3px] text-[#98A2B3]">
                            Generated
                          </p>

                          <p className="mt-0.5 text-[11px] font-semibold text-[#6B7785]">
                            {formatDate(
                              signal.generated_at
                            )}
                          </p>
                        </div>
                      </div>
                    </div>
                  )
                )}
              </div>
            )}
        </div>
      </div>
    </AdminShell>
  );
}
 
