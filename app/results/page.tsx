"use client";

import {
  useEffect,
  useMemo,
  useState,
} from "react";
import Link from "next/link";
import AdminShell from "@/components/layout/AdminShell";

type ResultStatus =
  | "SUCCESS"
  | "FAILED"
  | "PENDING";

type SignalResult = {
  id: string | null;
  signalId: string;

  signalNumber: string;
  game: string;

  boardSize: number;
  mineCount: number;

  confidence: number | null;

  predictedSafePositions: number[];
  actualSafePositions: number[];
  actualMines: number[];

  correct: number;
  incorrect: number;

  accuracy: number | null;

  attempts: number;

  result: ResultStatus;

  modelVersion: string | null;

  signalCreatedAt: string;
  recordedAt: string | null;
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

export default function SignalResultsPage() {
  const [results, setResults] =
    useState<SignalResult[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  const [search, setSearch] =
    useState("");

  const [resultFilter, setResultFilter] =
    useState("All Results");

  const [mineFilter, setMineFilter] =
    useState("All Mines");

  const [refreshing, setRefreshing] =
    useState(false);

  // ============================================================
  // LOAD RESULTS
  // ============================================================

  const loadResults = async (
    showRefresh = false
  ) => {
    try {
      if (showRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setError(null);

      const response = await fetch(
        `${API_URL}/api/results`,
        {
          method: "GET",
          credentials: "include",
          cache: "no-store",
        }
      );

      if (!response.ok) {
        let message =
          "Unable to load signal results.";

        try {
          const body =
            await response.json();

          if (body?.detail) {
            message = body.detail;
          }
        } catch {}

        throw new Error(message);
      }

      const data =
        await response.json();

      const mapped: SignalResult[] =
        (data.items ?? []).map(
          (item: any) => ({
            id: item.id,
            signalId: item.signal_id,

            signalNumber:
              item.signal_number,

            game: item.game,

            boardSize:
              item.board_size,

            mineCount:
              item.mine_count,

            confidence:
              item.confidence,

            predictedSafePositions:
              item.predicted_safe_positions ??
              [],

            actualSafePositions:
              item.actual_safe_positions ??
              [],

            actualMines:
              item.actual_mine_positions ??
              [],

            correct:
              item.correct_predictions ?? 0,

            incorrect:
              item.incorrect_predictions ??
              0,

            accuracy:
              item.accuracy,

            attempts:
              item.attempts,

            result:
              item.status,

            modelVersion:
              item.model_version,

            signalCreatedAt:
              item.signal_created_at,

            recordedAt:
              item.recorded_at,
          })
        );

      setResults(mapped);
    } catch (err) {
      console.error(
        "Failed to load results:",
        err
      );

      setError(
        err instanceof Error
          ? err.message
          : "Unable to load signal results."
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    let mounted = true;

    const load = async () => {
      if (!mounted) {
        return;
      }

      await loadResults();
    };

    load();

    return () => {
      mounted = false;
    };
  }, []);

  // ============================================================
  // FILTER
  // ============================================================

  const filteredResults = useMemo(() => {
    return results.filter((result) => {
      const query =
        search.trim().toLowerCase();

      const matchesSearch =
        !query ||
        result.signalNumber
          .toLowerCase()
          .includes(query) ||
        result.game
          .toLowerCase()
          .includes(query);

      const matchesResult =
        resultFilter === "All Results" ||
        result.result === resultFilter;

      const matchesMines =
        mineFilter === "All Mines" ||
        result.mineCount.toString() ===
          mineFilter;

      return (
        matchesSearch &&
        matchesResult &&
        matchesMines
      );
    });
  }, [
    results,
    search,
    resultFilter,
    mineFilter,
  ]);

  // ============================================================
  // SUMMARY
  // ============================================================

  const totalResults = results.filter(
    (result) =>
      result.result !== "PENDING"
  ).length;

  const successfulResults =
    results.filter(
      (result) =>
        result.result === "SUCCESS"
    ).length;

  const failedResults =
    results.filter(
      (result) =>
        result.result === "FAILED"
    ).length;

  const pendingResults =
    results.filter(
      (result) =>
        result.result === "PENDING"
    ).length;

  const completedResults =
    results.filter(
      (result) =>
        result.result !== "PENDING"
    );

  const correctTotal =
    completedResults.reduce(
      (total, result) =>
        total + result.correct,
      0
    );

  const incorrectTotal =
    completedResults.reduce(
      (total, result) =>
        total + result.incorrect,
      0
    );

  const evaluatedSignals =
    completedResults.length;

  const observedAccuracy =
    correctTotal + incorrectTotal > 0
      ? (
          correctTotal /
          (correctTotal + incorrectTotal)
        ) * 100
      : null;

  // ============================================================
  // RESET
  // ============================================================

  const resetFilters = () => {
    setSearch("");
    setResultFilter("All Results");
    setMineFilter("All Mines");
  };

  // ============================================================
  // EXPORT
  // ============================================================

  const exportResults = () => {
    if (filteredResults.length === 0) {
      return;
    }

    const header = [
      "Signal",
      "Game",
      "Board Size",
      "Mines",
      "Accuracy",
      "Correct",
      "Incorrect",
      "Status",
      "Attempts",
      "Model Version",
      "Recorded At",
    ];

    const rows =
      filteredResults.map(
        (result) => [
          result.signalNumber,
          result.game,
          `${result.boardSize} × ${result.boardSize}`,
          result.mineCount,
          result.accuracy ?? "",
          result.correct,
          result.incorrect,
          result.result,
          result.attempts,
          result.modelVersion ?? "",
          result.recordedAt ?? "",
        ]
      );

    const csv = [
      header,
      ...rows,
    ]
      .map((row) =>
        row
          .map((value) => {
            const text =
              String(value);

            return `"${text.replace(
              /"/g,
              '""'
            )}"`;
          })
          .join(",")
      )
      .join("\n");

    const blob = new Blob(
      [csv],
      {
        type: "text/csv;charset=utf-8;",
      }
    );

    const url =
      URL.createObjectURL(blob);

    const anchor =
      document.createElement("a");

    anchor.href = url;

    anchor.download =
      "signal-results.csv";

    document.body.appendChild(anchor);

    anchor.click();

    anchor.remove();

    URL.revokeObjectURL(url);
  };

  return (
    <AdminShell>
      <div className="results-page">

        {/* HEADER */}

        <div className="results-page-header">

          <div>

            <div className="breadcrumb">
              Signals <span>/</span>{" "}
              Signal Results
            </div>

            <h1>
              Signal Results
            </h1>

            <p>
              Review signal predictions
              against recorded game
              outcomes.
            </p>

          </div>

          <div
            style={{
              display: "flex",
              gap: 10,
            }}
          >

            <button
              className="back-button"
              type="button"
              onClick={() =>
                loadResults(true)
              }
              disabled={refreshing}
            >
              {refreshing
                ? "Refreshing..."
                : "↻ Refresh"}
            </button>

            <Link
              href="/signals"
              className="back-button"
            >
              ← Signals
            </Link>

          </div>

        </div>

        {/* ERROR */}

        {error && (
          <div
            className="results-empty"
            style={{
              marginBottom: 20,
            }}
          >
            <div>!</div>

            <h3>
              Unable to load results
            </h3>

            <p>
              {error}
            </p>

            <button
              className="results-reset"
              type="button"
              onClick={() =>
                loadResults()
              }
            >
              Try Again
            </button>
          </div>
        )}

        {/* SUMMARY */}

        <div className="result-summary-grid">

          <ResultStat
            label="Total Results"
            value={
              loading
                ? "—"
                : String(totalResults)
            }
            description="Recorded outcomes"
            icon="▦"
          />

          <ResultStat
            label="Successful"
            value={
              loading
                ? "—"
                : String(
                    successfulResults
                  )
            }
            description="Completed successfully"
            icon="✓"
            accent="green"
          />

          <ResultStat
            label="Failed"
            value={
              loading
                ? "—"
                : String(failedResults)
            }
            description="Required review"
            icon="×"
            accent="red"
          />

          <ResultStat
            label="Pending"
            value={
              loading
                ? "—"
                : String(pendingResults)
            }
            description="Awaiting outcomes"
            icon="◷"
            accent="orange"
          />

        </div>

        {/* PERFORMANCE */}

        <div className="performance-strip">

          <div className="performance-main">

            <div className="performance-icon">
              ↗
            </div>

            <div>

              <span>
                Observed prediction accuracy
              </span>

              <strong>
                {observedAccuracy !== null
                  ? `${observedAccuracy.toFixed(
                      1
                    )}%`
                  : "—"}
              </strong>

              <small>
                Based on recorded signal
                outcomes
              </small>

            </div>

          </div>

          <div className="performance-metrics">

            <div>
              <span>Correct</span>
              <strong>
                {correctTotal}
              </strong>
            </div>

            <div>
              <span>Incorrect</span>
              <strong>
                {incorrectTotal}
              </strong>
            </div>

            <div>
              <span>
                Signals evaluated
              </span>
              <strong>
                {evaluatedSignals}
              </strong>
            </div>

          </div>

        </div>

        {/* RESULTS CARD */}

        <div className="results-card">

          <div className="results-card-header">

            <div>

              <h2>
                Result History
              </h2>

              <p>
                Compare generated
                predictions with actual
                board outcomes.
              </p>

            </div>

            <button
              className="export-button"
              type="button"
              onClick={exportResults}
              disabled={
                filteredResults.length === 0
              }
            >
              ↓ Export
            </button>

          </div>

          {/* FILTERS */}

          <div className="results-filters">

            <div className="results-search">

              <span>⌕</span>

              <input
                type="text"
                placeholder="Search signal number..."
                value={search}
                onChange={(event) =>
                  setSearch(
                    event.target.value
                  )
                }
              />

            </div>

            <select
              value={resultFilter}
              onChange={(event) =>
                setResultFilter(
                  event.target.value
                )
              }
            >
              <option>
                All Results
              </option>

              <option value="SUCCESS">
                SUCCESS
              </option>

              <option value="FAILED">
                FAILED
              </option>

              <option value="PENDING">
                PENDING
              </option>
            </select>

            <select
              value={mineFilter}
              onChange={(event) =>
                setMineFilter(
                  event.target.value
                )
              }
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
              className="results-reset"
              type="button"
              onClick={resetFilters}
            >
              Reset
            </button>

          </div>

          {/* LOADING */}

          {loading ? (
            <div className="results-empty">

              <div>◷</div>

              <h3>
                Loading results
              </h3>

              <p>
                Fetching signal result
                history...
              </p>

            </div>
          ) : (
            <>
              {/* DESKTOP TABLE */}

              <div className="results-table-wrapper">

                <table className="results-table">

                  <thead>

                    <tr>
                      <th>Signal</th>
                      <th>Board</th>
                      <th>Accuracy</th>
                      <th>Correct</th>
                      <th>Result</th>
                      <th>Recorded</th>
                      <th></th>
                    </tr>

                  </thead>

                  <tbody>

                    {filteredResults.map(
                      (result) => (
                        <tr
                          key={
                            result.id ??
                            result.signalId
                          }
                        >

                          <td>

                            <div className="result-signal-id">

                              <div className="result-signal-icon">
                                {result.result ===
                                "PENDING"
                                  ? "◷"
                                  : "✓"}
                              </div>

                              <div>

                                <strong>
                                  {
                                    result.signalNumber
                                  }
                                </strong>

                                <span>
                                  {result.game}
                                </span>

                              </div>

                            </div>

                          </td>

                          <td>

                            <div className="result-board-cell">

                              <ResultBoard
                                predicted={
                                  result.predictedSafePositions
                                }
                                actualSafe={
                                  result.actualSafePositions
                                }
                                actualMines={
                                  result.actualMines
                                }
                              />

                              <div>

                                <strong>
                                  {
                                    result.boardSize
                                  }{" "}
                                  ×{" "}
                                  {
                                    result.boardSize
                                  }
                                </strong>

                                <span>
                                  {
                                    result.mineCount
                                  }{" "}
                                  mines
                                </span>

                              </div>

                            </div>

                          </td>

                          <td>
                            <Accuracy
                              value={
                                result.accuracy
                              }
                            />
                          </td>

                          <td>

                            <div className="correct-count">

                              <strong>
                                {
                                  result.correct
                                }
                              </strong>

                              <span>
                                {" "}
                                /{" "}
                                {
                                  result.correct +
                                  result.incorrect
                                }
                              </span>

                            </div>

                          </td>

                          <td>
                            <ResultBadge
                              result={
                                result.result
                              }
                            />
                          </td>

                          <td>

                            <span className="completed-date">
                              {result.recordedAt
                                ? formatDate(
                                    result.recordedAt
                                  )
                                : "Awaiting outcome"}
                            </span>

                          </td>

                          <td>

                            {result.result ===
                            "PENDING" ? (
                              <Link
                                className="result-action"
                                href={`/signals/${result.signalId}`}
                              >
                                →
                              </Link>
                            ) : (
                              <Link
                                className="result-action"
                                href={`/results/${result.id}`}
                              >
                                →
                              </Link>
                            )}

                          </td>

                        </tr>
                      )
                    )}

                  </tbody>

                </table>

              </div>

              {/* MOBILE */}

              <div className="results-mobile-list">

                {filteredResults.map(
                  (result) => (
                    <div
                      className="result-mobile-card"
                      key={
                        result.id ??
                        result.signalId
                      }
                    >

                      <div className="result-mobile-header">

                        <div className="result-signal-id">

                          <div className="result-signal-icon">
                            {result.result ===
                            "PENDING"
                              ? "◷"
                              : "✓"}
                          </div>

                          <div>

                            <strong>
                              {
                                result.signalNumber
                              }
                            </strong>

                            <span>
                              {result.recordedAt
                                ? formatDate(
                                    result.recordedAt
                                  )
                                : "Awaiting outcome"}
                            </span>

                          </div>

                        </div>

                        <ResultBadge
                          result={
                            result.result
                          }
                        />

                      </div>

                      <div className="result-mobile-board">

                        <ResultBoard
                          predicted={
                            result.predictedSafePositions
                          }
                          actualSafe={
                            result.actualSafePositions
                          }
                          actualMines={
                            result.actualMines
                          }
                        />

                        <div className="result-mobile-details">

                          <div>
                            <span>
                              Accuracy
                            </span>

                            <strong>
                              {result.accuracy !==
                              null
                                ? `${result.accuracy}%`
                                : "Pending"}
                            </strong>
                          </div>

                          <div>
                            <span>
                              Mines
                            </span>

                            <strong>
                              {
                                result.mineCount
                              }
                            </strong>
                          </div>

                          <div>
                            <span>
                              Correct
                            </span>

                            <strong>
                              {
                                result.correct
                              }
                            </strong>
                          </div>

                          <div>
                            <span>
                              Attempts
                            </span>

                            <strong>
                              {
                                result.attempts
                              }
                            </strong>
                          </div>

                        </div>

                      </div>

                      <div className="result-mobile-footer">

                        {result.result ===
                        "PENDING" ? (
                          <Link
                            href={`/signals/${result.signalId}`}
                          >
                            Record Result
                          </Link>
                        ) : (
                          <Link
                            href={`/results/${result.id}`}
                          >
                            View Result
                          </Link>
                        )}

                      </div>

                    </div>
                  )
                )}

              </div>

              {/* EMPTY */}

              {filteredResults.length ===
                0 && (
                <div className="results-empty">

                  <div>⌕</div>

                  <h3>
                    No results found
                  </h3>

                  <p>
                    Try changing your
                    search or filters.
                  </p>

                </div>
              )}

              {/* PAGINATION */}

              <div className="results-pagination">

                <span>
                  Showing{" "}
                  {
                    filteredResults.length
                  }{" "}
                  of{" "}
                  {results.length}{" "}
                  results
                </span>

                <div>

                  <button disabled>
                    ‹
                  </button>

                  <button className="active">
                    1
                  </button>

                  <button disabled>
                    2
                  </button>

                  <button disabled>
                    3
                  </button>

                  <button disabled>
                    ›
                  </button>

                </div>

              </div>
            </>
          )}

        </div>

      </div>
    </AdminShell>
  );
}


/* ============================================================
   HELPERS
============================================================ */

function formatDate(
  value: string
) {
  const date = new Date(value);

  if (
    Number.isNaN(
      date.getTime()
    )
  ) {
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


/* ============================================================
   RESULT STAT
============================================================ */

function ResultStat({
  label,
  value,
  description,
  icon,
  accent,
}: {
  label: string;
  value: string;
  description: string;
  icon: string;
  accent?: "green" | "red" | "orange";
}) {
  return (
    <div className="result-stat">

      <div
        className={`result-stat-icon ${
          accent || ""
        }`}
      >
        {icon}
      </div>

      <div>

        <span>{label}</span>

        <strong>{value}</strong>

        <small>
          {description}
        </small>

      </div>

    </div>
  );
}


/* ============================================================
   ACCURACY
============================================================ */

function Accuracy({
  value,
}: {
  value: number | null;
}) {
  if (value === null) {
    return (
      <span className="accuracy-pending">
        Pending
      </span>
    );
  }

  return (
    <div className="accuracy">

      <div>
        <strong>
          {Math.round(value)}%
        </strong>
      </div>

      <div className="accuracy-bar">
        <span
          style={{
            width: `${Math.max(
              0,
              Math.min(100, value)
            )}%`,
          }}
        />
      </div>

    </div>
  );
}


/* ============================================================
   RESULT BADGE
============================================================ */

function ResultBadge({
  result,
}: {
  result: ResultStatus;
}) {
  const labels = {
    SUCCESS: "Success",
    FAILED: "Failed",
    PENDING: "Pending",
  };

  return (
    <span
      className={`result-badge result-${result.toLowerCase()}`}
    >
      <i />
      {labels[result]}
    </span>
  );
}


/* ============================================================
   RESULT BOARD
============================================================ */

function ResultBoard({
  predicted,
  actualSafe,
  actualMines,
}: {
  predicted: number[];
  actualSafe: number[];
  actualMines: number[];
}) {
  return (
    <div className="result-board">

      {Array.from(
        { length: 25 }
      ).map((_, index) => {
        const position =
          index + 1;

        const wasPredicted =
          predicted.includes(
            position
          );

        const isSafe =
          actualSafe.includes(
            position
          );

        const isMine =
          actualMines.includes(
            position
          );

        let className =
          "result-cell";

        if (isMine) {
          className += " mine";
        } else if (
          wasPredicted &&
          isSafe
        ) {
          className += " correct";
        } else if (
          wasPredicted
        ) {
          className += " incorrect";
        }

        return (
          <div
            key={position}
            className={className}
          >
            {isMine
              ? "×"
              : wasPredicted &&
                isSafe
                ? "✓"
                : wasPredicted
                  ? "!"
                  : ""}
          </div>
        );
      })}

    </div>
  );
}