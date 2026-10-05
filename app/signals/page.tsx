"use client";

import {
  useEffect,
  useMemo,
  useState,
} from "react";
import Link from "next/link";
import AdminShell from "@/components/layout/AdminShell";

type SignalStatus =
  | "DRAFT"
  | "ANALYZED"
  | "CONFIRMED"
  | "PUBLISHED"
  | "RESULT_PENDING"
  | "SUCCESS"
  | "FAILED";

type ApiSignal = {
  id: string;
  signal_number: string;
  game: string;
  board_size: number;
  mine_count: number;
  confidence: number | null;
  attempts: number;
  recommended_positions: number[];
  status: SignalStatus;
  model_version: string | null;
  generated_at: string;
  published_at: string | null;
  confirmed_at: string | null;
  result_status: string | null;
};

type Signal = {
  id: string;
  signalNumber: string;
  game: string;
  boardSize: number;
  mineCount: number;
  confidence: number | null;
  attempts: number;
  safePositions: number[];
  status: SignalStatus;
  telegramStatus:
    | "Published"
    | "Not Published"
    | "Pending";
  modelVersion: string | null;
  createdAt: string;
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

const PAGE_SIZE = 10;

export default function SignalsPage() {
  const [signals, setSignals] = useState<Signal[]>(
    []
  );

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [search, setSearch] =
    useState("");

  const [statusFilter, setStatusFilter] =
    useState("All Status");

  const [mineFilter, setMineFilter] =
    useState("All Mines");

  const [currentPage, setCurrentPage] =
    useState(1);

  /*
   * ----------------------------------------------------------
   * LOAD SIGNALS
   * ----------------------------------------------------------
   */

  const loadSignals = async () => {
  setLoading(true);
  setError("");

  try {
    const response = await fetch(
      `${API_URL}/api/signals`,
      {
        method: "GET",
        credentials: "include",
        cache: "no-store",
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
          "Unable to load signals."
      );
      return;
    }

    const apiSignals: ApiSignal[] =
      Array.isArray(data?.items)
        ? data.items
        : [];

    const mappedSignals: Signal[] =
      apiSignals.map((signal) => ({
        id: signal.id,
        signalNumber:
          signal.signal_number,
        game: signal.game,
        boardSize:
          signal.board_size,
        mineCount:
          signal.mine_count,
        confidence:
          signal.confidence,
        attempts:
          signal.attempts,
        safePositions:
          Array.isArray(
            signal.recommended_positions
          )
            ? signal.recommended_positions
            : [],
        status:
          signal.status,
        telegramStatus:
          getTelegramStatus(signal),
        modelVersion:
          signal.model_version,
        createdAt:
          formatDate(
            signal.generated_at
          ),
      }));

    setSignals(mappedSignals);
    setCurrentPage(1);
  } catch (requestError) {
    console.error(
      "Failed to load signals:",
      requestError
    );

    setError(
      "Unable to connect to the signal server."
    );
  } finally {
    setLoading(false);
  }
};

useEffect(() => {
  let cancelled = false;

  const load = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `${API_URL}/api/signals`,
        {
          method: "GET",
          credentials: "include",
          cache: "no-store",
        }
      );

      let data: any = null;

      try {
        data = await response.json();
      } catch {
        data = null;
      }

      if (cancelled) {
        return;
      }

      if (!response.ok) {
        setError(
          data?.detail ||
            "Unable to load signals."
        );
        return;
      }

      const apiSignals: ApiSignal[] =
        Array.isArray(data?.items)
          ? data.items
          : [];

      const mappedSignals: Signal[] =
        apiSignals.map((signal) => ({
          id: signal.id,
          signalNumber:
            signal.signal_number,
          game: signal.game,
          boardSize:
            signal.board_size,
          mineCount:
            signal.mine_count,
          confidence:
            signal.confidence,
          attempts:
            signal.attempts,
          safePositions:
            Array.isArray(
              signal.recommended_positions
            )
              ? signal.recommended_positions
              : [],
          status:
            signal.status,
          telegramStatus:
            getTelegramStatus(signal),
          modelVersion:
            signal.model_version,
          createdAt:
            formatDate(
              signal.generated_at
            ),
        }));

      setSignals(mappedSignals);
      setCurrentPage(1);
    } catch (requestError) {
      if (cancelled) {
        return;
      }

      console.error(
        "Failed to load signals:",
        requestError
      );

      setError(
        "Unable to connect to the signal server."
      );
    } finally {
      if (!cancelled) {
        setLoading(false);
      }
    }
  };

  load();

  return () => {
    cancelled = true;
  };
}, []);

