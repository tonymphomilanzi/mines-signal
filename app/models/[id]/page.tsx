"use client";

import { useEffect, useState } from "react";
import {
  useParams,
  useRouter,
} from "next/navigation";

import AdminShell from "@/components/layout/AdminShell";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

/* ============================================================
   TYPES
============================================================ */

type ModelStatus =
  | "ACTIVE"
  | "READY"
  | "ARCHIVED";

type BackendModel = {
  id: string;
  version: string;
  name: string;
  model_type: string;
  status: ModelStatus;
  description: string | null;
  observed_accuracy: number | null;
  confidence_score: number | null;
  board_size: number;
  maximum_attempts: number;
  created_at: string;
  updated_at: string;
  activated_at: string | null;
};

type Model = {
  id: string;
  version: string;
  name: string;
  type: string;
  status: ModelStatus;

  accuracy: number | null;
  confidence: number | null;

  signalsGenerated: number | null;
  signalsEvaluated: number | null;
  pendingResults: number | null;

  boardSize: string;
  supportedMines: number[];
  maximumAttempts: number;

  outputType: string;

  environment: string;

  createdAt: string;
  updatedAt: string;
  activatedAt: string | null;

  description: string;
};

/* ============================================================
   BACKTEST TYPES
============================================================ */

type PatternBacktestGame = {
  sequence: number;
  signal_id: string;
  signal_number: string | null;
  result_id: string;
  recorded_at: string;

  historical_results_used: number;

  predicted_safe_positions: number[];
  predicted_mine_positions: number[];

  actual_safe_positions: number[];
  actual_mine_positions: number[];

  safe_hits: number;
  safe_misses: number;
  safe_precision_percent: number;
  safe_recall_percent: number;

  mine_hits: number;
  mine_misses: number;
  mine_precision_percent: number;
  mine_recall_percent: number;

  combined_hits: number;
  combined_predictions: number;
  combined_precision_percent: number;

  overlap_count: number;
  confidence: number;
};

type PatternBacktestSkippedGame = {
  sequence: number;
  signal_id: string;
  result_id: string;
  recorded_at: string;
  reason: string;
};

type PatternBacktestSummary = {
  total_completed_results: number;
  evaluated_games: number;
  skipped_games: number;

  safe_predictions: number;
  safe_hits: number;
  safe_precision_percent: number;
  safe_recall_percent: number;

  mine_predictions: number;
  mine_hits: number;
  mine_precision_percent: number;
  mine_recall_percent: number;

  combined_predictions: number;
  combined_hits: number;
  combined_precision_percent: number;

  average_confidence: number;

  games_with_safe_hit: number;
  games_with_all_safe_predictions_correct: number;
  games_with_all_mine_predictions_correct: number;
};

type PatternBacktestResponse = {
  engine: string;
  engine_version: string;

  model_id: string;
  model_version: string;

  board_size: number;
  mine_count: number;

  summary: PatternBacktestSummary;

  games: PatternBacktestGame[];

  skipped_games: PatternBacktestSkippedGame[];
};

/* ============================================================
   HELPERS
============================================================ */

