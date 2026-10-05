"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  useParams,
  useRouter,
} from "next/navigation";

import AdminShell from "@/components/layout/AdminShell";


type ResultStatus =
  | "SUCCESS"
  | "FAILED";


type Result = {
  id: string;
  signalId: string;

  signalNumber: string;
  game: string;

  boardSize: string;
  mineCount: number;

  modelVersion: string | null;
  confidence: number | null;

  predictedSafePositions: number[];
  actualSafePositions: number[];
  actualMinePositions: number[];

  correctPredictions: number;
  incorrectPredictions: number;

  accuracy: number | null;

  status: ResultStatus;

  attempts: number;

  signalCreatedAt: string;
  recordedAt: string | null;
};


const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";


export default function ResultDetailsPage() {
  const router = useRouter();

  const params = useParams();

  const resultId = Array.isArray(
    params?.id
  )
    ? params.id[0]
    : params?.id;

  const [result, setResult] =
    useState<Result | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);


  // ============================================================
  // LOAD RESULT
  // ============================================================

  useEffect(() => {
    if (!resultId) {
      return;
    }

    let mounted = true;

    const loadResult = async () => {
      try {
        setLoading(true);
        setError(null);

        const response =
          await fetch(
            `${API_URL}/api/results/${resultId}`,
            {
              method: "GET",
              credentials: "include",
              cache: "no-store",
            }
          );

        if (!response.ok) {
          let message =
            "Result not found.";

          try {
            const body =
              await response.json();

            if (body?.detail) {
              message =
                body.detail;
            }
          } catch {}

          throw new Error(message);
        }

        const data =
          await response.json();

        if (!mounted) {
          return;
        }

        setResult({
          id: data.id,
          signalId:
            data.signal_id,

          signalNumber:
            data.signal_number,

          game:
            data.game,

          boardSize:
            `${data.board_size} × ${data.board_size}`,

          mineCount:
            data.mine_count,

          modelVersion:
            data.model_version,

          confidence:
            data.confidence,

          predictedSafePositions:
            data.predicted_safe_positions ??
            [],

          actualSafePositions:
            data.actual_safe_positions ??
            [],

          actualMinePositions:
            data.actual_mine_positions ??
            [],

          correctPredictions:
            data.correct_predictions ??
            0,

          incorrectPredictions:
            data.incorrect_predictions ??
            0,

          accuracy:
            data.accuracy,

          status:
            data.status,

          attempts:
            data.attempts,

          signalCreatedAt:
            data.signal_created_at,

          recordedAt:
            data.recorded_at,
        });
      } catch (err) {
        console.error(
          "Failed to load result:",
          err
        );

        if (!mounted) {
          return;
        }

        setError(
          err instanceof Error
            ? err.message
            : "Unable to load result."
        );
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    loadResult();

    return () => {
      mounted = false;
    };
  }, [resultId]);


  // ============================================================
  // LOADING
  // ============================================================

  if (loading) {
    return (
      <AdminShell>

        <div className="result-details-page">

          <div className="result-details-not-found">

            <div className="result-not-found-icon">
              ◷
            </div>

            <h2>
              Loading result
            </h2>

            <p>
              Fetching the recorded
              signal outcome...
            </p>

          </div>

        </div>

      </AdminShell>
    );
  }


  // ============================================================
  // ERROR / NOT FOUND
  // ============================================================

  if (
    error ||
    !result
  ) {
    return (
      <AdminShell>

        <div className="result-details-page">

          <div className="result-details-not-found">

            <div className="result-not-found-icon">

              <svg
                width="28"
                height="28"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <circle
                  cx="12"
                  cy="12"
                  r="9"
                />

                <path d="M9 9l6 6M15 9l-6 6" />
              </svg>

            </div>

            <h2>
              Result not found
            </h2>

            <p>
              {error ||
                "The result you are looking for does not exist or is no longer available."}
            </p>

            <button
              className="result-secondary-btn"
              onClick={() =>
                router.push(
                  "/results"
                )
              }
            >
              ← Back to Results
            </button>

          </div>

        </div>

      </AdminShell>
    );
  }


  const totalPredictions =
    result.correctPredictions +
    result.incorrectPredictions;

  const correctRate =
    totalPredictions > 0
      ? Math.round(
          (result.correctPredictions /
            totalPredictions) *
            100
        )
      : 0;


  return (
    <AdminShell>

      <div className="result-details-page">

        {/* =====================================================
            HEADER
        ====================================================== */}

        <div className="result-details-header">

          <div className="result-details-header-left">

            <button
              className="result-back-btn"
              onClick={() =>
                router.push(
                  "/results"
                )
              }
            >

              <svg
                width="17"
                height="17"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M19 12H5" />
                <path d="M12 19l-7-7 7-7" />
              </svg>

              Back to Results

            </button>


            <div className="result-breadcrumb">

              <span>
                Results
              </span>

              <span>/</span>

              <strong>
                {result.id}
              </strong>

            </div>


            <div className="result-title-row">

              <div>

                <h1>
                  {result.id}
                </h1>

                <p>
                  Observed result and
                  prediction performance
                </p>

              </div>

              <ResultStatusBadge
                status={result.status}
              />

            </div>

          </div>


          <div className="result-header-actions">

            <button
              className="result-secondary-btn"
              onClick={() =>
                router.push(
                  `/signals/${result.signalId}`
                )
              }
            >

              <svg
                width="17"
                height="17"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M15 18l-6-6 6-6" />
              </svg>

              View Signal

            </button>

          </div>

        </div>


        {/* =====================================================
            SUMMARY
        ====================================================== */}

        <div className="result-overview-grid">

          <ResultStat
            label="Observed Accuracy"
            value={
              result.accuracy !== null
                ? `${result.accuracy}%`
                : "—"
            }
            icon="accuracy"
            accent="green"
          />

          <ResultStat
            label="Correct Predictions"
            value={String(
              result.correctPredictions
            )}
            icon="correct"
            accent="blue"
          />

          <ResultStat
            label="Incorrect Predictions"
            value={String(
              result.incorrectPredictions
            )}
            icon="incorrect"
            accent="red"
          />

          <ResultStat
            label="Model Confidence"
            value={
              result.confidence !== null
                ? `${result.confidence}%`
                : "—"
            }
            icon="confidence"
            accent="purple"
          />

        </div>


        {/* =====================================================
            COMPARISON
        ====================================================== */}

        <section className="result-card result-comparison-card">

          <div className="result-card-header">

            <div>

              <h2>
                Prediction vs Actual Result
              </h2>

              <p>
                Comparison between the
                model's recommended
                positions and the recorded
                board outcome.
              </p>

            </div>

            <span className="result-board-label">
              {result.boardSize}
            </span>

          </div>


          <div className="result-comparison-grid">

            {/* PREDICTION */}

            <div className="result-board-column">

              <div className="result-board-heading">

                <div>

                  <strong>
                    Model Prediction
                  </strong>

                  <span>
                    Recommended safe
                    positions
                  </span>

                </div>

                <span className="result-board-count">
                  {
                    result
                      .predictedSafePositions
                      .length
                  }
                </span>

              </div>


              <div className="result-board">

                {Array.from(
                  { length: 25 },
                  (_, index) => {
                    const position =
                      index + 1;

                    const isPredicted =
                      result
                        .predictedSafePositions
                        .includes(
                          position
                        );

                    return (
                      <div
                        key={position}
                        className={`result-board-cell ${
                          isPredicted
                            ? "predicted"
                            : ""
                        }`}
                      >

                        {isPredicted ? (
                          <svg
                            width="19"
                            height="19"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2.5"
                          >
                            <path d="M20 6L9 17l-5-5" />
                          </svg>
                        ) : (
                          <span>
                            {position}
                          </span>
                        )}

                      </div>
                    );
                  }
                )}

              </div>

            </div>


            {/* ACTUAL */}

            <div className="result-board-column">

              <div className="result-board-heading">

                <div>

                  <strong>
                    Actual Result
                  </strong>

                  <span>
                    Recorded board outcome
                  </span>

                </div>

                <span className="result-board-count danger">
                  {result.mineCount}
                </span>

              </div>


              <div className="result-board">

                {Array.from(
                  { length: 25 },
                  (_, index) => {
                    const position =
                      index + 1;

                    const isMine =
                      result
                        .actualMinePositions
                        .includes(
                          position
                        );

                    const wasPredicted =
                      result
                        .predictedSafePositions
                        .includes(
                          position
                        );

                    const isCorrect =
                      wasPredicted &&
                      result
                        .actualSafePositions
                        .includes(
                          position
                        );

                    const isIncorrect =
                      wasPredicted &&
                      isMine;

                    return (
                      <div
                        key={position}
                        className={[
                          "result-board-cell",
                          isMine
                            ? "actual-mine"
                            : "",
                          isCorrect
                            ? "correct"
                            : "",
                          isIncorrect
                            ? "incorrect"
                            : "",
                        ].join(" ")}
                      >

                        {isMine ? (
                          <svg
                            width="18"
                            height="18"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                          >
                            <circle
                              cx="12"
                              cy="12"
                              r="5"
                            />

                            <path d="M12 2v3M12 19v3M2 12h3M19 12h3" />
                          </svg>
                        ) : isCorrect ? (
                          <svg
                            width="18"
                            height="18"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2.5"
                          >
                            <path d="M20 6L9 17l-5-5" />
                          </svg>
                        ) : (
                          <span>
                            {position}
                          </span>
                        )}

                      </div>
                    );
                  }
                )}

              </div>

            </div>

          </div>


          {/* LEGEND */}

          <div className="result-board-legend">

            <ResultLegend
              type="correct"
              label="Correct prediction"
            />

            <ResultLegend
              type="mine"
              label="Actual mine"
            />

            <ResultLegend
              type="incorrect"
              label="Incorrect prediction"
            />

            <ResultLegend
              type="empty"
              label="Not selected"
            />

          </div>

        </section>


        {/* =====================================================
            PERFORMANCE + INFORMATION
        ====================================================== */}

        <div className="result-details-main-grid">

          {/* PERFORMANCE */}

          <section className="result-card">

            <div className="result-card-header">

              <div>

                <h2>
                  Prediction Performance
                </h2>

                <p>
                  Performance calculated
                  from the recorded result.
                </p>

              </div>

            </div>


            <div className="result-performance-main">

              <div className="result-performance-score">

                <strong>
                  {result.accuracy !==
                  null
                    ? `${result.accuracy}%`
                    : "—"}
                </strong>

                <span>
                  Observed accuracy
                </span>

              </div>


              <div className="result-performance-ring">

                <div
                  className="result-ring"
                  style={{
                    background:
                      `conic-gradient(
                        #229ed9 ${
                          (result.accuracy ??
                            0) *
                          3.6
                        }deg,
                        #edf1f4 0deg
                      )`,
                  }}
                >

                  <div>

                    <strong>
                      {result.accuracy !==
                      null
                        ? `${result.accuracy}%`
                        : "—"}
                    </strong>

                  </div>

                </div>

              </div>

            </div>


            <div className="result-performance-bars">

              <PerformanceBar
                label="Correct"
                value={
                  result.correctPredictions
                }
                total={
                  totalPredictions
                }
                type="correct"
              />

              <PerformanceBar
                label="Incorrect"
                value={
                  result.incorrectPredictions
                }
                total={
                  totalPredictions
                }
                type="incorrect"
              />

            </div>


            <div className="result-performance-note">

              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <circle
                  cx="12"
                  cy="12"
                  r="9"
                />

                <path d="M12 11v5M12 8h.01" />
              </svg>

              <span>
                Observed accuracy reflects
                recorded outcomes for this
                signal. It should not be
                interpreted as a guaranteed
                probability of a future game
                outcome.
              </span>

            </div>

          </section>


          {/* INFORMATION */}

          <section className="result-card">

            <div className="result-card-header">

              <div>

                <h2>
                  Result Information
                </h2>

                <p>
                  Configuration and
                  recording details.
                </p>

              </div>

            </div>


            <div className="result-info-list">

              <ResultInfoRow
                label="Result ID"
                value={result.id}
                mono
              />

              <ResultInfoRow
                label="Signal"
                value={
                  result.signalNumber
                }
                accent
              />

              <ResultInfoRow
                label="Game"
                value={result.game}
              />

              <ResultInfoRow
                label="Board Size"
                value={
                  result.boardSize
                }
              />

              <ResultInfoRow
                label="Mine Count"
                value={`${result.mineCount} mines`}
              />

              <ResultInfoRow
                label="Attempts"
                value={`${result.attempts} attempts`}
              />

              <ResultInfoRow
                label="Model Version"
                value={
                  result.modelVersion ??
                  "No model version"
                }
                accent
              />

              <ResultInfoRow
                label="Recorded"
                value={
                  result.recordedAt
                    ? formatDate(
                        result.recordedAt
                      )
                    : "Pending"
                }
              />

            </div>

          </section>

        </div>


        {/* =====================================================
            RESULT TIMELINE
        ====================================================== */}

        <section className="result-card">

          <div className="result-card-header">

            <div>

              <h2>
                Result Activity
              </h2>

              <p>
                Timeline for the signal
                and observed result.
              </p>

            </div>

          </div>


          <div className="result-timeline">

            <ResultTimelineItem
              title="Signal Created"
              description="The signal was created by the signal engine."
              date={formatDate(
                result.signalCreatedAt
              )}
              active
            />

            <ResultTimelineItem
              title="Result Recorded"
              description="The actual game outcome was recorded and evaluated."
              date={
                result.recordedAt
                  ? formatDate(
                      result.recordedAt
                    )
                  : "Pending"
              }
              active={
                Boolean(
                  result.recordedAt
                )
              }
              last
            />

          </div>

        </section>

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
  const date =
    new Date(value);

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
   STATUS
============================================================ */

function ResultStatusBadge({
  status,
}: {
  status: ResultStatus;
}) {
  const config = {
    SUCCESS: {
      label: "Success",
      className: "success",
    },

    FAILED: {
      label: "Failed",
      className: "failed",
    },
  }[status];

  return (
    <span
      className={`result-status-badge ${config.className}`}
    >
      <span />
      {config.label}
    </span>
  );
}


/* ============================================================
   STAT
============================================================ */

function ResultStat({
  label,
  value,
  icon,
  accent,
}: {
  label: string;
  value: string;
  icon: string;
  accent: string;
}) {
  return (
    <div className="result-stat-card">

      <div
        className={`result-stat-icon ${accent}`}
      >

        {icon === "accuracy" && (
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <circle
              cx="12"
              cy="12"
              r="9"
            />

            <path d="M8 12l2.5 2.5L16 9" />
          </svg>
        )}

        {icon === "correct" && (
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M20 6L9 17l-5-5" />
          </svg>
        )}

        {icon === "incorrect" && (
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M6 6l12 12M18 6L6 18" />
          </svg>
        )}

        {icon === "confidence" && (
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M12 3l7 4v5c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V7l7-4z" />

            <path d="M9 12l2 2 4-4" />
          </svg>
        )}

      </div>

      <div>

        <span>
          {label}
        </span>

        <strong>
          {value}
        </strong>

      </div>

    </div>
  );
}


/* ============================================================
   LEGEND
============================================================ */

function ResultLegend({
  type,
  label,
}: {
  type:
    | "correct"
    | "mine"
    | "incorrect"
    | "empty";

  label: string;
}) {
  return (
    <div className="result-legend-item">

      <span
        className={`result-legend-icon ${type}`}
      >
        {type === "correct" && "✓"}
        {type === "mine" && "×"}
        {type === "incorrect" && "!"}
      </span>

      <span>
        {label}
      </span>

    </div>
  );
}


/* ============================================================
   PERFORMANCE BAR
============================================================ */

function PerformanceBar({
  label,
  value,
  total,
  type,
}: {
  label: string;
  value: number;
  total: number;
  type:
    | "correct"
    | "incorrect";
}) {
  const percentage =
    total > 0
      ? (value / total) * 100
      : 0;

  return (
    <div className="result-performance-bar-row">

      <div className="result-performance-bar-label">

        <span>
          {label}
        </span>

        <strong>
          {value}
        </strong>

      </div>

      <div className="result-performance-track">

        <div
          className={`result-performance-fill ${type}`}
          style={{
            width: `${percentage}%`,
          }}
        />

      </div>

    </div>
  );
}


/* ============================================================
   INFO ROW
============================================================ */

function ResultInfoRow({
  label,
  value,
  mono,
  accent,
}: {
  label: string;
  value: string;
  mono?: boolean;
  accent?: boolean;
}) {
  return (
    <div className="result-info-row">

      <span>
        {label}
      </span>

      <strong
        className={[
          mono ? "mono" : "",
          accent ? "accent" : "",
        ].join(" ")}
      >
        {value}
      </strong>

    </div>
  );
}


/* ============================================================
   TIMELINE
============================================================ */

function ResultTimelineItem({
  title,
  description,
  date,
  active,
  last,
}: {
  title: string;
  description: string;
  date: string;
  active: boolean;
  last?: boolean;
}) {
  return (
    <div
      className={`result-timeline-item ${
        last ? "last" : ""
      }`}
    >

      <div className="result-timeline-marker">

        {active
          ? "✓"
          : ""}

      </div>

      {!last && (
        <div className="result-timeline-line" />
      )}

      <div className="result-timeline-content">

        <div className="result-timeline-title">

          <strong>
            {title}
          </strong>

          <span>
            {date}
          </span>

        </div>

        <p>
          {description}
        </p>

      </div>

    </div>
  );
}