// useEffect(() => {
//   loadSignals();
// }, []);
  // const loadSignals = async () => {
  //   setLoading(true);
  //   setError("");

  //   try {
  //     const response = await fetch(
  //       `${API_URL}/api/signals`,
  //       {
  //         method: "GET",
  //         credentials: "include",
  //         cache: "no-store",
  //       }
  //     );

  //     let data: any = null;

  //     try {
  //       data = await response.json();
  //     } catch {
  //       data = null;
  //     }

  //     if (!response.ok) {
  //       setError(
  //         data?.detail ||
  //           "Unable to load signals."
  //       );
  //       return;
  //     }

  //     const apiSignals: ApiSignal[] =
  //       Array.isArray(data?.items)
  //         ? data.items
  //         : [];

  //     const mappedSignals: Signal[] =
  //       apiSignals.map((signal) => ({
  //         id: signal.id,
  //         signalNumber:
  //           signal.signal_number,
  //         game: signal.game,
  //         boardSize:
  //           signal.board_size,
  //         mineCount:
  //           signal.mine_count,
  //         confidence:
  //           signal.confidence,
  //         attempts:
  //           signal.attempts,
  //         safePositions:
  //           Array.isArray(
  //             signal.recommended_positions
  //           )
  //             ? signal.recommended_positions
  //             : [],
  //         status:
  //           signal.status,
  //         telegramStatus:
  //           getTelegramStatus(signal),
  //         modelVersion:
  //           signal.model_version,
  //         createdAt:
  //           formatDate(signal.generated_at),
  //       }));

  //     setSignals(mappedSignals);
  //     setCurrentPage(1);
  //   } catch (requestError) {
  //     console.error(
  //       "Failed to load signals:",
  //       requestError
  //     );

  //     setError(
  //       "Unable to connect to the signal server."
  //     );
  //   } finally {
  //     setLoading(false);
  //   }
  // };

  /*
   * Load on first render.
   *
   * We intentionally use a small effect wrapper below instead
   * of changing the page structure.
   */

  // useEffect(() => {
  //   loadSignals();
  //  }, []);

  // useState(() => {
  //   loadSignals();
  // }, []);

  /*
   * ----------------------------------------------------------
   * FILTERING
   * ----------------------------------------------------------
   */

  const filteredSignals = useMemo(() => {
    const normalizedSearch =
      search.trim().toLowerCase();

    return signals.filter((signal) => {
      const matchesSearch =
        !normalizedSearch ||
        signal.signalNumber
          .toLowerCase()
          .includes(normalizedSearch) ||
        signal.game
          .toLowerCase()
          .includes(normalizedSearch);

      const matchesStatus =
        statusFilter === "All Status" ||
        signal.status === statusFilter;

      const matchesMines =
        mineFilter === "All Mines" ||
        signal.mineCount.toString() ===
          mineFilter;

      return (
        matchesSearch &&
        matchesStatus &&
        matchesMines
      );
    });
  }, [
    signals,
    search,
    statusFilter,
    mineFilter,
  ]);

  /*
   * ----------------------------------------------------------
   * PAGINATION
   * ----------------------------------------------------------
   */

  const totalPages = Math.max(
    1,
    Math.ceil(
      filteredSignals.length / PAGE_SIZE
    )
  );

  const safeCurrentPage = Math.min(
    currentPage,
    totalPages
  );

  const paginatedSignals =
    filteredSignals.slice(
      (safeCurrentPage - 1) *
        PAGE_SIZE,
      safeCurrentPage * PAGE_SIZE
    );

  /*
   * ----------------------------------------------------------
   * STATS
   * ----------------------------------------------------------
   */

  const totalSignals =
    signals.length;

  const confirmedSignals =
    signals.filter(
      (signal) =>
        signal.status === "CONFIRMED"
    ).length;

  const pendingResults =
    signals.filter(
      (signal) =>
        signal.status ===
        "RESULT_PENDING"
    ).length;

  const publishedSignals =
    signals.filter(
      (signal) =>
        signal.status ===
          "PUBLISHED" ||
        signal.status ===
          "RESULT_PENDING" ||
        signal.status === "SUCCESS" ||
        signal.status === "FAILED"
    ).length;

  /*
   * ----------------------------------------------------------
   * RESET
   * ----------------------------------------------------------
   */

  const resetFilters = () => {
    setSearch("");
    setStatusFilter("All Status");
    setMineFilter("All Mines");
    setCurrentPage(1);
  };

  /*
   * ----------------------------------------------------------
   * PAGE
   * ----------------------------------------------------------
   */

  return (
    <AdminShell>
      <div className="signals-page">

        {/* PAGE HEADER */}

        <div className="page-header">

          <div>

            <div className="breadcrumb">
              Dashboard <span>/</span> Signals
            </div>

            <h1>Signals</h1>

            <p>
              Manage, review and monitor generated
              Mines signals.
            </p>

          </div>

          <Link
            href="/signals/create"
            className="primary-button"
          >
            <span>+</span>
            Create Signal
          </Link>

        </div>

        {/* ERROR */}

        {error && (
          <div
            style={{
              marginBottom: "18px",
              padding: "14px 16px",
              borderRadius: "12px",
              background: "#fef2f2",
              border:
                "1px solid #fecaca",
              color: "#b91c1c",
              display: "flex",
              alignItems: "center",
              justifyContent:
                "space-between",
              gap: "16px",
            }}
          >
            <span>{error}</span>

            <button
              type="button"
              onClick={loadSignals}
              style={{
                border: 0,
                background:
                  "transparent",
                color: "#b91c1c",
                fontWeight: 700,
                cursor: "pointer",
              }}
            >
              Retry
            </button>
          </div>
        )}

        {/* STAT CARDS */}

        <div className="signal-stats">

          <StatCard
            label="Total Signals"
            value={
              loading
                ? "—"
                : String(totalSignals)
            }
            icon="▦"
            description="All generated signals"
          />

          <StatCard
            label="Entry Confirmed"
            value={
              loading
                ? "—"
                : String(
                    confirmedSignals
                  )
            }
            icon="✓"
            description="Ready for publishing"
            accent="blue"
          />

          <StatCard
            label="Pending Results"
            value={
              loading
                ? "—"
                : String(
                    pendingResults
                  )
            }
            icon="◷"
            description="Awaiting game results"
            accent="orange"
          />

          <StatCard
            label="Published"
            value={
              loading
                ? "—"
                : String(
                    publishedSignals
                  )
            }
            icon="↗"
            description="Published signals"
            accent="green"
          />

        </div>

        {/* MAIN CARD */}

        <div className="signals-card">

          {/* CARD HEADER */}

          <div className="signals-card-header">

            <div>

              <h2>Signal History</h2>

              <p>
                Review generated signals and
                their current status.
              </p>

            </div>

            <button
              type="button"
              className="filter-button"
              onClick={() => {
                document
                  .querySelector(
                    ".signals-filters"
                  )
                  ?.scrollIntoView({
                    behavior: "smooth",
                    block: "center",
                  });
              }}
            >
              <span>☷</span>
              Filters
            </button>

          </div>

          {/* FILTER BAR */}

          <div className="signals-filters">

            <div className="search-box">

              <span>⌕</span>

              <input
                type="text"
                placeholder="Search signal number..."
                value={search}
                onChange={(event) => {
                  setSearch(
                    event.target.value
                  );
                  setCurrentPage(1);
                }}
              />

            </div>

            <select
              value={statusFilter}
              onChange={(event) => {
                setStatusFilter(
                  event.target.value
                );
                setCurrentPage(1);
              }}
            >
              <option>
                All Status
              </option>

              <option>DRAFT</option>
              <option>ANALYZED</option>
              <option>CONFIRMED</option>
              <option>PUBLISHED</option>
              <option>
                RESULT_PENDING
              </option>
              <option>SUCCESS</option>
              <option>FAILED</option>
            </select>

            <select
              value={mineFilter}
              onChange={(event) => {
                setMineFilter(
                  event.target.value
                );
                setCurrentPage(1);
              }}
            >
              <option>
                All Mines
              </option>

              <option value="3">
                3 Mines
              </option>

              <option value="5">
                5 Mines
              </option>

              <option value="7">
                7 Mines
              </option>
            </select>

            <button
              type="button"
              className="reset-button"
              onClick={
                resetFilters
              }
            >
              Reset
            </button>

          </div>

          {/* LOADING */}

          {loading ? (
            <div
              style={{
                padding:
                  "60px 20px",
                textAlign:
                  "center",
                color: "#6B7785",
              }}
            >
              <div
                style={{
                  width: "30px",
                  height: "30px",
                  margin:
                    "0 auto 14px",
                  border:
                    "3px solid #E5EAF0",
                  borderTopColor:
                    "#229ED9",
                  borderRadius:
                    "50%",
                  animation:
                    "signal-spin 0.8s linear infinite",
                }}
              />

              <p>
                Loading signals...
              </p>
            </div>
          ) : (
            <>
              {/* DESKTOP TABLE */}

              <div className="signals-table-wrapper">

                <table className="signals-table">

                  <thead>
                    <tr>
                      <th>
                        Signal
                      </th>

                      <th>
                        Board
                      </th>

                      <th>
                        Confidence
                      </th>

                      <th>
                        Attempts
                      </th>

                      <th>
                        Telegram
                      </th>

                      <th>
                        Status
                      </th>

                      <th>
                        Created
                      </th>

                      <th />
                    </tr>
                  </thead>

                  <tbody>

                    {paginatedSignals.map(
                      (signal) => (
                        <tr
                          key={signal.id}
                          onClick={() =>
                            window.location.href =
                              `/signals/${signal.id}`
                          }
                          style={{
                            cursor:
                              "pointer",
                          }}
                        >

                          <td>

                            <div className="signal-id">

                              <div className="signal-icon">
                                ✦
                              </div>

                              <div>

                                <strong>
                                  {
                                    signal.signalNumber
                                  }
                                </strong>

                                <span>
                                  {
                                    signal.game
                                  }
                                </span>

                              </div>

                            </div>

                          </td>

                          <td>

                            <div className="board-cell">

                              <MiniBoard
                                positions={
                                  signal.safePositions
                                }
                              />

                              <div className="board-info">

                                <strong>
                                  {
                                    signal.boardSize
                                  }{" "}
                                  ×{" "}
                                  {
                                    signal.boardSize
                                  }
                                </strong>

                                <span>
                                  {
                                    signal.mineCount
                                  }{" "}
                                  mines
                                </span>

                              </div>

                            </div>

                          </td>

                          <td>

                            <Confidence
                              value={
                                signal.confidence
                              }
                            />

                          </td>

                          <td>

                            <span className="attempt-badge">
                              {
                                signal.attempts
                              }
                            </span>

                          </td>

                          <td>

                            <TelegramStatus
                              status={
                                signal.telegramStatus
                              }
                            />

                          </td>

                          <td>

                            <StatusBadge
                              status={
                                signal.status
                              }
                            />

                          </td>

                          <td>

                            <span className="created-date">
                              {
                                signal.createdAt
                              }
                            </span>

                          </td>

                          <td>

                            <button
                              type="button"
                              className="action-button"
                              onClick={(
                                event
                              ) => {
                                event.stopPropagation();

                                window.location.href =
                                  `/signals/${signal.id}`;
                              }}
                            >
                              ⋮
                            </button>

                          </td>

                        </tr>
                      )
                    )}

                  </tbody>

                </table>

              </div>

              {/* MOBILE CARDS */}

              <div className="signals-mobile-list">

                {paginatedSignals.map(
                  (signal) => (
                    <div
                      className="signal-mobile-card"
                      key={signal.id}
                      onClick={() =>
                        window.location.href =
                          `/signals/${signal.id}`
                      }
                      style={{
                        cursor:
                          "pointer",
                      }}
                    >

                      <div className="mobile-card-top">

                        <div className="signal-id">

                          <div className="signal-icon">
                            ✦
                          </div>

                          <div>

                            <strong>
                              {
                                signal.signalNumber
                              }
                            </strong>

                            <span>
                              {
                                signal.createdAt
                              }
                            </span>

                          </div>

                        </div>

                        <StatusBadge
                          status={
                            signal.status
                          }
                        />

                      </div>

                      <div className="mobile-board-section">

                        <MiniBoard
                          positions={
                            signal.safePositions
                          }
                        />

                        <div className="mobile-board-info">

                          <div>
                            <span>
                              Game
                            </span>

                            <strong>
                              {
                                signal.game
                              }
                            </strong>
                          </div>

                          <div>
                            <span>
                              Mines
                            </span>

                            <strong>
                              {
                                signal.mineCount
                              }
                            </strong>
                          </div>

                          <div>
                            <span>
                              Attempts
                            </span>

                            <strong>
                              {
                                signal.attempts
                              }
                            </strong>
                          </div>

                          <div>
                            <span>
                              Confidence
                            </span>

                            <strong>
                              {
                                signal.confidence ===
                                null
                                  ? "—"
                                  : `${signal.confidence}%`
                              }
                            </strong>
                          </div>

                        </div>

                      </div>

                      <div className="mobile-card-footer">

                        <TelegramStatus
                          status={
                            signal.telegramStatus
                          }
                        />

                        <button
                          type="button"
                          className="view-button"
                          onClick={(
                            event
                          ) => {
                            event.stopPropagation();

                            window.location.href =
                              `/signals/${signal.id}`;
                          }}
                        >
                          View Signal
                        </button>

                      </div>

                    </div>
                  )
                )}

              </div>

              {/* EMPTY */}

              {filteredSignals.length ===
                0 && (
                <div className="signals-empty">

                  <div>⌕</div>

                  <h3>
                    No signals found
                  </h3>

                  <p>
                    Try changing your
                    search or filters.
                  </p>

                </div>
              )}

              {/* PAGINATION */}

              <div className="signals-pagination">

                <span>
                  Showing{" "}
                  {filteredSignals.length ===
                  0
                    ? 0
                    : (safeCurrentPage -
                        1) *
                        PAGE_SIZE +
                      1}
                  {" "}–{" "}
                  {Math.min(
                    safeCurrentPage *
                      PAGE_SIZE,
                    filteredSignals.length
                  )}{" "}
                  of{" "}
                  {filteredSignals.length}{" "}
                  signals
                </span>

                <div className="pagination-buttons">

                  <button
                    type="button"
                    disabled={
                      safeCurrentPage <=
                      1
                    }
                    onClick={() =>
                      setCurrentPage(
                        (page) =>
                          Math.max(
                            1,
                            page - 1
                          )
                      )
                    }
                  >
                    ‹
                  </button>

                  {Array.from(
                    {
                      length:
                        totalPages,
                    },
                    (_, index) =>
                      index + 1
                  ).map((page) => (
                    <button
                      type="button"
                      key={page}
                      className={
                        page ===
                        safeCurrentPage
                          ? "active"
                          : ""
                      }
                      onClick={() =>
                        setCurrentPage(
                          page
                        )
                      }
                    >
                      {page}
                    </button>
                  ))}

                  <button
                    type="button"
                    disabled={
                      safeCurrentPage >=
                      totalPages
                    }
                    onClick={() =>
                      setCurrentPage(
                        (page) =>
                          Math.min(
                            totalPages,
                            page + 1
                          )
                      )
                    }
                  >
                    ›
                  </button>

                </div>

              </div>

            </>
          )}

        </div>

      </div>

      <style jsx global>{`
        @keyframes signal-spin {
          from {
            transform: rotate(0deg);
          }

          to {
            transform: rotate(360deg);
          }
        }
      `}</style>
    </AdminShell>
  );
}