function formatDateTime(
  value: string | null
) {
  if (!value) {
    return "Not available";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatModelType(
  type: string
) {
  switch (type) {
    case "PRODUCTION":
      return "Production Model";

    case "EXPERIMENTAL":
      return "Experimental Model";

    case "DEVELOPMENT":
      return "Development Model";

    default:
      return type;
  }
}

function mapBackendModel(
  model: BackendModel
): Model {
  return {
    id: model.id,
    version: model.version,
    name: model.name,
    type: formatModelType(
      model.model_type
    ),
    status: model.status,

    accuracy: model.observed_accuracy,
    confidence: model.confidence_score,

    /*
     * These are still not exposed by the current
     * ModelResponse backend.
     */
    signalsGenerated: null,
    signalsEvaluated: null,
    pendingResults: null,

    boardSize:
      `${model.board_size} × ${model.board_size}`,

    /*
     * Current backend model schema does not
     * contain supported mine counts.
     */
    supportedMines: [3, 5, 7],

    maximumAttempts:
      model.maximum_attempts,

    outputType: "Safe Positions",

    environment:
      model.status === "ACTIVE"
        ? "Production"
        : model.status === "READY"
        ? "Staging"
        : "Archive",

    createdAt:
      formatDateTime(
        model.created_at
      ),

    updatedAt:
      formatDateTime(
        model.updated_at
      ),

    activatedAt:
      model.activated_at
        ? formatDateTime(
            model.activated_at
          )
        : null,

    description:
      model.description ??
      "No description has been provided for this model version.",
  };
}

/* ============================================================
   PAGE
============================================================ */

export default function ModelDetailsPage() {
  const router = useRouter();
  const params = useParams();

  const modelId = Array.isArray(
    params?.id
  )
    ? params.id[0]
    : params?.id;

  const [model, setModel] =
    useState<Model | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  const [actionLoading, setActionLoading] =
    useState(false);

  const [actionError, setActionError] =
    useState<string | null>(null);

  const [showDeleteConfirm, setShowDeleteConfirm] =
    useState(false);

  /* ==========================================================
     BACKTEST STATE
  ========================================================== */

  const [backtestMineCount, setBacktestMineCount] =
    useState(3);

  const [backtestLoading, setBacktestLoading] =
    useState(false);

  const [backtestError, setBacktestError] =
    useState<string | null>(null);

  const [backtestResult, setBacktestResult] =
    useState<PatternBacktestResponse | null>(
      null
    );

  /* ==========================================================
     LOAD MODEL
  ========================================================== */

  const loadModel = async () => {
    if (!modelId) {
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `${API_URL}/api/models/${encodeURIComponent(
          String(modelId)
        )}`,
        {
          method: "GET",
          credentials: "include",
          cache: "no-store",
        }
      );

      if (response.status === 404) {
        setModel(null);
        return;
      }

      if (!response.ok) {
        const body =
          await response.text();

        throw new Error(
          body ||
            `Unable to load model (${response.status}).`
        );
      }

      const data: BackendModel =
        await response.json();

      setModel(
        mapBackendModel(data)
      );
    } catch (err) {
      console.error(
        "Failed to load model:",
        err
      );

      setError(
        err instanceof Error
          ? err.message
          : "Unable to load model."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadModel();
  }, [modelId]);

  /* ==========================================================
     RUN BACKTEST
  ========================================================== */

  const runBacktest = async () => {
    if (!modelId || !model || backtestLoading) {
      return;
    }

    try {
      setBacktestLoading(true);
      setBacktestError(null);

      const response = await fetch(
        `${API_URL}/api/engines/pattern/backtest`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            model_id: String(modelId),
            board_size: Number(
              model.boardSize
                .split("×")[0]
                .trim()
            ),
            mine_count:
              backtestMineCount,
            limit: 100,
          }),
        }
      );

      const body =
        await response.text();

      if (!response.ok) {
        let message = body;

        try {
          const parsed = JSON.parse(body);

          if (
            parsed?.detail
          ) {
            message =
              typeof parsed.detail ===
              "string"
                ? parsed.detail
                : JSON.stringify(
                    parsed.detail
                  );
          }
        } catch {
          // Keep original response body.
        }

        throw new Error(
          message ||
            `Unable to run backtest (${response.status}).`
        );
      }

      const data: PatternBacktestResponse =
        JSON.parse(body);

      setBacktestResult(data);
    } catch (err) {
      console.error(
        "Failed to run model backtest:",
        err
      );

      setBacktestError(
        err instanceof Error
          ? err.message
          : "Unable to run model backtest."
      );
    } finally {
      setBacktestLoading(false);
    }
  };

  /* ==========================================================
     MODEL ACTIONS
  ========================================================== */

  const performModelAction = async (
    action:
      | "activate"
      | "archive"
      | "delete"
  ) => {
    if (!model || actionLoading) {
      return;
    }

    try {
      setActionLoading(true);
      setActionError(null);

      if (action === "delete") {
        const response =
          await fetch(
            `${API_URL}/api/models/${encodeURIComponent(
              model.id
            )}`,
            {
              method: "DELETE",
              credentials: "include",
            }
          );

        if (!response.ok) {
          const body =
            await response.text();

          throw new Error(
            body ||
              `Unable to delete model (${response.status}).`
          );
        }

        router.push("/models");
        router.refresh();

        return;
      }

      const endpoint =
        action === "activate"
          ? `${API_URL}/api/models/${encodeURIComponent(
              model.id
            )}/activate`
          : `${API_URL}/api/models/${encodeURIComponent(
              model.id
            )}/deactivate`;

      const response =
        await fetch(endpoint, {
          method: "PATCH",
          credentials: "include",
        });

      if (!response.ok) {
        const body =
          await response.text();

        throw new Error(
          body ||
            `Unable to ${action} model (${response.status}).`
        );
      }

      const updatedModel: BackendModel =
        await response.json();

      setModel(
        mapBackendModel(
          updatedModel
        )
      );
    } catch (err) {
      console.error(
        `Failed to ${action} model:`,
        err
      );

      setActionError(
        err instanceof Error
          ? err.message
          : `Unable to ${action} model.`
      );
    } finally {
      setActionLoading(false);
      setShowDeleteConfirm(false);
    }
  };

  /* ==========================================================
     DERIVED VALUES
  ========================================================== */

  const evaluationRate =
    model?.signalsGenerated &&
    model.signalsGenerated > 0 &&
    model.signalsEvaluated !== null
      ? Math.round(
          (model.signalsEvaluated /
            model.signalsGenerated) *
            100
        )
      : 0;

  const accuracyValue =
    model?.accuracy !== null &&
    model?.accuracy !== undefined
      ? Number(
          model.accuracy
        ).toFixed(1)
      : "—";

  const confidenceValue =
    model?.confidence !== null &&
    model?.confidence !== undefined
      ? Number(
          model.confidence
        ).toFixed(1)
      : "—";

  /* ==========================================================
     LOADING
  ========================================================== */

  if (loading) {
    return (
      <AdminShell>
        <div className="model-details-page">
          <div className="model-details-not-found">
            <div className="model-not-found-icon">
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
                <path d="M12 8v4l2 2" />
              </svg>
            </div>

            <h2>
              Loading model
            </h2>

            <p>
              Retrieving model information...
            </p>
          </div>
        </div>
      </AdminShell>
    );
  }

  /* ==========================================================
     ERROR
  ========================================================== */

  if (error) {
    return (
      <AdminShell>
        <div className="model-details-page">
          <div className="model-details-not-found">
            <div className="model-not-found-icon">
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
              Unable to load model
            </h2>

            <p>{error}</p>

            <button
              className="model-secondary-btn"
              onClick={loadModel}
            >
              Try Again
            </button>
          </div>
        </div>
      </AdminShell>
    );
  }

  /* ==========================================================
     NOT FOUND
  ========================================================== */

  if (!model) {
    return (
      <AdminShell>
        <div className="model-details-page">
          <div className="model-details-not-found">
            <div className="model-not-found-icon">
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
                <path d="M9 9l6 6M15 9l-6-6" />
              </svg>
            </div>

            <h2>
              Model not found
            </h2>

            <p>
              The model version you are looking for does
              not exist or is no longer available.
            </p>

            <button
              className="model-secondary-btn"
              onClick={() =>
                router.push("/models")
              }
            >
              ← Back to Models
            </button>
          </div>
        </div>
      </AdminShell>
    );
  }

  /* ==========================================================
     MAIN PAGE
  ========================================================== */

  return (
    <AdminShell>
      <div className="model-details-page">

        {/* =====================================================
            HEADER
        ===================================================== */}

        <div className="model-details-header">

          <div className="model-details-header-left">

            <button
              className="model-back-btn"
              onClick={() =>
                router.push(
                  "/models"
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

              Back to Models
            </button>

            <div className="model-breadcrumb">
              <span>
                Intelligence
              </span>

              <span>/</span>

              <span>
                Models
              </span>

              <span>/</span>

              <strong>
                {model.version}
              </strong>
            </div>

            <div className="model-title-row">

              <div className="model-title-icon">
                <svg
                  width="23"
                  height="23"
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

                  <path d="M8 8h8M8 12h8M8 16h5" />
                </svg>
              </div>

              <div>
                <h1>
                  {model.version}
                </h1>

                <p>
                  {model.name} ·{" "}
                  {model.type}
                </p>
              </div>

              <ModelStatusBadge
                status={model.status}
              />

            </div>

          </div>

          <div className="model-header-actions">

            <button
              className="model-secondary-btn"
              onClick={() =>
                router.push(
                  `/models/${model.id}`
                )
              }
              disabled={actionLoading}
            >
              Configure
            </button>

            {model.status ===
              "READY" && (
              <button
                className="model-primary-btn"
                onClick={() =>
                  performModelAction(
                    "activate"
                  )
                }
                disabled={
                  actionLoading
                }
              >
                {actionLoading
                  ? "Activating..."
                  : "Activate Model"}
              </button>
            )}

            {model.status ===
              "ACTIVE" && (
              <button
                className="model-danger-btn"
                onClick={() =>
                  performModelAction(
                    "archive"
                  )
                }
                disabled={
                  actionLoading
                }
              >
                {actionLoading
                  ? "Archiving..."
                  : "Archive"}
              </button>
            )}

          </div>

        </div>

        {/* =====================================================
            ACTION ERROR
        ===================================================== */}

        {actionError && (
          <div
            style={{
              marginBottom: 20,
              padding: "14px 16px",
              borderRadius: 12,
              background: "#fff5f5",
              border: "1px solid #fecaca",
              color: "#b91c1c",
              display: "flex",
              alignItems: "center",
              justifyContent:
                "space-between",
              gap: 16,
            }}
          >
            <span>
              {actionError}
            </span>

            <button
              className="model-secondary-btn"
              onClick={() =>
                setActionError(null)
              }
            >
              Dismiss
            </button>
          </div>
        )}

        {/* =====================================================
            SUMMARY
        ===================================================== */}

        <div className="model-overview-grid">

          <ModelStat
            label="Observed Accuracy"
            value={`${accuracyValue}%`}
            icon="accuracy"
            accent="green"
          />

          <ModelStat
            label="Model Confidence"
            value={`${confidenceValue}%`}
            icon="confidence"
            accent="blue"
          />

          <ModelStat
            label="Signals Evaluated"
            value={
              model.signalsEvaluated !==
              null
                ? String(
                    model.signalsEvaluated
                  )
                : "—"
            }
            icon="signals"
            accent="purple"
          />

          <ModelStat
            label="Pending Results"
            value={
              model.pendingResults !==
              null
                ? String(
                    model.pendingResults
                  )
                : "—"
            }
            icon="pending"
            accent="orange"
          />

        </div>

        {/* =====================================================
            MODEL OVERVIEW
        ===================================================== */}

        <div className="model-main-grid">

          <section className="model-card">

            <div className="model-card-header">

              <div>
                <h2>
                  Model Overview
                </h2>

                <p>
                  General information about this model
                  version.
                </p>
              </div>

              <ModelStatusBadge
                status={model.status}
              />

            </div>

            <div className="model-description">
              {model.description}
            </div>

            <div className="model-info-grid">

              <ModelInfo
                label="Model ID"
                value={model.id}
                mono
              />

              <ModelInfo
                label="Version"
                value={model.version}
                accent
              />

              <ModelInfo
                label="Type"
                value={model.type}
              />

              <ModelInfo
                label="Environment"
                value={model.environment}
              />

              <ModelInfo
                label="Created"
                value={model.createdAt}
              />

              <ModelInfo
                label="Last Updated"
                value={model.updatedAt}
              />

              <ModelInfo
                label="Activated"
                value={
                  model.activatedAt ??
                  "Not activated"
                }
              />

              <ModelInfo
                label="Output"
                value={
                  model.outputType
                }
              />

            </div>

          </section>

          {/* =================================================
              CONFIGURATION
          ================================================= */}

          <section className="model-card">

            <div className="model-card-header">

              <div>
                <h2>
                  Model Configuration
                </h2>

                <p>
                  Parameters supported by this version.
                </p>
              </div>

            </div>

            <div className="model-config-list">

              <ConfigRow
                label="Board Size"
                value={
                  model.boardSize
                }
              />

              <ConfigRow
                label="Maximum Attempts"
                value={String(
                  model.maximumAttempts
                )}
              />

              <ConfigRow
                label="Output Type"
                value={
                  model.outputType
                }
              />

              <div className="model-config-row">

                <span>
                  Supported Mines
                </span>

                <div className="model-mine-pills">

                  {model.supportedMines.map(
                    (mine) => (
                      <span key={mine}>
                        {mine} mines
                      </span>
                    )
                  )}

                </div>

              </div>

              <ConfigRow
                label="Signal Status"
                value={
                  model.status ===
                  "ACTIVE"
                    ? "Active"
                    : model.status ===
                      "READY"
                    ? "Ready"
                    : "Archived"
                }
              />

              <ConfigRow
                label="Confidence"
                value={
                  model.confidence !==
                    null &&
                  model.confidence !==
                    undefined
                    ? "Enabled"
                    : "Not configured"
                }
              />

            </div>

          </section>

        </div>

        {/* =====================================================
            PERFORMANCE
        ===================================================== */}

        <div className="model-performance-grid">

          <section className="model-card">

            <div className="model-card-header">

              <div>
                <h2>
                  Model Performance
                </h2>

                <p>
                  Performance based on evaluated signal
                  outcomes.
                </p>
              </div>

            </div>

            <div className="model-performance-main">

              <div className="model-performance-score">

                <strong>
                  {accuracyValue}%
                </strong>

                <span>
                  Observed accuracy
                </span>

              </div>

              <div className="model-performance-ring">

                <div
                  className="model-ring"
                  style={{
                    background:
                      model.accuracy !==
                        null &&
                      model.accuracy !==
                        undefined
                        ? `conic-gradient(
                            #229ed9 ${
                              model.accuracy *
                              3.6
                            }deg,
                            #edf1f4 0deg
                          )`
                        : "#edf1f4",
                  }}
                >
                  <div>
                    <strong>
                      {accuracyValue}%
                    </strong>
                  </div>
                </div>

              </div>

            </div>

            <div className="model-performance-bars">

              <PerformanceRow
                label="Evaluated"
                value={
                  model.signalsEvaluated ??
                  0
                }
                total={
                  model.signalsGenerated ??
                  0
                }
              />

              <PerformanceRow
                label="Pending"
                value={
                  model.pendingResults ??
                  0
                }
                total={
                  model.signalsGenerated ??
                  0
                }
                pending
              />

            </div>

            <div className="model-performance-note">

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
                Accuracy is based on recorded and
                evaluated outcomes. It is not a guaranteed
                probability of future results.
              </span>

            </div>

          </section>

          {/* =================================================
              USAGE
          ================================================= */}

          <section className="model-card">

            <div className="model-card-header">

              <div>
                <h2>
                  Model Usage
                </h2>

                <p>
                  Signal generation and evaluation
                  activity.
                </p>
              </div>

            </div>

            <div className="model-usage-number">

              <strong>
                {model.signalsGenerated ??
                  "—"}
              </strong>

              <span>
                Signals generated
              </span>

            </div>

            <div className="model-usage-progress">

              <div className="model-usage-progress-top">

                <span>
                  Evaluation coverage
                </span>

                <strong>
                  {model.signalsGenerated !==
                    null
                    ? `${evaluationRate}%`
                    : "—"}
                </strong>

              </div>

              <div className="model-progress-track">

                <div
                  className="model-progress-fill"
                  style={{
                    width: `${evaluationRate}%`,
                  }}
                />

              </div>

            </div>

            <div className="model-usage-stats">

              <UsageStat
                label="Generated"
                value={
                  model.signalsGenerated ??
                  0
                }
              />

              <UsageStat
                label="Evaluated"
                value={
                  model.signalsEvaluated ??
                  0
                }
              />

              <UsageStat
                label="Pending"
                value={
                  model.pendingResults ??
                  0
                }
              />

            </div>

            <div className="model-version-box">

              <span>
                Current version
              </span>

              <strong>
                {model.version}
              </strong>

            </div>

          </section>

        </div>

        {/* =====================================================
            HISTORICAL PERFORMANCE
        ===================================================== */}

        <section
          className="model-card"
          style={{
            marginTop: 20,
          }}
        >

          <div className="model-card-header">

            <div>
              <h2>
                Historical Performance
              </h2>

              <p>
                Walk-forward backtest performance using
                completed historical signal results.
              </p>
            </div>

          </div>

          {/* BACKTEST CONTROLS */}

          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent:
                "space-between",
              gap: 16,
              flexWrap: "wrap",
              marginBottom: 24,
              padding: 16,
              borderRadius: 14,
              background: "#f8fafc",
              border:
                "1px solid #e7edf2",
            }}
          >

            <div>
              <strong
                style={{
                  display: "block",
                  fontSize: 14,
                  color: "#182230",
                  marginBottom: 5,
                }}
              >
                Run historical backtest
              </strong>

              <span
                style={{
                  display: "block",
                  fontSize: 12,
                  color: "#718096",
                }}
              >
                Evaluate this model against historical
                results without creating new results.
              </span>
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                flexWrap: "wrap",
              }}
            >

              <select
                value={backtestMineCount}
                onChange={(event) =>
                  setBacktestMineCount(
                    Number(
                      event.target.value
                    )
                  )
                }
                disabled={backtestLoading}
                style={{
                  height: 42,
                  padding: "0 14px",
                  borderRadius: 10,
                  border:
                    "1px solid #d9e1e8",
                  background:
                    "#ffffff",
                  color:
                    "#253041",
                  fontSize: 13,
                  fontWeight: 600,
                  outline: "none",
                }}
              >
                {model.supportedMines.map(
                  (mine) => (
                    <option
                      key={mine}
                      value={mine}
                    >
                      {mine} Mines
                    </option>
                  )
                )}
              </select>

              <button
                className="model-primary-btn"
                onClick={runBacktest}
                disabled={
                  backtestLoading
                }
              >
                {backtestLoading
                  ? "Running Backtest..."
                  : "Run Backtest"}
              </button>

            </div>

          </div>

          {/* BACKTEST ERROR */}

          {backtestError && (
            <div
              style={{
                marginBottom: 20,
                padding: "14px 16px",
                borderRadius: 12,
                background:
                  "#fff5f5",
                border:
                  "1px solid #fecaca",
                color: "#b91c1c",
                display: "flex",
                alignItems:
                  "center",
                justifyContent:
                  "space-between",
                gap: 16,
                flexWrap: "wrap",
              }}
            >

              <span>
                {backtestError}
              </span>

              <button
                className="model-secondary-btn"
                onClick={() =>
                  setBacktestError(
                    null
                  )
                }
              >
                Dismiss
              </button>

            </div>
          )}

          {/* EMPTY STATE */}

          {!backtestResult &&
            !backtestLoading &&
            !backtestError && (
              <div
                style={{
                  padding:
                    "34px 20px",
                  textAlign:
                    "center",
                  borderRadius: 14,
                  background:
                    "#f8fafc",
                  border:
                    "1px dashed #d9e1e8",
                  marginBottom: 20,
                }}
              >

                <div
                  style={{
                    width: 46,
                    height: 46,
                    borderRadius:
                      "50%",
                    margin:
                      "0 auto 12px",
                    display: "flex",
                    alignItems:
                      "center",
                    justifyContent:
                      "center",
                    background:
                      "#eef6fb",
                    color:
                      "#229ed9",
                    fontSize: 21,
                  }}
                >
                  ↗
                </div>

                <strong
                  style={{
                    display:
                      "block",
                    fontSize: 14,
                    color:
                      "#253041",
                    marginBottom:
                      5,
                  }}
                >
                  No historical backtest loaded
                </strong>

                <span
                  style={{
                    display:
                      "block",
                    fontSize: 12,
                    color:
                      "#718096",
                  }}
                >
                  Select the mine configuration and run a
                  backtest to evaluate this model.
                </span>

              </div>
            )}

          {/* LOADING */}

          {backtestLoading && (
            <div
              style={{
                padding:
                  "30px 20px",
                textAlign:
                  "center",
                borderRadius: 14,
                background:
                  "#f8fafc",
                border:
                  "1px solid #e7edf2",
                marginBottom: 20,
              }}
            >

              <div
                style={{
                  width: 28,
                  height: 28,
                  margin:
                    "0 auto 12px",
                  borderRadius:
                    "50%",
                  border:
                    "3px solid #e6edf2",
                  borderTopColor:
                    "#229ed9",
                  animation:
                    "modelBacktestSpin 0.8s linear infinite",
                }}
              />

              <strong
                style={{
                  display:
                    "block",
                  fontSize: 13,
                  color:
                    "#253041",
                  marginBottom:
                    4,
                }}
              >
                Running historical backtest
              </strong>

              <span
                style={{
                  fontSize: 12,
                  color:
                    "#718096",
                }}
              >
                Evaluating the model against historical
                completed results...
              </span>

            </div>
          )}

          {/* BACKTEST RESULTS */}

          {backtestResult && (
            <>
              {/* RESULT HEADER */}

              <div
                style={{
                  display: "flex",
                  alignItems:
                    "center",
                  justifyContent:
                    "space-between",
                  gap: 16,
                  flexWrap:
                    "wrap",
                  marginBottom: 18,
                }}
              >

                <div>
                  <strong
                    style={{
                      display:
                        "block",
                      fontSize: 14,
                      color:
                        "#182230",
                    }}
                  >
                    Backtest Results
                  </strong>

                  <span
                    style={{
                      display:
                        "block",
                      marginTop: 4,
                      fontSize: 12,
                      color:
                        "#718096",
                    }}
                  >
                    {
                      backtestResult
                        .summary
                        .evaluated_games
                    }{" "}
                    evaluated games ·{" "}
                    {
                      backtestResult
                        .summary
                        .total_completed_results
                    }{" "}
                    completed historical results ·{" "}
                    {
                      backtestResult.board_size
                    }{" "}
                    ×{" "}
                    {
                      backtestResult.board_size
                    }{" "}
                    ·{" "}
                    {
                      backtestResult.mine_count
                    }{" "}
                    mines
                  </span>
                </div>

                <span
                  style={{
                    display:
                      "inline-flex",
                    alignItems:
                      "center",
                    padding:
                      "6px 10px",
                    borderRadius: 20,
                    background:
                      "#eef6fb",
                    color:
                      "#229ed9",
                    fontSize: 11,
                    fontWeight: 700,
                  }}
                >
                  Pattern Engine v
                  {
                    backtestResult.engine_version
                  }
                </span>

              </div>

              {/* PRIMARY METRICS */}

              <div
                style={{
                  display:
                    "grid",
                  gridTemplateColumns:
                    "repeat(auto-fit, minmax(180px, 1fr))",
                  gap: 12,
                  marginBottom: 20,
                }}
              >

                <HistoricalMetric
                  label="Combined Precision"
                  value={`${backtestResult.summary.combined_precision_percent.toFixed(
                    2
                  )}%`}
                  description={`${backtestResult.summary.combined_hits} hits / ${backtestResult.summary.combined_predictions} predictions`}
                  accent="green"
                />

                <HistoricalMetric
                  label="Safe Precision"
                  value={`${backtestResult.summary.safe_precision_percent.toFixed(
                    2
                  )}%`}
                  description={`${backtestResult.summary.safe_hits} safe hits`}
                  accent="blue"
                />

                <HistoricalMetric
                  label="Safe Recall"
                  value={`${backtestResult.summary.safe_recall_percent.toFixed(
                    2
                  )}%`}
                  description="Historical safe-position coverage"
                  accent="purple"
                />

                <HistoricalMetric
                  label="Mine Precision"
                  value={`${backtestResult.summary.mine_precision_percent.toFixed(
                    2
                  )}%`}
                  description={`${backtestResult.summary.mine_hits} mine hits`}
                  accent="orange"
                />

                <HistoricalMetric
                  label="Mine Recall"
                  value={`${backtestResult.summary.mine_recall_percent.toFixed(
                    2
                  )}%`}
                  description="Historical mine-position coverage"
                  accent="red"
                />

              </div>

              {/* SECONDARY METRICS */}

              <div
                style={{
                  display:
                    "grid",
                  gridTemplateColumns:
                    "repeat(auto-fit, minmax(160px, 1fr))",
                  gap: 12,
                  marginBottom: 22,
                }}
              >

                <HistoricalSmallMetric
                  label="Evaluated Games"
                  value={
                    backtestResult
                      .summary
                      .evaluated_games
                  }
                />

                <HistoricalSmallMetric
                  label="Safe Predictions"
                  value={
                    backtestResult
                      .summary
                      .safe_predictions
                  }
                />

                <HistoricalSmallMetric
                  label="Mine Predictions"
                  value={
                    backtestResult
                      .summary
                      .mine_predictions
                  }
                />

                <HistoricalSmallMetric
                  label="Games With Safe Hit"
                  value={
                    backtestResult
                      .summary
                      .games_with_safe_hit
                  }
                />

                <HistoricalSmallMetric
                  label="All Safe Correct"
                  value={
                    backtestResult
                      .summary
                      .games_with_all_safe_predictions_correct
                  }
                />

                <HistoricalSmallMetric
                  label="All Mines Correct"
                  value={
                    backtestResult
                      .summary
                      .games_with_all_mine_predictions_correct
                  }
                />

              </div>

              {/* PRECISION BREAKDOWN */}

              <div
                style={{
                  marginBottom: 22,
                  padding: 18,
                  borderRadius: 14,
                  background:
                    "#f8fafc",
                  border:
                    "1px solid #e7edf2",
                }}
              >

                <div
                  style={{
                    marginBottom: 15,
                  }}
                >
                  <strong
                    style={{
                      display:
                        "block",
                      fontSize: 13,
                      color:
                        "#253041",
                    }}
                  >
                    Precision Breakdown
                  </strong>

                  <span
                    style={{
                      display:
                        "block",
                      marginTop: 3,
                      fontSize: 11,
                      color:
                        "#718096",
                    }}
                  >
                    Precision across the evaluated historical
                    sample.
                  </span>
                </div>

                <HistoricalBar
                  label="Combined"
                  value={
                    backtestResult
                      .summary
                      .combined_precision_percent
                  }
                />

                <HistoricalBar
                  label="Safe"
                  value={
                    backtestResult
                      .summary
                      .safe_precision_percent
                  }
                />

                <HistoricalBar
                  label="Mine"
                  value={
                    backtestResult
                      .summary
                      .mine_precision_percent
                  }
                />

              </div>

              {/* HISTORICAL GAMES */}

              <div>

                <div
                  style={{
                    marginBottom: 12,
                  }}
                >

                  <strong
                    style={{
                      display:
                        "block",
                      fontSize: 14,
                      color:
                        "#253041",
                    }}
                  >
                    Historical Games
                  </strong>

                  <span
                    style={{
                      display:
                        "block",
                      marginTop: 4,
                      fontSize: 12,
                      color:
                        "#718096",
                    }}
                  >
                    Walk-forward results. Each game is evaluated
                    using only historical results available before
                    that game.
                  </span>

                </div>

                <div
                  style={{
                    overflowX:
                      "auto",
                    border:
                      "1px solid #e7edf2",
                    borderRadius: 14,
                  }}
                >

                  <div
                    style={{
                      minWidth: 760,
                    }}
                  >

                    <div
                      style={{
                        display:
                          "grid",
                        gridTemplateColumns:
                          "70px 1fr 100px 100px 100px 110px",
                        gap: 12,
                        padding:
                          "12px 16px",
                        background:
                          "#f8fafc",
                        borderBottom:
                          "1px solid #e7edf2",
                        fontSize: 11,
                        fontWeight: 700,
                        color:
                          "#718096",
                      }}
                    >
                      <span>
                        Game
                      </span>

                      <span>
                        Signal
                      </span>

                      <span>
                        Safe Hits
                      </span>

                      <span>
                        Mine Hits
                      </span>

                      <span>
                        Combined
                      </span>

                      <span>
                        History Used
                      </span>
                    </div>

                    {backtestResult.games.map(
                      (game) => (
                        <div
                          key={`${game.sequence}-${game.result_id}`}
                          style={{
                            display:
                              "grid",
                            gridTemplateColumns:
                              "70px 1fr 100px 100px 100px 110px",
                            gap: 12,
                            padding:
                              "14px 16px",
                            borderBottom:
                              "1px solid #edf1f4",
                            alignItems:
                              "center",
                            fontSize: 12,
                            color:
                              "#253041",
                          }}
                        >

                          <span
                            style={{
                              fontWeight:
                                700,
                            }}
                          >
                            #{game.sequence}
                          </span>

                          <div>

                            <strong
                              style={{
                                display:
                                  "block",
                                fontSize:
                                  12,
                              }}
                            >
                              {game.signal_number ??
                                "Signal"}
                            </strong>

                            <span
                              style={{
                                display:
                                  "block",
                                marginTop:
                                  3,
                                color:
                                  "#8a96a3",
                                fontSize:
                                  10,
                              }}
                            >
                              {formatDateTime(
                                game.recorded_at
                              )}
                            </span>

                          </div>

                          <span
                            style={{
                              fontWeight:
                                700,
                              color:
                                "#229ed9",
                            }}
                          >
                            {game.safe_hits}
                          </span>

                          <span
                            style={{
                              fontWeight:
                                700,
                              color:
                                "#e35d6a",
                            }}
                          >
                            {game.mine_hits}
                          </span>

                          <span
                            style={{
                              fontWeight:
                                700,
                              color:
                                game.combined_precision_percent >=
                                80
                                  ? "#16835b"
                                  : "#c67a00",
                            }}
                          >
                            {game.combined_precision_percent.toFixed(
                              2
                            )}
                            %
                          </span>

                          <span
                            style={{
                              color:
                                "#718096",
                            }}
                          >
                            {
                              game.historical_results_used
                            }
                          </span>

                        </div>
                      )
                    )}

                  </div>

                </div>

              </div>

              {/* SKIPPED GAMES */}

              {backtestResult.skipped_games
                .length > 0 && (
                <div
                  style={{
                    marginTop: 16,
                    padding: 14,
                    borderRadius: 12,
                    background:
                      "#fffaf0",
                    border:
                      "1px solid #f7dfae",
                    color:
                      "#8a6415",
                    fontSize: 11,
                  }}
                >
                  <strong>
                    {
                      backtestResult
                        .skipped_games
                        .length
                    }{" "}
                    game
                    {
                      backtestResult
                        .skipped_games
                        .length ===
                      1
                        ? ""
                        : "s"
                    }{" "}
                    skipped
                  </strong>{" "}
                  because there was no prior historical
                  data available for walk-forward evaluation.
                </div>
              )}

              {/* METHODOLOGY */}

              <div
                style={{
                  marginTop: 18,
                  padding: 14,
                  borderRadius: 12,
                  background:
                    "#f8fafc",
                  border:
                    "1px solid #e7edf2",
                  display: "flex",
                  gap: 10,
                  alignItems:
                    "flex-start",
                }}
              >

                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  style={{
                    flexShrink: 0,
                    marginTop: 1,
                    color:
                      "#718096",
                  }}
                >
                  <circle
                    cx="12"
                    cy="12"
                    r="9"
                  />

                  <path d="M12 11v5M12 8h.01" />
                </svg>

                <div>

                  <strong
                    style={{
                      display:
                        "block",
                      marginBottom:
                        4,
                      fontSize: 11,
                      color:
                        "#4a5568",
                    }}
                  >
                    Historical metric notice
                  </strong>

                  <span
                    style={{
                      display:
                        "block",
                      fontSize: 11,
                      lineHeight:
                        1.55,
                      color:
                        "#718096",
                    }}
                  >
                    These metrics describe performance on the
                    available historical sample only. They are
                    not guaranteed probabilities of future game
                    outcomes. Larger and more representative
                    datasets are needed before drawing conclusions
                    about model performance.
                  </span>

                </div>

              </div>

            </>
          )}

        </section>

        {/* =====================================================
            SUPPORTED CONFIGURATIONS
        ===================================================== */}

        <section className="model-card">

          <div className="model-card-header">

            <div>
              <h2>
                Supported Configurations
              </h2>

              <p>
                Board configurations currently supported
                by this model version.
              </p>
            </div>

          </div>

          <div className="model-config-table">

            <div className="model-config-table-head">
              <span>Board</span>
              <span>Mines</span>
              <span>Attempts</span>
              <span>Output</span>
              <span>Status</span>
            </div>

            {model.supportedMines.map(
              (mineCount) => (
                <div
                  className="model-config-table-row"
                  key={mineCount}
                >

                  <span>
                    {model.boardSize}
                  </span>

                  <span>
                    <strong>
                      {mineCount}
                    </strong>{" "}
                    mines
                  </span>

                  <span>
                    {model.maximumAttempts}
                  </span>

                  <span>
                    {model.outputType}
                  </span>

                  <span>
                    <span className="model-enabled-badge">
                      Enabled
                    </span>
                  </span>

                </div>
              )
            )}

          </div>

        </section>

        {/* =====================================================
            ACTIVITY
        ===================================================== */}

        <section className="model-card">

          <div className="model-card-header">

            <div>
              <h2>
                Model Activity
              </h2>

              <p>
                Recent events associated with this model
                version.
              </p>
            </div>

          </div>

          <div className="model-timeline">

            <TimelineItem
              title="Configuration updated"
              description="Model configuration was reviewed and updated."
              date={model.updatedAt}
              active
            />

            {model.status ===
              "ACTIVE" && (
              <TimelineItem
                title="Model activated"
                description="This model version was activated for production signal generation."
                date={
                  model.activatedAt ??
                  "Not available"
                }
                active
              />
            )}

            <TimelineItem
              title="Model created"
              description="Model version was registered in the system."
              date={model.createdAt}
              active
              last
            />

          </div>

        </section>

        {/* =====================================================
            DELETE
        ===================================================== */}

        {model.status !==
          "ACTIVE" && (
          <section
            className="model-card"
            style={{
              marginTop: 20,
              borderColor:
                "#fecaca",
            }}
          >

            <div className="model-card-header">

              <div>
                <h2>
                  Danger Zone
                </h2>

                <p>
                  Permanently remove this model version
                  from the system.
                </p>
              </div>

              <button
                className="model-danger-btn"
                onClick={() =>
                  setShowDeleteConfirm(
                    true
                  )
                }
                disabled={
                  actionLoading
                }
              >
                Delete Model
              </button>

            </div>

          </section>
        )}

        {/* =====================================================
            DELETE CONFIRMATION
        ===================================================== */}

        {showDeleteConfirm && (
          <div
            style={{
              position: "fixed",
              inset: 0,
              zIndex: 1000,
              background:
                "rgba(15, 23, 42, 0.45)",
              display: "flex",
              alignItems:
                "center",
              justifyContent:
                "center",
              padding: 20,
            }}
          >

            <div
              style={{
                width: "100%",
                maxWidth: 440,
                background:
                  "#ffffff",
                borderRadius: 18,
                padding: 24,
                boxShadow:
                  "0 20px 60px rgba(0,0,0,.20)",
              }}
            >

              <h2
                style={{
                  margin:
                    "0 0 8px",
                  fontSize: 20,
                }}
              >
                Delete model?
              </h2>

              <p
                style={{
                  margin:
                    "0 0 22px",
                  color:
                    "#6b7785",
                  lineHeight:
                    1.6,
                }}
              >
                This will permanently delete{" "}
                <strong>
                  {model.version}
                </strong>
                . This action cannot be undone.
              </p>

              <div
                style={{
                  display: "flex",
                  justifyContent:
                    "flex-end",
                  gap: 10,
                }}
              >

                <button
                  className="model-secondary-btn"
                  onClick={() =>
                    setShowDeleteConfirm(
                      false
                    )
                  }
                  disabled={
                    actionLoading
                  }
                >
                  Cancel
                </button>

                <button
                  className="model-danger-btn"
                  onClick={() =>
                    performModelAction(
                      "delete"
                    )
                  }
                  disabled={
                    actionLoading
                  }
                >
                  {actionLoading
                    ? "Deleting..."
                    : "Delete Model"}
                </button>

              </div>

            </div>

          </div>
        )}

      </div>

      {/* =======================================================
          BACKTEST LOADING ANIMATION
      ======================================================= */}

      <style jsx global>{`
        @keyframes modelBacktestSpin {
          to {
            transform: rotate(360deg);
          }
        }
      `}</style>

    </AdminShell>
  );
}

