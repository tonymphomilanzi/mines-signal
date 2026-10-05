"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import AdminShell from "@/components/layout/AdminShell";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

type ModelType =
  | "PRODUCTION"
  | "EXPERIMENTAL"
  | "DEVELOPMENT";

export default function CreateModelPage() {
  const router = useRouter();

  const [name, setName] = useState(
    "Mines Signal Engine"
  );

  const [version, setVersion] = useState("");

  const [modelType, setModelType] =
    useState<ModelType>("PRODUCTION");

  const [description, setDescription] =
    useState("");

  const [boardSize, setBoardSize] =
    useState("5");

  const [maximumAttempts, setMaximumAttempts] =
    useState("3");

  const [confidenceScore, setConfidenceScore] =
    useState("");

  const [submitting, setSubmitting] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const [success, setSuccess] =
    useState<string | null>(null);

  const handleSubmit = async (
    event: FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();

    if (submitting) {
      return;
    }

    setError(null);
    setSuccess(null);

    if (!name.trim()) {
      setError(
        "Please enter a model name."
      );
      return;
    }

    if (!version.trim()) {
      setError(
        "Please enter a model version."
      );
      return;
    }

    const parsedBoardSize =
      Number(boardSize);

    const parsedMaximumAttempts =
      Number(maximumAttempts);

    const parsedConfidence =
      confidenceScore.trim()
        ? Number(confidenceScore)
        : null;

    if (
      !Number.isInteger(parsedBoardSize) ||
      parsedBoardSize < 1 ||
      parsedBoardSize > 20
    ) {
      setError(
        "Board size must be between 1 and 20."
      );
      return;
    }

    if (
      !Number.isInteger(
        parsedMaximumAttempts
      ) ||
      parsedMaximumAttempts < 1
    ) {
      setError(
        "Maximum attempts must be at least 1."
      );
      return;
    }

    if (
      parsedConfidence !== null &&
      (Number.isNaN(parsedConfidence) ||
        parsedConfidence < 0 ||
        parsedConfidence > 100)
    ) {
      setError(
        "Confidence score must be between 0 and 100."
      );
      return;
    }

    setSubmitting(true);

    try {
      const response = await fetch(
        `${API_URL}/api/models`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            name: name.trim(),
            version: version.trim(),
            model_type: modelType,
            description:
              description.trim() || null,
            board_size: parsedBoardSize,
            maximum_attempts:
              parsedMaximumAttempts,
            confidence_score:
              parsedConfidence,
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
        const message =
          typeof data?.detail === "string"
            ? data.detail
            : "Unable to create the model.";

        throw new Error(message);
      }

      setSuccess(
        "Model registered successfully."
      );

      const createdModelId =
        data?.id;

      setTimeout(() => {
        if (createdModelId) {
          router.push(
            `/models/${createdModelId}`
          );
          return;
        }

        router.push("/models");
      }, 700);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Unable to create the model."
      );

      setSubmitting(false);
    }
  };

  return (
    <AdminShell>
      <div className="create-model-page">

        {/* =====================================================
            HEADER
        ===================================================== */}

        <div className="create-model-header">

          <div className="create-model-header-left">

            <button
              type="button"
              className="create-model-back-btn"
              onClick={() =>
                router.push("/models")
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

            <div className="create-model-breadcrumb">
              <span>Intelligence</span>
              <span>/</span>
              <span>Models</span>
              <span>/</span>
              <strong>Register Model</strong>
            </div>

            <div className="create-model-title-row">

              <div className="create-model-title-icon">
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
                <h1>Register Model</h1>

                <p>
                  Add a new signal model version
                  to the intelligence engine.
                </p>
              </div>

            </div>

          </div>

        </div>

        {/* =====================================================
            CONTENT
        ===================================================== */}

        <form
          className="create-model-layout"
          onSubmit={handleSubmit}
        >

          <div className="create-model-main">

            {/* MODEL INFORMATION */}

            <section className="create-model-card">

              <div className="create-model-card-header">

                <div>

                  <h2>
                    Model Information
                  </h2>

                  <p>
                    Basic information used to
                    identify this model version.
                  </p>

                </div>

                <div className="create-model-card-icon">
                  AI
                </div>

              </div>

              <div className="create-model-form-grid">

                <div className="create-model-field create-model-field-full">

                  <label htmlFor="model-name">
                    Model Name
                    <span>*</span>
                  </label>

                  <input
                    id="model-name"
                    type="text"
                    value={name}
                    onChange={(event) =>
                      setName(
                        event.target.value
                      )
                    }
                    placeholder="Mines Signal Engine"
                    maxLength={150}
                    disabled={submitting}
                  />

                  <small>
                    The display name of the
                    intelligence model.
                  </small>

                </div>

                <div className="create-model-field">

                  <label htmlFor="model-version">
                    Version
                    <span>*</span>
                  </label>

                  <input
                    id="model-version"
                    type="text"
                    value={version}
                    onChange={(event) =>
                      setVersion(
                        event.target.value
                      )
                    }
                    placeholder="v2.2.0"
                    maxLength={50}
                    disabled={submitting}
                  />

                  <small>
                    Must be unique across models.
                  </small>

                </div>

                <div className="create-model-field">

                  <label htmlFor="model-type">
                    Model Type
                    <span>*</span>
                  </label>

                  <select
                    id="model-type"
                    value={modelType}
                    onChange={(event) =>
                      setModelType(
                        event.target
                          .value as ModelType
                      )
                    }
                    disabled={submitting}
                  >
                    <option value="PRODUCTION">
                      Production
                    </option>

                    <option value="EXPERIMENTAL">
                      Experimental
                    </option>

                    <option value="DEVELOPMENT">
                      Development
                    </option>
                  </select>

                  <small>
                    Determines the model's
                    operating environment.
                  </small>

                </div>

                <div className="create-model-field create-model-field-full">

                  <label htmlFor="model-description">
                    Description
                  </label>

                  <textarea
                    id="model-description"
                    value={description}
                    onChange={(event) =>
                      setDescription(
                        event.target.value
                      )
                    }
                    placeholder="Describe the purpose and role of this model..."
                    rows={5}
                    maxLength={2000}
                    disabled={submitting}
                  />

                  <div className="create-model-character-count">
                    {description.length}/2000
                  </div>

                </div>

              </div>

            </section>

            {/* CONFIGURATION */}

            <section className="create-model-card">

              <div className="create-model-card-header">

                <div>

                  <h2>
                    Model Configuration
                  </h2>

                  <p>
                    Define the board and signal
                    generation parameters supported
                    by this model.
                  </p>

                </div>

                <div className="create-model-card-icon">
                  ⚙
                </div>

              </div>

              <div className="create-model-form-grid">

                <div className="create-model-field">

                  <label htmlFor="board-size">
                    Board Size
                    <span>*</span>
                  </label>

                  <div className="create-model-input-suffix">

                    <input
                      id="board-size"
                      type="number"
                      min="1"
                      max="20"
                      value={boardSize}
                      onChange={(event) =>
                        setBoardSize(
                          event.target.value
                        )
                      }
                      disabled={submitting}
                    />

                    <span>× board</span>

                  </div>

                  <small>
                    A value of 5 represents a
                    5 × 5 board.
                  </small>

                </div>

                <div className="create-model-field">

                  <label htmlFor="maximum-attempts">
                    Maximum Attempts
                    <span>*</span>
                  </label>

                  <input
                    id="maximum-attempts"
                    type="number"
                    min="1"
                    value={
                      maximumAttempts
                    }
                    onChange={(event) =>
                      setMaximumAttempts(
                        event.target.value
                      )
                    }
                    disabled={submitting}
                  />

                  <small>
                    Maximum attempts allowed
                    for generated signals.
                  </small>

                </div>

                <div className="create-model-field">

                  <label htmlFor="confidence-score">
                    Confidence Score
                  </label>

                  <div className="create-model-input-suffix">

                    <input
                      id="confidence-score"
                      type="number"
                      min="0"
                      max="100"
                      step="0.1"
                      value={
                        confidenceScore
                      }
                      onChange={(event) =>
                        setConfidenceScore(
                          event.target.value
                        )
                      }
                      placeholder="70"
                      disabled={submitting}
                    />

                    <span>%</span>

                  </div>

                  <small>
                    Optional initial confidence
                    score from 0 to 100.
                  </small>

                </div>

              </div>

            </section>

            {/* STATUS */}

            <section className="create-model-card">

              <div className="create-model-card-header">

                <div>

                  <h2>
                    Initial Status
                  </h2>

                  <p>
                    New models are registered as
                    ready and can be activated
                    later.
                  </p>

                </div>

              </div>

              <div className="create-model-status-preview">

                <div className="create-model-ready-icon">
                  ✓
                </div>

                <div>

                  <div className="create-model-ready-title">

                    <strong>
                      Ready
                    </strong>

                    <span>
                      READY
                    </span>

                  </div>

                  <p>
                    This model will be available
                    for activation after it has
                    been registered.
                  </p>

                </div>

              </div>

            </section>

            {/* ALERTS */}

            {error && (
              <div className="create-model-alert create-model-alert-error">

                <div className="create-model-alert-icon">
                  !
                </div>

                <div>
                  <strong>
                    Unable to register model
                  </strong>

                  <p>{error}</p>
                </div>

              </div>
            )}

            {success && (
              <div className="create-model-alert create-model-alert-success">

                <div className="create-model-alert-icon">
                  ✓
                </div>

                <div>
                  <strong>
                    Model registered
                  </strong>

                  <p>
                    Redirecting to the model
                    details...
                  </p>
                </div>

              </div>
            )}

            {/* ACTIONS */}

            <div className="create-model-actions">

              <button
                type="button"
                className="create-model-cancel-btn"
                onClick={() =>
                  router.push("/models")
                }
                disabled={submitting}
              >
                Cancel
              </button>

              <button
                type="submit"
                className="create-model-submit-btn"
                disabled={submitting}
              >
                {submitting ? (
                  <>
                    <span className="create-model-spinner" />
                    Registering Model...
                  </>
                ) : (
                  <>
                    <span>＋</span>
                    Register Model
                  </>
                )}
              </button>

            </div>

          </div>

          {/* =================================================
              SIDEBAR
          ================================================= */}

          <aside className="create-model-sidebar">

            <div className="create-model-sidebar-card">

              <div className="create-model-sidebar-title">

                <div className="create-model-sidebar-icon">
                  i
                </div>

                <h3>
                  Before registering
                </h3>

              </div>

              <div className="create-model-checklist">

                <div>
                  <span>1</span>
                  <p>
                    Choose a unique model
                    version.
                  </p>
                </div>

                <div>
                  <span>2</span>
                  <p>
                    Select the correct model
                    type.
                  </p>
                </div>

                <div>
                  <span>3</span>
                  <p>
                    Configure the supported
                    board size.
                  </p>
                </div>

                <div>
                  <span>4</span>
                  <p>
                    Review the maximum attempts
                    setting.
                  </p>
                </div>

                <div>
                  <span>5</span>
                  <p>
                    Register the model as
                    READY.
                  </p>
                </div>

              </div>

            </div>

            <div className="create-model-sidebar-card create-model-lifecycle-card">

              <div className="create-model-sidebar-title">

                <div className="create-model-sidebar-icon">
                  ↻
                </div>

                <h3>
                  Model lifecycle
                </h3>

              </div>

              <div className="create-model-lifecycle">

                <div className="create-model-lifecycle-item active">
                  <span />
                  <div>
                    <strong>
                      READY
                    </strong>
                    <small>
                      Registered and available
                      for activation
                    </small>
                  </div>
                </div>

                <div className="create-model-lifecycle-line" />

                <div className="create-model-lifecycle-item">
                  <span />
                  <div>
                    <strong>
                      ACTIVE
                    </strong>
                    <small>
                      Used for production
                      signal generation
                    </small>
                  </div>
                </div>

                <div className="create-model-lifecycle-line" />

                <div className="create-model-lifecycle-item">
                  <span />
                  <div>
                    <strong>
                      ARCHIVED
                    </strong>
                    <small>
                      Retained for historical
                      analysis
                    </small>
                  </div>
                </div>

              </div>

            </div>

            <div className="create-model-sidebar-card create-model-note-card">

              <div className="create-model-note-icon">
                ⚠
              </div>

              <strong>
                Important
              </strong>

              <p>
                Registering a model does not
                activate it. The model must be
                explicitly activated before it
                can become the active production
                model.
              </p>

            </div>

          </aside>

        </form>

      </div>
    </AdminShell>
  );
}