/*
 * ------------------------------------------------------------
 * TELEGRAM STATUS
 * ------------------------------------------------------------
 *
 * TelegramMessage data is not currently part of the Signal API.
 * Therefore we derive the display status from the signal
 * lifecycle instead of inventing a Telegram message ID.
 */

function getTelegramStatus(
  signal: ApiSignal
):
  | "Published"
  | "Not Published"
  | "Pending" {

  if (
    signal.status === "PUBLISHED" ||
    signal.status ===
      "RESULT_PENDING" ||
    signal.status === "SUCCESS" ||
    signal.status === "FAILED"
  ) {
    return "Published";
  }

  if (
    signal.status ===
      "CONFIRMED" ||
    signal.status === "ANALYZED"
  ) {
    return "Pending";
  }

  return "Not Published";
}

/*
 * ------------------------------------------------------------
 * DATE
 * ------------------------------------------------------------
 */

function formatDate(
  value: string
): string {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString(
    undefined,
    {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }
  );
}

/*
 * ------------------------------------------------------------
 * STAT CARD
 * ------------------------------------------------------------
 */

function StatCard({
  label,
  value,
  icon,
  description,
  accent,
}: {
  label: string;
  value: string;
  icon: string;
  description: string;
  accent?:
    | "blue"
    | "orange"
    | "green";
}) {
  return (
    <div className="signal-stat-card">

      <div
        className={`stat-icon ${
          accent || ""
        }`}
      >
        {icon}
      </div>

      <div className="stat-content">

        <span>{label}</span>

        <strong>{value}</strong>

        <small>
          {description}
        </small>

      </div>

    </div>
  );
}

