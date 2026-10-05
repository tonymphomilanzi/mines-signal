"use client";

import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  useParams,
  useRouter,
} from "next/navigation";

import AdminShell from "@/components/layout/AdminShell";

type SignalStatus =
  | "DRAFT"
  | "ANALYZED"
  | "CONFIRMED"
  | "PUBLISHED"
  | "RESULT_PENDING"
  | "SUCCESS"
  | "FAILED";

type Prediction = {
  id: string;
  signal_id: string;
  model_id: string | null;
  safe_positions: number[];
  predicted_mine_positions: number[];
  confidence: number | null;
  attempts: number;
  model_version: string | null;
  created_at: string;
};

type SignalResult = {
  id: string;
  signal_id: string;
  actual_mine_positions: number[];
  actual_safe_positions: number[];
  correct_predictions: number;
  incorrect_predictions: number;
  accuracy: number | null;
  status: string;
  recorded_at: string;
};

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

type SignalDetail = ApiSignal & {
  predictions: Prediction[];
  result: SignalResult | null;
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

export default function SignalDetailsPage() {
  const router = useRouter();
  const params = useParams();

  const signalId = Array.isArray(params?.id)
    ? params.id[0]
    : params?.id;

  const [signal, setSignal] =
    useState<SignalDetail | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [actionLoading, setActionLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [actionMessage, setActionMessage] =
    useState("");

  const [actionError, setActionError] =
    useState("");

  /*
   * ----------------------------------------------------------
   * LOAD SIGNAL DETAILS
   * ----------------------------------------------------------
   */

  const loadSignal = useCallback(
    async () => {
      if (!signalId) {
        setError(
          "Signal ID is missing."
        );

        setLoading(false);

        return;
      }

      setLoading(true);
      setError("");

      try {
        const response =
          await fetch(
            `${API_URL}/api/signals/${signalId}`,
            {
              method: "GET",
              credentials: "include",
              cache: "no-store",
            }
          );

        let data: any = null;

        try {
          data =
            await response.json();
        } catch {
          data = null;
        }

        if (!response.ok) {
          setError(
            data?.detail ||
              "Unable to load signal details."
          );

          return;
        }

        setSignal(
          data as SignalDetail
        );
      } catch (requestError) {
        console.error(
          "Failed to load signal:",
          requestError
        );

        setError(
          "Unable to connect to the signal server."
        );
      } finally {
        setLoading(false);
      }
    },
    [signalId]
  );

  useEffect(() => {
    loadSignal();
  }, [loadSignal]);

  /*
   * ----------------------------------------------------------
   * SIGNAL ACTION
   * ----------------------------------------------------------
   *
   * Lifecycle:
   *
   * DRAFT
   *   ↓
   * ANALYZED
   *   ↓
   * CONFIRMED
   *   ↓
   * PUBLISHED
   *   ↓
   * RESULT_PENDING
   *   ↓
   * SUCCESS / FAILED
   *
   * ----------------------------------------------------------
   */

  const performSignalAction = async (
    action:
      | "confirm"
      | "publish"
  ) => {
    if (!signalId || actionLoading) {
      return;
    }

    setActionLoading(true);
    setActionMessage("");
    setActionError("");

    try {
      const response =
        await fetch(
          `${API_URL}/api/signals/${signalId}/${action}`,
          {
            method: "POST",
            credentials: "include",
            headers: {
              "Content-Type":
                "application/json",
            },
          }
        );

      let data: any = null;

      try {
        data =
          await response.json();
      } catch {
        data = null;
      }

      if (!response.ok) {
        setActionError(
          data?.detail ||
            `Unable to ${action} signal.`
        );

        return;
      }

      setActionMessage(
        data?.message ||
          (
            action === "publish"
              ? "Signal published successfully."
              : "Signal confirmed successfully."
          )
      );

      await loadSignal();
    } catch (requestError) {
      console.error(
        `Failed to ${action} signal:`,
        requestError
      );

      setActionError(
        "Unable to connect to the signal server."
      );
    } finally {
      setActionLoading(false);
    }
  };

  /*
   * ----------------------------------------------------------
   * RECORD RESULT
   * ----------------------------------------------------------
   */

  const openRecordResult = () => {
    if (!signal) {
      return;
    }

    router.push(
      `/results/${signal.id}/record`
    );
  };

  /*
   * ----------------------------------------------------------
   * VIEW RESULT
   * ----------------------------------------------------------
   */

  const openResult = () => {
    if (!signal?.result) {
      return;
    }

    router.push(
      `/results/${signal.result.id}`
    );
  };

  /*
   * ----------------------------------------------------------
   * LOADING
   * ----------------------------------------------------------
   */

  if (loading) {
    return (
      <AdminShell>
        <div className="signal-details-page">
          <div
            style={{
              minHeight: "500px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexDirection: "column",
              gap: "14px",
            }}
          >
            <div
              style={{
                width: "34px",
                height: "34px",
                border:
                  "3px solid #E5EAF0",
                borderTopColor:
                  "#229ED9",
                borderRadius: "50%",
                animation:
                  "signal-details-spin 0.8s linear infinite",
              }}
            />

            <p
              style={{
                color: "#6B7785",
                margin: 0,
              }}
            >
              Loading signal details...
            </p>
          </div>
        </div>

        <style jsx global>{`
          @keyframes signal-details-spin {
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
   * ----------------------------------------------------------
   * ERROR / NOT FOUND
   * ----------------------------------------------------------
   */

  if (error || !signal) {
    return (
      <AdminShell>
        <div className="signal-details-page">
          <div className="signal-details-not-found">
            <div className="signal-not-found-icon">
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
              {error
                ? "Unable to load signal"
                : "Signal not found"}
            </h2>

            <p>
              {error ||
                "The signal you are looking for does not exist or is no longer available."}
            </p>

            <div
              style={{
                display: "flex",
                gap: "10px",
                justifyContent: "center",
                flexWrap: "wrap",
              }}
            >
              {error && (
                <button
                  type="button"
                  className="signal-secondary-btn"
                  onClick={loadSignal}
                >
                  Try Again
                </button>
              )}

              <button
                type="button"
                className="signal-secondary-btn"
                onClick={() =>
                  router.push(
                    "/signals"
                  )
                }
              >
                ← Back to Signals
              </button>
            </div>
          </div>
        </div>
      </AdminShell>
    );
  }

  /*
   * ----------------------------------------------------------
   * DERIVED DATA
   * ----------------------------------------------------------
   */

  const latestPrediction =
    signal.predictions &&
    signal.predictions.length > 0
      ? signal.predictions[
          signal.predictions.length - 1
        ]
      : null;

  const safePositions =
    latestPrediction?.safe_positions
      ?.length
      ? latestPrediction.safe_positions
      : signal.recommended_positions ||
        [];

  const predictedMinePositions =
    latestPrediction
      ?.predicted_mine_positions ||
    [];

  const confidence =
    signal.confidence ??
    latestPrediction?.confidence ??
    null;

  const modelVersion =
    signal.model_version ??
    latestPrediction?.model_version ??
    null;

  const analysisDate =
    latestPrediction?.created_at ||
    null;

  const telegramStatus =
    getTelegramStatus(
      signal.status
    );

  const telegramPublishedAt =
    signal.published_at;

  const result =
    signal.result;

  /*
   * ----------------------------------------------------------
   * ACTION AVAILABILITY
   * ----------------------------------------------------------
   */

  const canAnalyze =
    signal.status === "DRAFT";

  const canConfirm =
    signal.status === "ANALYZED";

  /*
   * CONFIRMED signals can now be published.
   *
   * Publishing moves the signal through the
   * backend lifecycle and marks it RESULT_PENDING.
   */

  const canPublish =
    signal.status === "CONFIRMED";

  /*
   * Record Result is ONLY available after
   * the backend has moved the signal into
   * RESULT_PENDING.
   */

  const canRecordResult =
    signal.status ===
      "RESULT_PENDING" &&
    !result;

  const canViewResult =
    Boolean(result);

  /*
   * ----------------------------------------------------------
   * PAGE
   * ----------------------------------------------------------
   */

  return (
    <AdminShell>
      <div className="signal-details-page">

        {/* HEADER */}

        <div className="signal-details-header">

          <div className="signal-details-header-left">

            <button
              type="button"
              className="signal-back-btn"
              onClick={() =>
                router.push(
                  "/signals"
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

              Back to Signals
            </button>

            <div className="signal-breadcrumb">

              <span>
                Signals
              </span>

              <span>/</span>

              <strong>
                {
                  signal.signal_number
                }
              </strong>

            </div>

            <div className="signal-title-row">

              <div>

                <h1>
                  {
                    signal.signal_number
                  }
                </h1>

                <p>
                  Signal analysis and
                  prediction details
                </p>

              </div>

              <SignalStatusBadge
                status={
                  signal.status
                }
              />

            </div>

          </div>

          <div className="signal-header-actions">

            <button
              type="button"
              className="signal-secondary-btn"
              onClick={() =>
                router.push(
                  "/signals/create"
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
                <path d="M12 5v14M5 12h14" />
              </svg>

              New Signal
            </button>

          </div>

        </div>

        {/* ACTION MESSAGES */}

        {(actionMessage ||
          actionError) && (
          <div
            style={{
              marginBottom: "20px",
              padding: "13px 16px",
              borderRadius: "12px",
              border:
                actionError
                  ? "1px solid rgba(239,68,68,.20)"
                  : "1px solid rgba(34,158,217,.20)",
              background:
                actionError
                  ? "rgba(239,68,68,.06)"
                  : "rgba(34,158,217,.06)",
              color:
                actionError
                  ? "#DC2626"
                  : "#168AC0",
              fontSize: "13px",
              fontWeight: 600,
            }}
          >
            {actionError ||
              actionMessage}
          </div>
        )}

        {/* ACTION BAR */}

        {(canAnalyze ||
          canConfirm ||
          canPublish ||
          canRecordResult ||
          canViewResult) && (
          <section
            className="signal-card"
            style={{
              marginBottom: "20px",
            }}
          >
            <div
              className="signal-card-header"
              style={{
                alignItems:
                  "center",
              }}
            >
              <div>
                <h2>
                  Signal Actions
                </h2>

                <p>
                  Continue the signal
                  through its lifecycle.
                </p>
              </div>

              <div
                style={{
                  display: "flex",
                  gap: "10px",
                  flexWrap: "wrap",
                }}
              >

                {/* DRAFT */}

                {canAnalyze && (
                  <button
                    type="button"
                    className="signal-secondary-btn"
                    onClick={() =>
                      router.push(
                        `/signals/create?signalId=${signal.id}`
                      )
                    }
                    disabled={
                      actionLoading
                    }
                  >
                    Analyze Signal
                  </button>
                )}

                {/* ANALYZED */}

                {canConfirm && (
                  <button
                    type="button"
                    className="signal-secondary-btn"
                    onClick={() =>
                      performSignalAction(
                        "confirm"
                      )
                    }
                    disabled={
                      actionLoading
                    }
                  >
                    {actionLoading
                      ? "Processing..."
                      : "Confirm Signal"}
                  </button>
                )}

                {/* CONFIRMED */}

                {canPublish && (
                  <button
                    type="button"
                    className="signal-secondary-btn"
                    onClick={() =>
                      performSignalAction(
                        "publish"
                      )
                    }
                    disabled={
                      actionLoading
                    }
                  >
                    {actionLoading
                      ? "Processing..."
                      : "Publish Signal"}
                  </button>
                )}

                {/* RESULT PENDING */}

                {canRecordResult && (
                  <button
                    type="button"
                    className="signal-secondary-btn"
                    onClick={
                      openRecordResult
                    }
                  >
                    Record Result
                  </button>
                )}

                {/* RESULT EXISTS */}

                {canViewResult && (
                  <button
                    type="button"
                    className="signal-secondary-btn"
                    onClick={
                      openResult
                    }
                  >
                    View Result
                  </button>
                )}

              </div>
            </div>
          </section>
        )}

        {/* OVERVIEW */}

        <div className="signal-overview-grid">

          <SignalStat
            label="Model Confidence"
            value={
              confidence === null
                ? "—"
                : `${confidence}%`
            }
            icon="confidence"
            accent="blue"
          />

          <SignalStat
            label="Mine Count"
            value={String(
              signal.mine_count
            )}
            icon="mine"
            accent="orange"
          />

          <SignalStat
            label="Attempts"
            value={String(
              signal.attempts
            )}
            icon="attempt"
            accent="purple"
          />

          <SignalStat
            label="Board"
            value={`${signal.board_size} × ${signal.board_size}`}
            icon="board"
            accent="green"
          />

        </div>

        {/* MAIN GRID */}

        <div className="signal-details-main-grid">

          {/* BOARD */}

          <section className="signal-card signal-board-card">

            <div className="signal-card-header">

              <div>

                <h2>
                  Prediction Board
                </h2>

                <p>
                  Recommended positions
                  generated by the signal
                  engine.
                </p>

              </div>

              <span className="signal-board-label">
                {signal.board_size} ×{" "}
                {signal.board_size}
              </span>

            </div>

            <div className="signal-board-wrapper">

              <div
                className="signal-board"
                style={{
                  gridTemplateColumns: `repeat(${signal.board_size}, minmax(0, 1fr))`,
                }}
              >

                {Array.from(
                  {
                    length:
                      signal.board_size *
                      signal.board_size,
                  },
                  (_, index) => {

                    const position =
                      index + 1;

                    const isSafe =
                      safePositions.includes(
                        position
                      );

                    const isMine =
                      predictedMinePositions.includes(
                        position
                      );

                    return (
                      <div
                        key={
                          position
                        }
                        className={[
                          "signal-board-cell",
                          isSafe
                            ? "safe"
                            : "",
                          isMine
                            ? "predicted-mine"
                            : "",
                        ]
                          .filter(
                            Boolean
                          )
                          .join(" ")}
                      >

                        {isSafe ? (
                          <svg
                            width="21"
                            height="21"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2.5"
                          >
                            <path d="M20 6L9 17l-5-5" />
                          </svg>
                        ) : isMine ? (
                          <svg
                            width="21"
                            height="21"
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
                        ) : (
                          <span>
                            {
                              position
                            }
                          </span>
                        )}

                      </div>
                    );
                  }
                )}

              </div>

            </div>

            <div className="signal-board-legend">

              <Legend
                type="safe"
                label="Recommended safe position"
              />

              <Legend
                type="mine"
                label="Predicted mine"
              />

              <Legend
                type="empty"
                label="Not selected"
              />

            </div>

          </section>

          {/* SIGNAL INFORMATION */}

          <section className="signal-card">

            <div className="signal-card-header">

              <div>

                <h2>
                  Signal Information
                </h2>

                <p>
                  Configuration used
                  for this analysis.
                </p>

              </div>

            </div>

            <div className="signal-info-list">

              <InfoRow
                label="Signal Number"
                value={
                  signal.signal_number
                }
                mono
              />

              <InfoRow
                label="Game"
                value={
                  signal.game
                }
              />

              <InfoRow
                label="Board Size"
                value={`${signal.board_size} × ${signal.board_size}`}
              />

              <InfoRow
                label="Mine Count"
                value={`${signal.mine_count} mines`}
              />

              <InfoRow
                label="Attempts"
                value={`${signal.attempts} attempts`}
              />

              <InfoRow
                label="Model Version"
                value={
                  modelVersion ??
                  "Not assigned"
                }
                accent
              />

              <InfoRow
                label="Created"
                value={formatDate(
                  signal.generated_at
                )}
              />

            </div>

          </section>

        </div>

        {/* SECOND ROW */}

        <div className="signal-details-main-grid">

          {/* MODEL */}

          <section className="signal-card">

            <div className="signal-card-header">

              <div>

                <h2>
                  Model Information
                </h2>

                <p>
                  Model used to generate
                  this signal.
                </p>

              </div>

              <span className="signal-version-badge">
                {modelVersion ??
                  "Not assigned"}
              </span>

            </div>

            <div className="signal-model-box">

              <div className="signal-model-icon">

                <svg
                  width="23"
                  height="23"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.8"
                >
                  <rect
                    x="4"
                    y="4"
                    width="16"
                    height="16"
                    rx="3"
                  />

                  <path d="M9 9h6v6H9z" />

                  <path d="M9 2v2M15 2v2M9 20v2M15 20v2M2 9h2M2 15h2M20 9h2M20 15h2" />
                </svg>

              </div>

              <div className="signal-model-content">

                <strong>
                  Mines Signal Engine
                </strong>

                <span>
                  {modelVersion
                    ? "Prediction model assigned to this signal"
                    : "No production model assigned"}
                </span>

              </div>

              <div className="signal-model-status">

                <span
                  className="signal-status-dot"
                  style={{
                    background:
                      modelVersion
                        ? "#22C55E"
                        : "#98A2B3",
                  }}
                />

                {modelVersion
                  ? "Assigned"
                  : "Not Assigned"}

              </div>

            </div>

            <div className="signal-confidence-box">

              <div className="signal-confidence-header">

                <span>
                  Model Confidence
                </span>

                <strong>
                  {confidence ===
                  null
                    ? "—"
                    : `${confidence}%`}
                </strong>

              </div>

              <div className="signal-progress">

                <div
                  style={{
                    width: `${
                      confidence ===
                      null
                        ? 0
                        : Math.max(
                            0,
                            Math.min(
                              100,
                              confidence
                            )
                          )
                    }%`,
                  }}
                />

              </div>

              <p>
                Confidence is the
                model's internal
                assessment for this
                prediction and should
                be evaluated against
                observed results.
              </p>

            </div>

          </section>

          {/* TELEGRAM */}

          <section className="signal-card">

            <div className="signal-card-header">

              <div>

                <h2>
                  Telegram Publishing
                </h2>

                <p>
                  Distribution status
                  for this signal.
                </p>

              </div>

              <TelegramStatus
                status={
                  telegramStatus
                }
              />

            </div>

            <div className="telegram-detail-box">

              <div className="telegram-detail-icon">

                <svg
                  width="23"
                  height="23"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path d="M21.5 3.5L18.2 20c-.25 1.17-.9 1.46-1.83.91l-5.06-3.73-2.44 2.35c-.27.27-.5.5-1.03.5l.37-5.18 9.43-8.52c.41-.37-.09-.58-.64-.21L5.34 13.4.36 11.84c-1.08-.34-1.1-1.08.23-1.6L20.04 2.9c.89-.33 1.67.21 1.46.6Z" />
                </svg>

              </div>

              <div>

                <strong>
                  Telegram Channel
                </strong>

                <span>
                  Telegram message
                  information is
                  managed by the
                  Telegram module.
                </span>

              </div>

            </div>

            <div className="signal-info-list compact">

              <InfoRow
                label="Status"
                value={
                  telegramStatus ===
                  "Published"
                    ? "Published"
                    : telegramStatus ===
                      "Pending"
                    ? "Pending"
                    : "Not Published"
                }
                status={
                  telegramStatus ===
                  "Published"
                    ? "success"
                    : telegramStatus ===
                      "Pending"
                    ? "warning"
                    : "muted"
                }
              />

              <InfoRow
                label="Message ID"
                value="—"
                mono
              />

              <InfoRow
                label="Published"
                value={
                  telegramPublishedAt
                    ? formatDate(
                        telegramPublishedAt
                      )
                    : "—"
                }
              />

            </div>

            <button
              type="button"
              className="signal-outline-full-btn"
              onClick={() =>
                router.push(
                  "/telegram"
                )
              }
            >

              View Telegram Messages

              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M5 12h14" />
                <path d="M13 6l6 6-6 6" />
              </svg>

            </button>

          </section>

        </div>

        {/* RESULT */}

        <section className="signal-card signal-result-section">

          <div className="signal-card-header">

            <div>

              <h2>
                Signal Result
              </h2>

              <p>
                Observed outcome
                associated with this
                signal.
              </p>

            </div>

            {result ? (
              <span
                className={`signal-result-badge ${
                  result.status ===
                  "SUCCESS"
                    ? "success"
                    : "failed"
                }`}
              >
                {result.status}
              </span>
            ) : (
              <span className="signal-result-badge pending">
                RESULT PENDING
              </span>
            )}

          </div>

          {result ? (
            <div className="signal-result-summary">

              <div>

                <strong>
                  Result recorded
                </strong>

                <span>
                  {
                    result.correct_predictions
                  }{" "}
                  correct predictions
                  and{" "}
                  {
                    result.incorrect_predictions
                  }{" "}
                  incorrect predictions.
                  {result.accuracy !==
                    null &&
                    ` Accuracy: ${result.accuracy.toFixed(
                      1
                    )}%.`}
                </span>

              </div>

              <button
                type="button"
                className="signal-secondary-btn"
                onClick={
                  openResult
                }
              >
                View Result Details →
              </button>

            </div>
          ) : (
            <div className="signal-pending-result">

              <div className="signal-pending-icon">

                <svg
                  width="21"
                  height="21"
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

                  <path d="M12 7v5l3 2" />
                </svg>

              </div>

              <div>

                <strong>
                  Waiting for result
                </strong>

                <span>
                  The actual board
                  outcome has not been
                  recorded yet.
                </span>

              </div>

              {signal.status ===
                "RESULT_PENDING" && (
                <button
                  type="button"
                  className="signal-secondary-btn"
                  onClick={
                    openRecordResult
                  }
                >
                  Record Result
                </button>
              )}

            </div>
          )}

        </section>

        {/* TIMELINE */}

        <section className="signal-card">

          <div className="signal-card-header">

            <div>

              <h2>
                Signal Activity
              </h2>

              <p>
                Lifecycle history for
                this signal.
              </p>

            </div>

          </div>

          <div className="signal-timeline">

            <TimelineItem
              title="Signal Created"
              description="Signal configuration was created."
              date={formatDate(
                signal.generated_at
              )}
              active
            />

            <TimelineItem
              title="Analysis Completed"
              description={
                signal.status ===
                "DRAFT"
                  ? "Analysis has not been completed yet."
                  : "The signal engine completed its analysis."
              }
              date={
                signal.status ===
                "DRAFT"
                  ? "Pending"
                  : analysisDate
                  ? formatDate(
                      analysisDate
                    )
                  : "Completed"
              }
              active={
                signal.status !==
                "DRAFT"
              }
            />

            <TimelineItem
              title="Signal Confirmed"
              description={
                signal.confirmed_at
                  ? "Signal was confirmed."
                  : "Signal has not been confirmed yet."
              }
              date={
                signal.confirmed_at
                  ? formatDate(
                      signal.confirmed_at
                    )
                  : "Pending"
              }
              active={
                Boolean(
                  signal.confirmed_at
                )
              }
            />

            <TimelineItem
              title="Result Recorded"
              description={
                result
                  ? `Actual game result recorded as ${result.status}.`
                  : "The actual game outcome has not been recorded yet."
              }
              date={
                result
                  ? formatDate(
                      result.recorded_at
                    )
                  : "Pending"
              }
              active={
                Boolean(result)
              }
              last
            />

          </div>

        </section>

      </div>
    </AdminShell>
  );
}

/*
 * ------------------------------------------------------------
 * TELEGRAM STATUS
 * ------------------------------------------------------------
 */

function getTelegramStatus(
  status: SignalStatus
):
  | "Published"
  | "Pending"
  | "Not Published" {

  /*
   * Telegram is currently not part
   * of the active signal lifecycle.
   *
   * We keep this UI section because
   * the existing design is being
   * preserved.
   */

  if (status === "PUBLISHED") {
    return "Published";
  }

  if (
    status === "ANALYZED" ||
    status === "CONFIRMED"
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

/*
 * ------------------------------------------------------------
 * STATUS BADGE
 * ------------------------------------------------------------
 */

function SignalStatusBadge({
  status,
}: {
  status: SignalStatus;
}) {
  const styles: Record<
    SignalStatus,
    {
      label: string;
      className: string;
    }
  > = {
    DRAFT: {
      label: "Draft",
      className: "draft",
    },

    ANALYZED: {
      label: "Analyzed",
      className: "analyzed",
    },

    CONFIRMED: {
      label: "Entry Confirmed",
      className: "confirmed",
    },

    PUBLISHED: {
      label: "Published",
      className: "published",
    },

    RESULT_PENDING: {
      label: "Result Pending",
      className: "pending",
    },

    SUCCESS: {
      label: "Success",
      className: "success",
    },

    FAILED: {
      label: "Failed",
      className: "failed",
    },
  };

  const item =
    styles[status];

  return (
    <span
      className={`signal-status-badge ${item.className}`}
    >
      <span />

      {item.label}
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
    | "Pending"
    | "Not Published";
}) {
  const config = {
    Published: {
      label: "Published",
      className:
        "published",
    },

    Pending: {
      label: "Pending",
      className: "pending",
    },

    "Not Published": {
      label: "Not Published",
      className: "muted",
    },
  }[status];

  return (
    <span
      className={`telegram-status ${config.className}`}
    >
      <span />

      {config.label}
    </span>
  );
}

/*
 * ------------------------------------------------------------
 * STAT
 * ------------------------------------------------------------
 */

function SignalStat({
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
    <div className="signal-stat-card">

      <div
        className={`signal-stat-icon ${accent}`}
      >

        {icon ===
          "confidence" && (
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

        {icon === "mine" && (
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
              r="4"
            />

            <path d="M12 2v4M12 18v4M2 12h4M18 12h4M4.9 4.9l2.8 2.8M16.3 16.3l2.8 2.8M19.1 4.9l-2.8 2.8M7.7 16.3l-2.8 2.8" />
          </svg>
        )}

        {icon ===
          "attempt" && (
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M3 12a9 9 0 1 0 3-6.7" />

            <path d="M3 4v6h6" />
          </svg>
        )}

        {icon === "board" && (
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <rect
              x="3"
              y="3"
              width="18"
              height="18"
              rx="3"
            />

            <path d="M9 3v18M15 3v18M3 9h18M3 15h18" />
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

/*
 * ------------------------------------------------------------
 * INFO ROW
 * ------------------------------------------------------------
 */

function InfoRow({
  label,
  value,
  mono,
  accent,
  status,
}: {
  label: string;
  value: string;
  mono?: boolean;
  accent?: boolean;
  status?:
    | "success"
    | "warning"
    | "muted";
}) {
  return (
    <div className="signal-info-row">

      <span>
        {label}
      </span>

      <strong
        className={[
          mono
            ? "mono"
            : "",
          accent
            ? "accent"
            : "",
          status
            ? `status-${status}`
            : "",
        ]
          .filter(Boolean)
          .join(" ")}
      >
        {value}
      </strong>

    </div>
  );
}

/*
 * ------------------------------------------------------------
 * LEGEND
 * ------------------------------------------------------------
 */

function Legend({
  type,
  label,
}: {
  type:
    | "safe"
    | "mine"
    | "empty";
  label: string;
}) {
  return (
    <div className="signal-legend-item">

      <span
        className={`signal-legend-icon ${type}`}
      >
        {type === "safe" &&
          "✓"}

        {type === "mine" &&
          "×"}

        {type === "empty" &&
          ""}
      </span>

      <span>
        {label}
      </span>

    </div>
  );
}

/*
 * ------------------------------------------------------------
 * TIMELINE
 * ------------------------------------------------------------
 */

function TimelineItem({
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
      className={`signal-timeline-item ${
        last ? "last" : ""
      }`}
    >

      <div className="signal-timeline-marker">

        {active
          ? "✓"
          : ""}

      </div>

      {!last && (
        <div className="signal-timeline-line" />
      )}

      <div className="signal-timeline-content">

        <div className="signal-timeline-title">

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
