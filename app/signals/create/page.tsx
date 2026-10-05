"use client";

import { useEffect, useState } from "react";
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

type PredictionEngine = "PATTERN" | "ML";

type Model = {
  id: string;
  version: string;
  name: string;
  model_type: string;
  status: string;
  description: string | null;
  observed_accuracy: number | null;
  confidence_score: number | null;
  board_size: number;
  maximum_attempts: number;
  created_at: string;
  updated_at: string;
  activated_at: string | null;
};

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

type SignalResponse = {
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
  prediction_engine?: PredictionEngine;
  generated_at: string;
  published_at: string | null;
  confirmed_at: string | null;
  result_status: string | null;

  /*
   * Backend relationship.
   *
   * The signal returns the model selected
   * when the signal was created.
   */
  model_id?: string | null;
};

type ModelListResponse = {
  items: Model[];
  total: number;
};

type AnalyzeResponse = {
  message: string;
  signal: SignalResponse;
  prediction: Prediction;
};

export default function CreateSignalPage() {
  // ============================================================
  // API
  // ============================================================

  const API_URL =
    process.env.NEXT_PUBLIC_API_URL ||
    "http://127.0.0.1:8000";

  // ============================================================
  // FORM STATE
  // ============================================================

  const [mineCount, setMineCount] = useState("3");

  const [attempts, setAttempts] = useState("3");

  /*
   * Actual database model UUID.
   */
  const [selectedModelId, setSelectedModelId] =
    useState("");

  const [models, setModels] = useState<Model[]>([]);

  const [modelsLoading, setModelsLoading] =
    useState(true);

  const [modelsError, setModelsError] =
    useState("");

  /*
   * Prediction engine is separate from the model.
   *
   * PATTERN:
   *   Pattern Engine 2.0.0
   *
   * ML:
   *   Random Forest 1.0.0
   */
  const [predictionEngine, setPredictionEngine] =
    useState<PredictionEngine>("PATTERN");

  /*
   * Before analysis these are manual selections.
   * After analysis they are replaced by the backend prediction.
   */
  const [selectedCells, setSelectedCells] =
    useState<number[]>([
      8,
      9,
      10,
      22,
      23,
      24,
    ]);

  const [predictedMinePositions, setPredictedMinePositions] =
    useState<number[]>([]);

  // ============================================================
  // SIGNAL STATE
  // ============================================================

  const [signalId, setSignalId] =
    useState<string | null>(null);

  const [signalNumber, setSignalNumber] =
    useState<string | null>(null);

  const [signalStatus, setSignalStatus] =
    useState<SignalStatus>("DRAFT");

  const [confidence, setConfidence] =
    useState<number | null>(null);

  const [analysisStarted, setAnalysisStarted] =
    useState(false);

  // ============================================================
  // UI STATE
  // ============================================================

  const [loading, setLoading] = useState(false);

  const [loadingAction, setLoadingAction] =
    useState<"create" | "analyze" | null>(null);

  const [error, setError] = useState("");

  const [success, setSuccess] = useState("");

  // ============================================================
  // LOAD MODELS
  // ============================================================

  useEffect(() => {
    let mounted = true;

    const loadModels = async () => {
      setModelsLoading(true);
      setModelsError("");

      try {
        const response = await fetch(
          `${API_URL}/api/models`,
          {
            method: "GET",
            credentials: "include",
            cache: "no-store",
          }
        );

        let data: ModelListResponse | null =
          null;

        try {
          data = await response.json();
        } catch {
          data = null;
        }

        if (!response.ok) {
          throw new Error(
            (data as any)?.detail ||
              "Unable to load models."
          );
        }

        if (!data) {
          throw new Error(
            "The server returned an empty model response."
          );
        }

        if (!mounted) {
          return;
        }

        /*
         * Only ACTIVE and READY models can be
         * selected for new signals.
         */
        const availableModels =
          data.items.filter(
            (model) =>
              model.status === "ACTIVE" ||
              model.status === "READY"
          );

        setModels(availableModels);

        /*
         * Prefer ACTIVE.
         *
         * Otherwise use the first READY model.
         */
        const activeModel =
          availableModels.find(
            (model) =>
              model.status === "ACTIVE"
          );

        const defaultModel =
          activeModel ||
          availableModels[0];

        if (defaultModel) {
          setSelectedModelId(
            defaultModel.id
          );
        }
      } catch (requestError) {
        console.error(
          "Load models failed:",
          requestError
        );

        if (!mounted) {
          return;
        }

        setModelsError(
          requestError instanceof Error
            ? requestError.message
            : "Unable to load models."
        );
      } finally {
        if (mounted) {
          setModelsLoading(false);
        }
      }
    };

    loadModels();

    return () => {
      mounted = false;
    };
  }, [API_URL]);

  // ============================================================
  // DERIVED STATE
  // ============================================================

  const hasCreatedSignal =
    signalId !== null;

  const isDraft =
    signalStatus === "DRAFT";

  const isAnalyzed =
    signalStatus === "ANALYZED" ||
    signalStatus === "CONFIRMED" ||
    signalStatus === "PUBLISHED" ||
    signalStatus === "RESULT_PENDING" ||
    signalStatus === "SUCCESS" ||
    signalStatus === "FAILED";

  const selectedModel =
    models.find(
      (model) =>
        model.id === selectedModelId
    ) || null;

  const selectedModelVersion =
    selectedModel?.version || "—";

  const predictionEngineName =
    predictionEngine === "ML"
      ? "ML Engine"
      : "Pattern Engine";

  const predictionEngineVersion =
    predictionEngine === "ML"
      ? "1.0.0"
      : "2.0.0";

  const predictionEngineDisplay =
    `${predictionEngineName} ${predictionEngineVersion}`;

  // ============================================================
  // BOARD
  // ============================================================

  const toggleCell = (
    position: number
  ) => {
    /*
     * Once the signal has been created,
     * the board is controlled by backend prediction.
     */
    if (hasCreatedSignal || loading) {
      return;
    }

    setSelectedCells((current) =>
      current.includes(position)
        ? current.filter(
            (item) => item !== position
          )
        : [
            ...current,
            position,
          ]
    );
  };

  const clearSelection = () => {
    if (hasCreatedSignal || loading) {
      return;
    }

    setSelectedCells([]);
  };

  // ============================================================
  // CREATE SIGNAL
  // ============================================================

  const createSignal = async () => {
    if (loading) {
      return;
    }

    /*
     * Do not create another signal from
     * the same page.
     */
    if (signalId) {
      setError(
        "This signal has already been created. Analyze the signal to generate its positions."
      );
      return;
    }

    if (!selectedModelId) {
      setError(
        "Please select a model before creating the signal."
      );
      return;
    }

    if (!selectedModel) {
      setError(
        "The selected model could not be found."
      );
      return;
    }

    setLoading(true);
    setLoadingAction("create");
    setError("");
    setSuccess("");

    try {
      const response = await fetch(
        `${API_URL}/api/signals`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          credentials: "include",

          body: JSON.stringify({
            game: "Mines Classic",
            board_size: 5,
            mine_count:
              Number(mineCount),
            attempts:
              Number(attempts),

            /*
             * Selected SignalModel.
             */
            model_id: selectedModelId,

            /*
             * Selected production engine.
             */
            prediction_engine:
              predictionEngine,
          }),
        }
      );

      let data: SignalResponse | null =
        null;

      try {
        data = await response.json();
      } catch {
        data = null;
      }

      if (!response.ok) {
        setError(
          (data as any)?.detail ||
            "Unable to create signal."
        );
        return;
      }

      if (!data) {
        setError(
          "The server returned an empty response."
        );
        return;
      }

      setSignalId(data.id);

      setSignalNumber(
        data.signal_number
      );

      setSignalStatus(
        data.status || "DRAFT"
      );

      setConfidence(
        data.confidence ?? null
      );

      /*
       * Backend is the source of truth.
       */
      if (data.model_id) {
        setSelectedModelId(
          data.model_id
        );
      }

      /*
       * Synchronize the selected engine
       * with the backend response.
       */
      if (data.prediction_engine) {
        setPredictionEngine(
          data.prediction_engine
        );
      }

      setAnalysisStarted(false);

      setPredictedMinePositions([]);

      /*
       * A newly created signal has no prediction.
       */
      setSelectedCells([]);

      const returnedEngine =
        data.prediction_engine ||
        predictionEngine;

      const engineName =
        returnedEngine === "ML"
          ? "ML Engine"
          : "Pattern Engine";

      const engineVersion =
        returnedEngine === "ML"
          ? "1.0.0"
          : "2.0.0";

      setSuccess(
        `Signal ${data.signal_number} created successfully using ${engineName} ${engineVersion} with model ${selectedModel.version}. Next step: analyze the signal to generate positions.`
      );
    } catch (requestError) {
      console.error(
        "Create signal failed:",
        requestError
      );

      setError(
        "Unable to connect to the signal server."
      );
    } finally {
      setLoading(false);
      setLoadingAction(null);
    }
  };

  // ============================================================
  // ANALYZE SIGNAL
  // ============================================================

  const analyzeSignal = async () => {
    if (!signalId) {
      setError(
        "Create the signal before analyzing it."
      );
      return;
    }

    if (loading) {
      return;
    }

    if (!isDraft) {
      setError(
        "This signal has already been analyzed."
      );
      return;
    }

    setLoading(true);
    setLoadingAction("analyze");
    setError("");
    setSuccess("");

    try {
      const response = await fetch(
        `${API_URL}/api/signals/${signalId}/analyze`,
        {
          method: "POST",
          credentials: "include",
          cache: "no-store",
        }
      );

      let data: AnalyzeResponse | null =
        null;

      try {
        data = await response.json();
      } catch {
        data = null;
      }

      if (!response.ok) {
        setError(
          (data as any)?.detail ||
            "Unable to analyze signal."
        );
        return;
      }

      if (!data) {
        setError(
          "The server returned an empty analysis response."
        );
        return;
      }

      const returnedSignal =
        data.signal;

      const prediction =
        data.prediction;

      // ----------------------------------------------------------
      // SIGNAL
      // ----------------------------------------------------------

      setSignalStatus(
        returnedSignal.status ||
          "ANALYZED"
      );

      setSignalNumber(
        returnedSignal.signal_number ||
          signalNumber
      );

      setConfidence(
        prediction?.confidence ??
          returnedSignal.confidence ??
          null
      );

      /*
       * Synchronize model with backend.
       */
      if (returnedSignal.model_id) {
        setSelectedModelId(
          returnedSignal.model_id
        );
      }

      /*
       * Synchronize engine with backend.
       */
      if (
        returnedSignal.prediction_engine
      ) {
        setPredictionEngine(
          returnedSignal.prediction_engine
        );
      }

      // ----------------------------------------------------------
      // PREDICTION
      // ----------------------------------------------------------

      const safePositions =
        Array.isArray(
          prediction?.safe_positions
        )
          ? prediction.safe_positions
          : [];

      const minePositions =
        Array.isArray(
          prediction?.predicted_mine_positions
        )
          ? prediction.predicted_mine_positions
          : [];

      /*
       * Backend prediction controls the board.
       */
      setSelectedCells(
        safePositions
      );

      setPredictedMinePositions(
        minePositions
      );

      setAnalysisStarted(true);

      const returnedEngine =
        returnedSignal.prediction_engine ||
        predictionEngine;

      const engineName =
        returnedEngine === "ML"
          ? "ML Engine"
          : "Pattern Engine";

      const engineVersion =
        returnedEngine === "ML"
          ? "1.0.0"
          : "2.0.0";

      setSuccess(
        `Signal ${returnedSignal.signal_number} analyzed successfully using ${engineName} ${engineVersion} with model ${prediction?.model_version || selectedModelVersion}. ${safePositions.length} safe positions detected.`
      );
    } catch (requestError) {
      console.error(
        "Analyze signal failed:",
        requestError
      );

      setError(
        "Unable to connect to the signal server."
      );
    } finally {
      setLoading(false);
      setLoadingAction(null);
    }
  };

  // ============================================================
  // BOARD CELL STATE
  // ============================================================

  const getBoardCellClass = (
    position: number
  ) => {
    const isSafe =
      selectedCells.includes(
        position
      );

    const isMine =
      predictedMinePositions.includes(
        position
      );

    if (isMine) {
      return "large-board-cell predicted-mine";
    }

    if (isSafe) {
      return "large-board-cell selected";
    }

    return "large-board-cell";
  };

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <AdminShell>
      <div className="create-signal-page">

        {/* =====================================================
            PAGE HEADER
        ====================================================== */}

        <div className="create-page-header">

          <div>
            <div className="breadcrumb">
              Signals <span>/</span> Create Signal
            </div>

            <h1>Create Signal</h1>

            <p>
              Configure and prepare a new Mines signal for analysis.
            </p>
          </div>

          <Link
            href="/signals"
            className="back-button"
          >
            ← Back to Signals
          </Link>

        </div>

        {/* =====================================================
            FEEDBACK
        ====================================================== */}

        {error && (
          <div
            style={{
              marginBottom: "18px",
              padding: "13px 16px",
              borderRadius: "12px",
              background: "#FEF2F2",
              border:
                "1px solid #FECACA",
              color: "#B91C1C",
              fontSize: "13px",
              fontWeight: 600,
            }}
          >
            {error}
          </div>
        )}

        {success && (
          <div
            style={{
              marginBottom: "18px",
              padding: "13px 16px",
              borderRadius: "12px",
              background: "#F0FDF4",
              border:
                "1px solid #BBF7D0",
              color: "#15803D",
              fontSize: "13px",
              fontWeight: 600,
            }}
          >
            {success}
          </div>
        )}

        {/* =====================================================
            MODEL LOADING ERROR
        ====================================================== */}

        {modelsError && (
          <div
            style={{
              marginBottom: "18px",
              padding: "13px 16px",
              borderRadius: "12px",
              background: "#FEF2F2",
              border:
                "1px solid #FECACA",
              color: "#B91C1C",
              fontSize: "13px",
              fontWeight: 600,
            }}
          >
            Unable to load prediction models:{" "}
            {modelsError}
          </div>
        )}

        {/* =====================================================
            ANALYSIS NEXT STEP
        ====================================================== */}

        {hasCreatedSignal &&
          isDraft && (
            <div
              style={{
                marginBottom: "18px",
                padding: "16px 18px",
                borderRadius: "14px",
                background: "#EAF6FC",
                border:
                  "1px solid #B9E2F5",
                color: "#168AC0",
                display: "flex",
                alignItems: "center",
                justifyContent:
                  "space-between",
                gap: "16px",
                flexWrap: "wrap",
              }}
            >
              <div>
                <div
                  style={{
                    fontSize: "14px",
                    fontWeight: 800,
                    marginBottom: "4px",
                  }}
                >
                  Signal created — analysis is the next step
                </div>

                <div
                  style={{
                    fontSize: "12px",
                    color: "#6B7785",
                  }}
                >
                  Signal {signalNumber} is currently a
                  draft. Analyze it to generate the predicted
                  safe and mine positions using{" "}
                  <strong>
                    {predictionEngineDisplay}
                  </strong>{" "}
                  with model{" "}
                  <strong>
                    {selectedModelVersion}
                  </strong>
                  .
                </div>
              </div>

              <button
                type="button"
                className="primary-action"
                onClick={
                  analyzeSignal
                }
                disabled={loading}
              >
                {loadingAction ===
                "analyze"
                  ? "Analyzing..."
                  : "Analyze Signal"}
              </button>
            </div>
          )}

        {/* =====================================================
            MAIN GRID
        ====================================================== */}

        <div className="create-signal-grid">

          {/* =================================================
              LEFT COLUMN
          ================================================== */}

          <div className="create-signal-main">

            {/* =================================================
                SIGNAL CONFIGURATION
            ================================================== */}

            <section className="create-card">

              <div className="create-card-header">

                <div>
                  <h2>
                    Signal Configuration
                  </h2>

                  <p>
                    Select the game configuration for this signal.
                  </p>
                </div>

                <div className="section-icon">
                  ⚙
                </div>

              </div>

              <div className="form-grid">

                {/* GAME */}

                <div className="form-group">

                  <label>
                    Game
                  </label>

                  <select
                    defaultValue="Mines Classic"
                    disabled={
                      hasCreatedSignal ||
                      loading
                    }
                  >
                    <option>
                      Mines Classic
                    </option>
                  </select>

                </div>

                {/* BOARD */}

                <div className="form-group">

                  <label>
                    Board Size
                  </label>

                  <select
                    defaultValue="5 × 5"
                    disabled={
                      hasCreatedSignal ||
                      loading
                    }
                  >
                    <option>
                      5 × 5
                    </option>
                  </select>

                </div>

                {/* MINES */}

                <div className="form-group">

                  <label>
                    Mine Count
                  </label>

                  <div className="segmented-control">

                    {[
                      "3",
                      "5",
                      "7",
                    ].map(
                      (value) => (
                        <button
                          key={value}
                          type="button"
                          className={
                            mineCount ===
                            value
                              ? "selected"
                              : ""
                          }
                          onClick={() =>
                            setMineCount(
                              value
                            )
                          }
                          disabled={
                            hasCreatedSignal ||
                            loading
                          }
                        >
                          {value}

                          <span>
                            {value ===
                            "1"
                              ? " Mine"
                              : " Mines"}
                          </span>
                        </button>
                      )
                    )}

                  </div>

                </div>

                {/* ATTEMPTS */}

                <div className="form-group">

                  <label>
                    Attempts
                  </label>

                  <select
                    value={attempts}
                    onChange={(e) =>
                      setAttempts(
                        e.target.value
                      )
                    }
                    disabled={
                      hasCreatedSignal ||
                      loading
                    }
                  >
                    <option value="1">
                      1 Attempt
                    </option>

                    <option value="2">
                      2 Attempts
                    </option>

                    <option value="3">
                      3 Attempts
                    </option>

                    <option value="4">
                      4 Attempts
                    </option>

                    <option value="5">
                      5 Attempts
                    </option>
                  </select>

                </div>

                {/* MODEL */}

                <div className="form-group full-width">

                  <label>
                    Model Version
                  </label>

                  <select
                    value={
                      selectedModelId
                    }
                    onChange={(e) =>
                      setSelectedModelId(
                        e.target.value
                      )
                    }
                    disabled={
                      hasCreatedSignal ||
                      loading ||
                      modelsLoading ||
                      models.length === 0
                    }
                  >
                    {modelsLoading ? (
                      <option value="">
                        Loading models...
                      </option>
                    ) : models.length === 0 ? (
                      <option value="">
                        No available models
                      </option>
                    ) : (
                      models.map(
                        (model) => (
                          <option
                            key={
                              model.id
                            }
                            value={
                              model.id
                            }
                          >
                            {model.version}
                            {" — "}
                            {model.name}
                            {model.status ===
                            "ACTIVE"
                              ? " — Active"
                              : ""}
                          </option>
                        )
                      )
                    )}
                  </select>

                </div>

                {/* =================================================
                    PREDICTION ENGINE
                    ================================================= */}

                <div className="form-group full-width">

                  <label>
                    Prediction Engine
                  </label>

                  <select
                    value={
                      predictionEngine
                    }
                    onChange={(e) =>
                      setPredictionEngine(
                        e.target
                          .value as PredictionEngine
                      )
                    }
                    disabled={
                      hasCreatedSignal ||
                      loading
                    }
                  >
                    <option value="PATTERN">
                      Pattern Engine — 2.0.0
                    </option>

                    <option value="ML">
                      ML Engine — Random Forest 1.0.0
                    </option>
                  </select>

                </div>

              </div>

            </section>

            {/* =================================================
                BOARD ANALYSIS
            ================================================== */}

            <section className="create-card">

              <div className="create-card-header">

                <div>
                  <h2>
                    Board Analysis
                  </h2>

                  <p>
                    {isAnalyzed
                      ? "Positions detected by the signal analysis engine."
                      : hasCreatedSignal
                        ? "Analyze the signal to detect the recommended positions."
                        : "Select the positions to include in this signal."}
                  </p>
                </div>

                <div className="board-selection-count">
                  {
                    selectedCells.length
                  }{" "}
                  safe
                </div>

              </div>

              <div className="board-analysis-layout">

                <div className="large-board">

                  {Array.from({
                    length: 25,
                  }).map(
                    (_, index) => {

                      const position =
                        index + 1;

                      const isSafe =
                        selectedCells.includes(
                          position
                        );

                      const isMine =
                        predictedMinePositions.includes(
                          position
                        );

                      return (
                        <button
                          key={
                            position
                          }
                          type="button"
                          className={getBoardCellClass(
                            position
                          )}
                          onClick={() =>
                            toggleCell(
                              position
                            )
                          }
                          disabled={
                            hasCreatedSignal ||
                            loading
                          }
                        >
                          {isMine ? (
                            <span>
                              💣
                            </span>
                          ) : isSafe ? (
                            <span>
                              ★
                            </span>
                          ) : (
                            <small>
                              {
                                position
                              }
                            </small>
                          )}
                        </button>
                      );
                    }
                  )}

                </div>

                <div className="board-side-info">

                  <div className="board-info-item">

                    <span>
                      Board
                    </span>

                    <strong>
                      5 × 5
                    </strong>

                  </div>

                  <div className="board-info-item">

                    <span>
                      Mines
                    </span>

                    <strong>
                      {mineCount}
                    </strong>

                  </div>

                  <div className="board-info-item">

                    <span>
                      Safe
                    </span>

                    <strong>
                      {
                        selectedCells.length
                      }
                    </strong>

                  </div>

                  <div className="board-info-item">

                    <span>
                      Attempts
                    </span>

                    <strong>
                      {attempts}
                    </strong>

                  </div>

                  {!hasCreatedSignal && (
                    <button
                      type="button"
                      className="clear-selection"
                      onClick={
                        clearSelection
                      }
                      disabled={
                        loading
                      }
                    >
                      Clear Selection
                    </button>
                  )}

                </div>

              </div>

              <div className="board-help">

                <span>
                  {isAnalyzed
                    ? "✓"
                    : "★"}
                </span>

                <p>
                  {isAnalyzed
                    ? `These positions were returned by the ${predictionEngineDisplay} using model ${selectedModelVersion}. The board is now read-only.`
                    : hasCreatedSignal
                      ? `Click Analyze Signal to generate positions using ${predictionEngineDisplay} with model ${selectedModelVersion}.`
                      : "Click any cell to mark it as a recommended position. These manual selections are only used before the signal is created."}
                </p>

              </div>

            </section>

            {/* =================================================
                ACTIONS
            ================================================== */}

            <div className="create-actions">

              {/* SAVE DRAFT */}

              <button
                type="button"
                className="secondary-action"
                onClick={
                  createSignal
                }
                disabled={
                  loading ||
                  hasCreatedSignal ||
                  modelsLoading ||
                  !selectedModelId
                }
              >
                {loadingAction ===
                "create"
                  ? "Saving..."
                  : "Save Draft"}
              </button>

              {/* ANALYZE */}

              <button
                type="button"
                className={
                  isDraft &&
                  hasCreatedSignal
                    ? "primary-action"
                    : "outline-action"
                }
                onClick={
                  analyzeSignal
                }
                disabled={
                  !signalId ||
                  loading ||
                  !isDraft
                }
              >
                {loadingAction ===
                "analyze"
                  ? "Analyzing..."
                  : isAnalyzed
                    ? "Analysis Complete"
                    : "Analyze Signal"}
              </button>

              {/* CREATE */}

              <button
                type="button"
                className="primary-action"
                onClick={
                  createSignal
                }
                disabled={
                  loading ||
                  hasCreatedSignal ||
                  modelsLoading ||
                  !selectedModelId
                }
              >
                {loadingAction ===
                "create"
                  ? "Creating..."
                  : hasCreatedSignal
                    ? "Signal Created"
                    : "Create Signal"}
              </button>

            </div>

          </div>

          {/* =================================================
              RIGHT COLUMN
          ================================================== */}

          <aside className="create-signal-sidebar">

            {/* =================================================
                INTELLIGENCE
            ================================================== */}

            <section className="create-card">

              <div className="create-card-header compact">

                <div>
                  <h2>
                    Signal Intelligence
                  </h2>

                  <p>
                    Current analysis information.
                  </p>
                </div>

                <div className="section-icon">
                  ✦
                </div>

              </div>

              <div className="intelligence-status">

                <div className="intelligence-icon">
                  ✦
                </div>

                <div>

                  <strong>
                    {analysisStarted
                      ? "Analysis complete"
                      : hasCreatedSignal
                        ? "Ready to analyze"
                        : "Ready for analysis"}
                  </strong>

                  <span>
                    {analysisStarted
                      ? `The ${predictionEngineDisplay} prediction using model ${selectedModelVersion} has been loaded onto the board.`
                      : hasCreatedSignal
                        ? `Signal created using ${predictionEngineDisplay} with model ${selectedModelVersion}. Analyze it to generate positions.`
                        : "No analysis has been run yet."}
                  </span>

                </div>

              </div>

              <div className="intelligence-list">

                <div>
                  <span>
                    Engine
                  </span>

                  <strong>
                    {predictionEngineName}
                  </strong>
                </div>

                <div>
                  <span>
                    Engine Version
                  </span>

                  <strong>
                    {predictionEngineVersion}
                  </strong>
                </div>

                <div>
                  <span>
                    Model
                  </span>

                  <strong>
                    {selectedModelVersion}
                  </strong>
                </div>

                <div>
                  <span>
                    Confidence
                  </span>

                  <strong
                    className={
                      confidence ===
                      null
                        ? "muted-value"
                        : ""
                    }
                  >
                    {confidence ===
                    null
                      ? "—"
                      : `${confidence}%`}
                  </strong>
                </div>

                <div>
                  <span>
                    Analysis
                  </span>

                  <strong
                    className={
                      analysisStarted
                        ? ""
                        : "muted-value"
                    }
                  >
                    {analysisStarted
                      ? "Completed"
                      : hasCreatedSignal
                        ? "Ready"
                        : "Not started"}
                  </strong>
                </div>

                <div>
                  <span>
                    Positions
                  </span>

                  <strong>
                    {
                      selectedCells.length
                    }
                  </strong>
                </div>

              </div>

            </section>

            {/* =================================================
                TELEGRAM PREVIEW
            ================================================== */}

            <section className="create-card telegram-preview-card">

              <div className="create-card-header compact">

                <div>
                  <h2>
                    Telegram Preview
                  </h2>

                  <p>
                    Preview of the signal message.
                  </p>
                </div>

                <div className="telegram-preview-icon">
                  ✈
                </div>

              </div>

              <div className="telegram-message">

                <div className="telegram-message-header">
                  👑 ENTRY CONFIRMED 👑
                </div>

                <div className="telegram-confidence-label">
                  👇 Model confidence 👇
                </div>

                <div className="confidence-preview">

                  <div className="confidence-block">

                    <span>🟩</span>
                    <span>🟩</span>
                    <span>🟩</span>
                    <span>🟩</span>
                    <span>🟩</span>
                    <span>🟩</span>
                    <span>🟩</span>
                    <span>🟩</span>
                    <span>🟩</span>
                    <span>⬜</span>

                  </div>

                  <strong>
                    {confidence ===
                    null
                      ? "—"
                      : `${confidence}%`}
                  </strong>

                </div>

                <div className="telegram-mini-board">

                  {Array.from({
                    length: 25,
                  }).map(
                    (_, index) => {

                      const position =
                        index + 1;

                      const selected =
                        selectedCells.includes(
                          position
                        );

                      const mine =
                        predictedMinePositions.includes(
                          position
                        );

                      return (
                        <div
                          key={
                            position
                          }
                          className={
                            mine
                              ? "telegram-cell selected"
                              : selected
                                ? "telegram-cell selected"
                                : "telegram-cell"
                          }
                        >
                          {mine
                            ? "💣"
                            : selected
                              ? "⭐"
                              : "🟦"}
                        </div>
                      );
                    }
                  )}

                </div>

                <div className="telegram-details">

                  <div>
                    💣:{" "}
                    <strong>
                      {mineCount} mines
                    </strong>
                  </div>

                  <div>
                    ♻️:{" "}
                    <strong>
                      {attempts} ATTEMPTS
                    </strong>
                  </div>

                </div>

                <div className="telegram-placeholder">
                  Play by clicking here 👉
                </div>

              </div>

              <div className="telegram-preview-note">
                Telegram publishing will be connected later.
              </div>

            </section>

            {/* =================================================
                SIGNAL INFORMATION
            ================================================== */}

            <section className="create-card">

              <div className="create-card-header compact">

                <div>
                  <h2>
                    Signal Information
                  </h2>

                  <p>
                    System generated details.
                  </p>
                </div>

              </div>

              <div className="signal-information">

                <div>

                  <span>
                    Signal Number
                  </span>

                  <strong>
                    {signalNumber ||
                      "Not created"}
                  </strong>

                </div>

                <div>

                  <span>
                    Status
                  </span>

                  <strong className="draft-text">
                    {signalStatus}
                  </strong>

                </div>

                <div>

                  <span>
                    Prediction Engine
                  </span>

                  <strong>
                    {predictionEngineName}
                  </strong>

                </div>

                <div>

                  <span>
                    Engine Version
                  </span>

                  <strong>
                    {predictionEngineVersion}
                  </strong>

                </div>

                <div>

                  <span>
                    Model
                  </span>

                  <strong>
                    {selectedModelVersion}
                  </strong>

                </div>

                <div>

                  <span>
                    Created By
                  </span>

                  <strong>
                    Administrator
                  </strong>

                </div>

              </div>

            </section>

          </aside>

        </div>

      </div>
    </AdminShell>
  );
} 