/*
 * ------------------------------------------------------------
 * CONFIDENCE
 * ------------------------------------------------------------
 */

function Confidence({
  value,
}: {
  value: number | null;
}) {
  const displayValue =
    value === null ? 0 : value;

  return (
    <div className="confidence">

      <div className="confidence-top">

        <strong>
          {value === null
            ? "—"
            : `${value}%`}
        </strong>

        <span>Model</span>

      </div>

      <div className="confidence-bar">

        <div
          style={{
            width: `${Math.max(
              0,
              Math.min(
                100,
                displayValue
              )
            )}%`,
          }}
        />

      </div>

    </div>
  );
}

/*
 * ------------------------------------------------------------
 * STATUS
 * ------------------------------------------------------------
 */

function StatusBadge({
  status,
}: {
  status: SignalStatus;
}) {
  const labels: Record<
    SignalStatus,
    string
  > = {
    DRAFT: "Draft",
    ANALYZED: "Analyzed",
    CONFIRMED: "Confirmed",
    PUBLISHED: "Published",
    RESULT_PENDING:
      "Result Pending",
    SUCCESS: "Success",
    FAILED: "Failed",
  };

  return (
    <span
      className={`status-badge status-${status
        .toLowerCase()
        .replace("_", "-")}`}
    >
      <i />

      {labels[status]}
    </span>
  );
}

/*
 * ------------------------------------------------------------
 * TELEGRAM STATUS
 * ------------------------------------------------------------
 */

function TelegramStatus({
  status,
}: {
  status:
    | "Published"
    | "Not Published"
    | "Pending";
}) {
  return (
    <span
      className={`telegram-status telegram-${status
        .toLowerCase()
        .replace(" ", "-")}`}
    >
      <span className="telegram-dot">
        ✈
      </span>

      {status}
    </span>
  );
}

/*
 * ------------------------------------------------------------
 * MINI BOARD
 * ------------------------------------------------------------
 */

function MiniBoard({
  positions,
}: {
  positions: number[];
}) {
  return (
    <div className="mini-board">

      {Array.from(
        { length: 25 }
      ).map((_, index) => {

        const position =
          index + 1;

        const safe =
          positions.includes(
            position
          );

        return (
          <div
            key={position}
            className={`mini-cell ${
              safe ? "safe" : ""
            }`}
          >
            {safe && "★"}
          </div>
        );
      })}

    </div>
  );
}