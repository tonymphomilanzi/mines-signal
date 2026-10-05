"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  useParams,
  useRouter,
} from "next/navigation";

import AdminShell from "@/components/layout/AdminShell";

import "./record-result.css";

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

export default function RecordResultPage() {
  const router = useRouter();
  const params = useParams();

  const signalId = Array.isArray(params?.id)
    ? params.id[0]
    : params?.id;

  const [signal, setSignal] =
    useState<SignalDetail | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [submitting, setSubmitting] =
    useState(false);

  const [selectedMines, setSelectedMines] =
    useState<Set<number>>(new Set());

  const [error, setError] =
    useState("");

  const [submitError, setSubmitError] =
    useState("");

  const loadSignal = useCallback(
    async () => {
      if (!signalId) {
        setError("Signal ID is missing.");
        setLoading(false);
        return;
      }

      setLoading(true);
      setError("");

      try {
        const response = await fetch(
          `${API_URL}/api/signals/${signalId}`,
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
              "Unable to load signal details."
          );
          return;
        }

        setSignal(data as SignalDetail);
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

  const latestPrediction = useMemo(() => {
    if (
      !signal ||
      !signal.predictions ||
      signal.predictions.length === 0
    ) {
      return null;
    }

    return [...signal.predictions].sort(
      (a, b) =>
        new Date(b.created_at).getTime() -
        new Date(a.created_at).getTime()
    )[0];
  }, [signal]);

  const totalPositions =
    signal
      ? signal.board_size * signal.board_size
      : 0;

  const safeCount =
    totalPositions - selectedMines.size;

  const requiredMines =
    signal?.mine_count ?? 0;

  const minesRemaining = Math.max(
    requiredMines - selectedMines.size,
    0
  );

  const boardPositions = useMemo(() => {
    return Array.from(
      { length: totalPositions },
      (_, index) => index + 1
    );
  }, [totalPositions]);

  const canRecord =
    Boolean(signal) &&
    !signal?.result &&
    (signal?.status === "CONFIRMED" ||
      signal?.status === "RESULT_PENDING") &&
    selectedMines.size === requiredMines;

  const toggleMine = (position: number) => {
    if (
      submitting ||
      !signal ||
      signal.result ||
      !(
        signal.status === "CONFIRMED" ||
        signal.status === "RESULT_PENDING"
      )
    ) {
      return;
    }

    setSubmitError("");

    setSelectedMines((current) => {
      const next = new Set(current);

      if (next.has(position)) {
        next.delete(position);
        return next;
      }

      if (next.size >= requiredMines) {
        return next;
      }

      next.add(position);

      return next;
    });
  };

  const clearSelection = () => {
    if (submitting) {
      return;
    }

    setSelectedMines(new Set());
    setSubmitError("");
  };

  const recordResult = async () => {
    if (!signalId || !signal) {
      return;
    }

    if (
      signal.result
    ) {
      setSubmitError(
        "A result has already been recorded for this signal."
      );
      return;
    }

    if (
      signal.status !== "CONFIRMED" &&
      signal.status !== "RESULT_PENDING"
    ) {
      setSubmitError(
        "This signal is not ready for result recording."
      );
      return;
    }

    if (
      selectedMines.size !==
      requiredMines
    ) {
      setSubmitError(
        `Select exactly ${requiredMines} mine ${
          requiredMines === 1
            ? "position"
            : "positions"
        } before recording the result.`
      );
      return;
    }

    setSubmitting(true);
    setSubmitError("");

    const actualMinePositions = Array.from(
      selectedMines
    ).sort((a, b) => a - b);

    const actualSafePositions =
      boardPositions.filter(
        (position) =>
          !selectedMines.has(position)
      );

    try {
      const response = await fetch(
        `${API_URL}/api/signals/${signalId}/result`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            actual_mine_positions:
              actualMinePositions,
            actual_safe_positions:
              actualSafePositions,
          }),
        }
      );

      let data: any = null;

      try {
        data = await response.json();
      } catch {
        data = null;
      }

      if (!response.ok) {
        setSubmitError(
          data?.detail ||
            "Unable to record the signal result."
        );
        return;
      }

      const resultId =
        data?.result?.id;

      if (resultId) {
        router.push(
          `/results/${resultId}`
        );
        return;
      }

      router.push("/results");
    } catch (requestError) {
      console.error(
        "Failed to record result:",
        requestError
      );

      setSubmitError(
        "Unable to connect to the signal server."
      );
    } finally {
      setSubmitting(false);
    }
  };

  const formatDate = (
    value: string | null | undefined
  ) => {
    if (!value) {
      return "—";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return "—";
    }

    return date.toLocaleString(
      "en-US",
      {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "numeric",
        minute: "2-digit",
      }
    );
  };

  if (loading) {
    return (
      <AdminShell>
        <div className="record-result-page">
          <div className="record-result-loading">
            <div className="record-result-spinner" />

            <h3>
              Loading signal...
            </h3>

            <p>
              Preparing the result recording board.
            </p>
          </div>
        </div>
      </AdminShell>
    );
  }

  if (error || !signal) {
    return (
      <AdminShell>
        <div className="record-result-page">
          <div className="record-result-error-card">
            <div className="record-result-error-icon">
              <span>!</span>
            </div>

            <h2>
              Unable to Load Signal
            </h2>

            <p>
              {error ||
                "The requested signal could not be found."}
            </p>

            <div className="record-result-error-actions">
              <button
                type="button"
                className="record-result-secondary-button"
                onClick={() =>
                  router.push("/results")
                }
              >
                Back to Results
              </button>

              <button
                type="button"
                className="record-result-primary-button"
                onClick={loadSignal}
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      </AdminShell>
    );
  }

  const hasExistingResult =
    Boolean(signal.result);

  const invalidStatus =
    signal.status !== "CONFIRMED" &&
    signal.status !== "RESULT_PENDING";

  if (hasExistingResult) {
    return (
      <AdminShell>
        <div className="record-result-page">
          <div className="record-result-header">
            <div>
              <button
                type="button"
                className="record-result-back-button"
                onClick={() =>
                  router.push(
                    `/signals/${signal.id}`
                  )
                }
              >
                <span>←</span>
                Back to Signal
              </button>

              <div className="record-result-breadcrumb">
                Results
                <span>/</span>
                Record Result
              </div>
            </div>
          </div>

          <div className="record-result-already-card">
            <div className="record-result-success-icon">
              ✓
            </div>

            <h2>
              Result Already Recorded
            </h2>

            <p>
              A result has already been recorded
              for signal{" "}
              <strong>
                {signal.signal_number}
              </strong>.
            </p>

            <div className="record-result-already-actions">
              <button
                type="button"
                className="record-result-secondary-button"
                onClick={() =>
                  router.push(
                    `/signals/${signal.id}`
                  )
                }
              >
                View Signal
              </button>

              <button
                type="button"
                className="record-result-primary-button"
                onClick={() =>
                  router.push(
                    `/results/${signal.result?.id}`
                  )
                }
              >
                View Result
              </button>
            </div>
          </div>
        </div>
      </AdminShell>
    );
  }

  return (
    <AdminShell>
      <div className="record-result-page">
        {/* -------------------------------------------------- */}
        {/* HEADER */}
        {/* -------------------------------------------------- */}

        <div className="record-result-header">
          <div>
            <button
              type="button"
              className="record-result-back-button"
              onClick={() =>
                router.push(
                  `/signals/${signal.id}`
                )
              }
            >
              <span>←</span>
              Back to Signal
            </button>

            <div className="record-result-breadcrumb">
              Results
              <span>/</span>
              Record Result
            </div>

            <div className="record-result-title-row">
              <div>
                <h1>
                  Record Signal Result
                </h1>

                <p>
                  Record the actual mine positions
                  from the completed game.
                </p>
              </div>

              <div className="record-result-signal-badge">
                <span className="record-result-signal-dot" />
                {signal.signal_number}
              </div>
            </div>
          </div>
        </div>

        {/* -------------------------------------------------- */}
        {/* WARNING */}
        {/* -------------------------------------------------- */}

        <div className="record-result-warning">
          <div className="record-result-warning-icon">
            !
          </div>

          <div>
            <strong>
              Record the actual game outcome
            </strong>

            <p>
              Select only the cells that contained
              mines in the completed game. Safe
              positions will be calculated automatically.
              This does not modify the original prediction.
            </p>
          </div>
        </div>

        {/* -------------------------------------------------- */}
        {/* INVALID STATUS */}
        {/* -------------------------------------------------- */}

        {invalidStatus && (
          <div className="record-result-status-error">
            <div className="record-result-status-error-icon">
              !
            </div>

            <div>
              <strong>
                Result recording is unavailable
              </strong>

              <p>
                This signal must be confirmed before
                its actual result can be recorded.
                Current status:{" "}
                <strong>
                  {signal.status}
                </strong>
              </p>
            </div>
          </div>
        )}

        {/* -------------------------------------------------- */}
        {/* SIGNAL SUMMARY */}
        {/* -------------------------------------------------- */}

        <div className="record-result-summary-grid">
          <div className="record-result-summary-card">
            <div className="record-result-summary-icon blue">
              #
            </div>

            <div>
              <span>
                Signal
              </span>

              <strong>
                {signal.signal_number}
              </strong>
            </div>
          </div>

          <div className="record-result-summary-card">
            <div className="record-result-summary-icon blue">
              ▦
            </div>

            <div>
              <span>
                Board
              </span>

              <strong>
                {signal.board_size} ×{" "}
                {signal.board_size}
              </strong>
            </div>
          </div>

          <div className="record-result-summary-card">
            <div className="record-result-summary-icon red">
              ×
            </div>

            <div>
              <span>
                Required Mines
              </span>

              <strong>
                {requiredMines}
              </strong>
            </div>
          </div>

          <div className="record-result-summary-card">
            <div className="record-result-summary-icon green">
              ✓
            </div>

            <div>
              <span>
                Safe Cells
              </span>

              <strong>
                {safeCount}
              </strong>
            </div>
          </div>
        </div>

        {/* -------------------------------------------------- */}
        {/* MAIN CONTENT */}
        {/* -------------------------------------------------- */}

        <div className="record-result-layout">
          {/* BOARD CARD */}

          <section className="record-result-board-card">
            <div className="record-result-card-header">
              <div>
                <h2>
                  Actual Game Board
                </h2>

                <p>
                  Click cells to mark where mines
                  actually appeared.
                </p>
              </div>

              <div className="record-result-board-size">
                {signal.board_size} ×{" "}
                {signal.board_size}
              </div>
            </div>

            {/* BOARD */}

            <div
              className="record-result-board"
              style={{
                gridTemplateColumns: `repeat(${signal.board_size}, minmax(0, 1fr))`,
              }}
            >
              {boardPositions.map(
                (position) => {
                  const isMine =
                    selectedMines.has(
                      position
                    );

                  const disabled =
                    submitting ||
                    invalidStatus;

                  return (
                    <button
                      key={position}
                      type="button"
                      disabled={disabled}
                      className={`record-result-cell ${
                        isMine
                          ? "is-mine"
                          : "is-safe"
                      } ${
                        disabled
                          ? "is-disabled"
                          : ""
                      }`}
                      onClick={() =>
                        toggleMine(
                          position
                        )
                      }
                      aria-label={
                        isMine
                          ? `Position ${position}, mine selected`
                          : `Position ${position}, safe`
                      }
                    >
                      {isMine ? (
                        <>
                          <span className="record-result-mine-icon">
                            ×
                          </span>

                          <span className="record-result-cell-number">
                            {position}
                          </span>
                        </>
                      ) : (
                        <span className="record-result-cell-number">
                          {position}
                        </span>
                      )}
                    </button>
                  );
                }
              )}
            </div>

            {/* LEGEND */}

            <div className="record-result-legend">
              <div className="record-result-legend-item">
                <span className="record-result-legend-box safe">
                  ✓
                </span>

                <span>
                  Safe
                </span>
              </div>

              <div className="record-result-legend-item">
                <span className="record-result-legend-box mine">
                  ×
                </span>

                <span>
                  Actual Mine
                </span>
              </div>

              <div className="record-result-legend-item">
                <span className="record-result-legend-box unselected">
                  #
                </span>

                <span>
                  Unselected
                </span>
              </div>
            </div>
          </section>

          {/* SIDE PANEL */}

          <aside className="record-result-side">
            {/* SELECTION CARD */}

            <section className="record-result-selection-card">
              <div className="record-result-card-header compact">
                <div>
                  <h2>
                    Mine Selection
                  </h2>

                  <p>
                    Select the actual mine cells.
                  </p>
                </div>
              </div>

              <div className="record-result-counter">
                <div className="record-result-counter-main">
                  <strong>
                    {selectedMines.size}
                  </strong>

                  <span>
                    / {requiredMines}
                  </span>
                </div>

                <div className="record-result-counter-label">
                  Mines selected
                </div>
              </div>

              <div className="record-result-progress">
                <div
                  className="record-result-progress-bar"
                  style={{
                    width: `${Math.min(
                      (selectedMines.size /
                        Math.max(
                          requiredMines,
                          1
                        )) *
                        100,
                      100
                    )}%`,
                  }}
                />
              </div>

              {minesRemaining > 0 ? (
                <div className="record-result-selection-message">
                  <span>i</span>

                  <p>
                    Select{" "}
                    <strong>
                      {minesRemaining}
                    </strong>{" "}
                    more{" "}
                    {minesRemaining === 1
                      ? "mine"
                      : "mines"}.
                  </p>
                </div>
              ) : (
                <div className="record-result-selection-success">
                  <span>✓</span>

                  <p>
                    All required mines have
                    been selected.
                  </p>
                </div>
              )}

              <button
                type="button"
                className="record-result-clear-button"
                disabled={
                  submitting ||
                  selectedMines.size === 0
                }
                onClick={clearSelection}
              >
                Clear Selection
              </button>
            </section>

            {/* PREDICTION CARD */}

            <section className="record-result-prediction-card">
              <div className="record-result-card-header compact">
                <div>
                  <h2>
                    Original Prediction
                  </h2>

                  <p>
                    Reference only
                  </p>
                </div>

                <span className="record-result-reference-badge">
                  Reference
                </span>
              </div>

              <div className="record-result-prediction-row">
                <span>
                  Predicted safe
                </span>

                <strong>
                  {latestPrediction
                    ?.safe_positions
                    ?.length ?? 0}
                </strong>
              </div>

              <div className="record-result-prediction-row">
                <span>
                  Predicted mines
                </span>

                <strong>
                  {latestPrediction
                    ?.predicted_mine_positions
                    ?.length ?? 0}
                </strong>
              </div>

              <div className="record-result-prediction-row">
                <span>
                  Confidence
                </span>

                <strong>
                  {latestPrediction?.confidence !=
                  null
                    ? `${latestPrediction.confidence.toFixed(
                        1
                      )}%`
                    : "—"}
                </strong>
              </div>

              <div className="record-result-prediction-divider" />

              <p className="record-result-prediction-note">
                The original prediction is shown
                for comparison. Your selection above
                must represent the actual game outcome.
              </p>
            </section>

            {/* SIGNAL INFO */}

            <section className="record-result-info-card">
              <div className="record-result-card-header compact">
                <div>
                  <h2>
                    Signal Information
                  </h2>
                </div>
              </div>

              <div className="record-result-info-row">
                <span>
                  Game
                </span>

                <strong>
                  {signal.game}
                </strong>
              </div>

              <div className="record-result-info-row">
                <span>
                  Attempts
                </span>

                <strong>
                  {signal.attempts}
                </strong>
              </div>

              <div className="record-result-info-row">
                <span>
                  Status
                </span>

                <span className="record-result-status-badge">
                  {signal.status}
                </span>
              </div>

              <div className="record-result-info-row">
                <span>
                  Confirmed
                </span>

                <strong>
                  {formatDate(
                    signal.confirmed_at
                  )}
                </strong>
              </div>
            </section>
          </aside>
        </div>

        {/* -------------------------------------------------- */}
        {/* ERROR */}
        {/* -------------------------------------------------- */}

        {submitError && (
          <div className="record-result-submit-error">
            <div className="record-result-submit-error-icon">
              !
            </div>

            <div>
              <strong>
                Unable to record result
              </strong>

              <p>
                {submitError}
              </p>
            </div>
          </div>
        )}

        {/* -------------------------------------------------- */}
        {/* ACTION BAR */}
        {/* -------------------------------------------------- */}

        <div className="record-result-action-bar">
          <div className="record-result-action-info">
            <div className="record-result-action-icon">
              ✓
            </div>

            <div>
              <strong>
                Ready to record?
              </strong>

              <p>
                {selectedMines.size ===
                requiredMines
                  ? `All ${requiredMines} mine positions are selected.`
                  : `Select ${requiredMines} mine ${
                      requiredMines === 1
                        ? "position"
                        : "positions"
                    } to continue.`}
              </p>
            </div>
          </div>

          <div className="record-result-action-buttons">
            <button
              type="button"
              className="record-result-cancel-button"
              disabled={submitting}
              onClick={() =>
                router.push(
                  `/signals/${signal.id}`
                )
              }
            >
              Cancel
            </button>

            <button
              type="button"
              className="record-result-submit-button"
              disabled={
                !canRecord ||
                submitting
              }
              onClick={recordResult}
            >
              {submitting ? (
                <>
                  <span className="record-result-button-spinner" />
                  Recording...
                </>
              ) : (
                <>
                  <span>✓</span>
                  Record Result
                </>
              )}
            </button>
          </div>
        </div>

        {/* -------------------------------------------------- */}
        {/* FOOTNOTE */}
        {/* -------------------------------------------------- */}

        <div className="record-result-footnote">
          <span>i</span>

          <p>
            Once recorded, the result will be
            evaluated against the signal prediction
            and cannot be submitted again for the same
            signal.
          </p>
        </div>
      </div>
    </AdminShell>
  );
}