/* ============================================================
   STATUS BADGE
============================================================ */

function ModelStatusBadge({
  status,
}: {
  status: ModelStatus;
}) {
  const config = {
    ACTIVE: {
      label: "Active",
      className: "active",
    },

    READY: {
      label: "Ready",
      className: "ready",
    },

    ARCHIVED: {
      label: "Archived",
      className: "archived",
    },
  }[status];

  return (
    <span
      className={`model-status-badge ${config.className}`}
    >
      <span />
      {config.label}
    </span>
  );
}

/* ============================================================
   STAT
============================================================ */

function ModelStat({
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
    <div className="model-stat-card">

      <div
        className={`model-stat-icon ${accent}`}
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

        {icon === "signals" && (
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M4 18V6" />
            <path d="M4 18h16" />
            <path d="M8 15v-3" />
            <path d="M12 15V8" />
            <path d="M16 15v-5" />
          </svg>
        )}

        {icon === "pending" && (
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

            <path d="M12 7v5l3 2" />
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
   INFO
============================================================ */

function ModelInfo({
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
    <div className="model-info-item">

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
   CONFIG ROW
============================================================ */

function ConfigRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="model-config-row">

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

    </div>
  );
}

/* ============================================================
   PERFORMANCE
============================================================ */

function PerformanceRow({
  label,
  value,
  total,
  pending,
}: {
  label: string;
  value: number;
  total: number;
  pending?: boolean;
}) {
  const percentage =
    total > 0
      ? Math.min(
          100,
          (value / total) * 100
        )
      : 0;

  return (
    <div className="model-performance-row">

      <div className="model-performance-label">

        <span>
          {label}
        </span>

        <strong>
          {total > 0
            ? value
            : "—"}
        </strong>

      </div>

      <div className="model-performance-track">

        <div
          className={`model-performance-fill ${
            pending
              ? "pending"
              : ""
          }`}
          style={{
            width: `${percentage}%`,
          }}
        />

      </div>

    </div>
  );
}

/* ============================================================
   USAGE STAT
============================================================ */

function UsageStat({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="model-usage-stat">

      <strong>
        {value === 0
          ? "—"
          : value}
      </strong>

      <span>
        {label}
      </span>

    </div>
  );
}

/* ============================================================
   HISTORICAL METRIC
============================================================ */

function HistoricalMetric({
  label,
  value,
  description,
  accent,
}: {
  label: string;
  value: string;
  description: string;
  accent:
    | "green"
    | "blue"
    | "purple"
    | "orange"
    | "red";
}) {
  const accentColors = {
    green: {
      background: "#edf9f3",
      color: "#16835b",
    },

    blue: {
      background: "#eef6fb",
      color: "#229ed9",
    },

    purple: {
      background: "#f4f0ff",
      color: "#7557c7",
    },

    orange: {
      background: "#fff7eb",
      color: "#c67a00",
    },

    red: {
      background: "#fff1f2",
      color: "#d84c5b",
    },
  };

  const colors =
    accentColors[accent];

  return (
    <div
      style={{
        padding: 16,
        borderRadius: 14,
        background: "#ffffff",
        border:
          "1px solid #e7edf2",
      }}
    >

      <span
        style={{
          display: "block",
          fontSize: 11,
          fontWeight: 700,
          color: "#718096",
          marginBottom: 8,
        }}
      >
        {label}
      </span>

      <strong
        style={{
          display: "block",
          fontSize: 23,
          lineHeight: 1.1,
          color: colors.color,
          marginBottom: 7,
        }}
      >
        {value}
      </strong>

      <span
        style={{
          display:
            "inline-block",
          padding:
            "4px 7px",
          borderRadius: 6,
          background:
            colors.background,
          color:
            colors.color,
          fontSize: 10,
          lineHeight: 1.3,
        }}
      >
        {description}
      </span>

    </div>
  );
}

/* ============================================================
   HISTORICAL SMALL METRIC
============================================================ */

function HistoricalSmallMetric({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div
      style={{
        padding: 14,
        borderRadius: 12,
        background: "#ffffff",
        border:
          "1px solid #e7edf2",
      }}
    >

      <strong
        style={{
          display: "block",
          fontSize: 19,
          color: "#253041",
          marginBottom: 4,
        }}
      >
        {value}
      </strong>

      <span
        style={{
          display: "block",
          fontSize: 10,
          color: "#718096",
          lineHeight: 1.4,
        }}
      >
        {label}
      </span>

    </div>
  );
}

/* ============================================================
   HISTORICAL BAR
============================================================ */

function HistoricalBar({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  const safeValue =
    Math.max(
      0,
      Math.min(100, value)
    );

  return (
    <div
      style={{
        marginBottom: 14,
      }}
    >

      <div
        style={{
          display: "flex",
          alignItems:
            "center",
          justifyContent:
            "space-between",
          marginBottom: 7,
        }}
      >

        <span
          style={{
            fontSize: 11,
            fontWeight: 700,
            color: "#596575",
          }}
        >
          {label}
        </span>

        <strong
          style={{
            fontSize: 11,
            color: "#253041",
          }}
        >
          {value.toFixed(2)}%
        </strong>

      </div>

      <div
        style={{
          height: 7,
          width: "100%",
          borderRadius: 20,
          background: "#e9eef2",
          overflow: "hidden",
        }}
      >

        <div
          style={{
            height: "100%",
            width: `${safeValue}%`,
            borderRadius: 20,
            background:
              "linear-gradient(90deg, #229ed9, #16835b)",
            transition:
              "width 300ms ease",
          }}
        />

      </div>

    </div>
  );
}

/* ============================================================
   TIMELINE
============================================================ */

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
      className={`model-timeline-item ${
        last ? "last" : ""
      }`}
    >

      <div className="model-timeline-marker">
        {active ? "✓" : ""}
      </div>

      {!last && (
        <div className="model-timeline-line" />
      )}

      <div className="model-timeline-content">

        <div className="model-timeline-title">

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