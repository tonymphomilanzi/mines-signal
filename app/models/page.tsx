"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import AdminShell from "@/components/layout/AdminShell";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

type ModelStatus = "ACTIVE" | "READY" | "ARCHIVED";

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
  signals: number | null;
  createdAt: string;
  updatedAt: string;
};

type ActivityItem = {
  id: string;
  version: string;
  event: string;
  description: string;
  date: string;
  type: "active" | "evaluation" | "archive" | "configuration";
};

function formatDate(value: string | null) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatDateTime(value: string | null) {
  if (!value) {
    return "—";
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

function formatModelType(type: string) {
  switch (type) {
    case "PRODUCTION":
      return "Production";

    case "EXPERIMENTAL":
      return "Experimental";

    case "DEVELOPMENT":
      return "Development";

    default:
      return type;
  }
}

function formatAccuracy(value: number | null) {
  if (value === null || value === undefined) {
    return null;
  }

  return Number(value).toFixed(1);
}

function mapBackendModel(model: BackendModel): Model {
  return {
    id: model.id,
    version: model.version,
    name: model.name,
    type: formatModelType(model.model_type),
    status: model.status,
    accuracy: model.observed_accuracy,
    confidence: model.confidence_score,
    // The current ModelResponse does not expose signal counts.
    signals: null,
    createdAt: formatDate(model.created_at),
    updatedAt: formatDate(model.updated_at),
  };
}

export default function ModelsPage() {
  const router = useRouter();

  const [models, setModels] = useState<Model[]>([]);
  const [statusFilter, setStatusFilter] = useState("All");
  const [search, setSearch] = useState("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadModels = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `${API_URL}/api/models`,
        {
          method: "GET",
          credentials: "include",
          cache: "no-store",
        }
      );

      if (!response.ok) {
        const body = await response.text();

        throw new Error(
          body ||
            `Unable to load models (${response.status}).`
        );
      }

      const data = await response.json();

      const backendModels: BackendModel[] =
        Array.isArray(data)
          ? data
          : data.items ?? [];

      setModels(
        backendModels.map(mapBackendModel)
      );
    } catch (err) {
      console.error(
        "Failed to load models:",
        err
      );

      setError(
        err instanceof Error
          ? err.message
          : "Unable to load models."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadModels();
  }, []);

  const activeModel = useMemo(
    () =>
      models.find(
        (model) => model.status === "ACTIVE"
      ) ?? null,
    [models]
  );

  const filteredModels = useMemo(() => {
    return models.filter((model) => {
      const searchValue =
        search.toLowerCase();

      const matchesSearch =
        model.version
          .toLowerCase()
          .includes(searchValue) ||
        model.name
          .toLowerCase()
          .includes(searchValue);

      const matchesStatus =
        statusFilter === "All" ||
        model.status === statusFilter;

      return (
        matchesSearch &&
        matchesStatus
      );
    });
  }, [models, search, statusFilter]);

  const availableVersions = models.length;

  const activeAccuracy =
    activeModel?.accuracy ?? null;

  const activeBoardSize =
    activeModel
      ? `${activeModel.id ? "" : ""}`
      : "—";

  const activity: ActivityItem[] = useMemo(() => {
    return [...models]
      .sort(
        (a, b) =>
          new Date(b.updatedAt).getTime() -
          new Date(a.updatedAt).getTime()
      )
      .slice(0, 4)
      .map((model, index) => {
        let event:
          | ActivityItem["event"]
          | string;

        let description: string;

        let type: ActivityItem["type"];

        if (model.status === "ACTIVE") {
          event = "Model active";
          description =
            `${model.version} is currently active for signal generation.`;
          type = "active";
        } else if (
          model.status === "ARCHIVED"
        ) {
          event = "Model archived";
          description =
            `${model.version} is retained as an archived model version.`;
          type = "archive";
        } else {
          event = "Model ready";
          description =
            `${model.version} is ready for activation.`;
          type = "evaluation";
        }

        return {
          id: model.id,
          version: model.version,
          event,
          description,
          date: model.updatedAt,
          type,
        };
      });
  }, [models]);

  const openModel = (id: string) => {
    router.push(`/models/${id}`);
  };

  return (
    <AdminShell>
      <div className="models-page">

        {/* HEADER */}
        <div className="models-page-header">

          <div>
            <div className="models-breadcrumb">
              Intelligence / Models
            </div>

            <h1>Models</h1>

            <p>
              Manage signal models, versions, configurations,
              and model deployment status.
            </p>
          </div>

          <button
            className="models-primary-button"
            onClick={() =>
              router.push("/models/create")
            }
          >
            <span>＋</span>
            Register Model
          </button>

        </div>

        {/* ERROR */}
        {error && (
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
              justifyContent: "space-between",
              gap: 16,
            }}
          >
            <span>{error}</span>

            <button
              className="models-outline-button"
              onClick={loadModels}
            >
              Retry
            </button>
          </div>
        )}

        {/* MODEL OVERVIEW */}
        <div className="models-stats-grid">

          <ModelStat
            label="Active Model"
            value={
              activeModel?.version ?? "None"
            }
            description="Currently in production"
            icon="◎"
            type="blue"
          />

          <ModelStat
            label="Model Status"
            value={
              activeModel
                ? "Operational"
                : "No Active Model"
            }
            description={
              activeModel
                ? "Ready for signal generation"
                : "Activate a ready model"
            }
            icon="✓"
            type="green"
          />

          <ModelStat
            label="Observed Accuracy"
            value={
              activeAccuracy !== null
                ? `${formatAccuracy(
                    activeAccuracy
                  )}%`
                : "—"
            }
            description="Based on evaluated signals"
            icon="◈"
            type="purple"
          />

          <ModelStat
            label="Available Versions"
            value={String(
              availableVersions
            )}
            description="Across all environments"
            icon="◉"
            type="orange"
          />

        </div>

        {/* ACTIVE MODEL */}
        <div className="models-active-card">

          <div className="models-active-left">

            <div className="models-active-icon">
              AI
            </div>

            <div>

              <div className="models-active-title-row">

                <h2>
                  {activeModel?.name ??
                    "No Active Model"}
                </h2>

                <span className="models-active-badge">
                  <span />
                  {activeModel
                    ? "Active"
                    : "Not Active"}
                </span>

              </div>

              <p>
                {activeModel
                  ? "Production signal generation model"
                  : "There is currently no active production model."}
              </p>

              {activeModel && (
                <div className="models-active-meta">

                  <span>
                    <strong>Version:</strong>{" "}
                    {activeModel.version}
                  </span>

                  <span>
                    <strong>Environment:</strong>{" "}
                    Production
                  </span>

                  <span>
                    <strong>Updated:</strong>{" "}
                    {activeModel.updatedAt}
                  </span>

                </div>
              )}

            </div>

          </div>

          {activeModel && (
            <div className="models-active-actions">

              <button
                className="models-outline-button"
                onClick={() =>
                  openModel(
                    activeModel.id
                  )
                }
              >
                View Details
              </button>

              <button
                className="models-primary-small-button"
                onClick={() =>
                  openModel(
                    activeModel.id
                  )
                }
              >
                Configure
              </button>

            </div>
          )}

        </div>

        {/* MODEL CONFIGURATION */}
        <div className="models-configuration-grid">

          <div className="models-card">

            <div className="models-card-header">

              <div>
                <h2>
                  Active Model Configuration
                </h2>

                <p>
                  Current parameters used by the signal engine.
                </p>
              </div>

              <div className="models-card-icon">
                ⚙
              </div>

            </div>

            <div className="models-config-list">

              <ModelConfig
                label="Board Size"
                value={
                  activeModel
                    ? "Configured in model details"
                    : "—"
                }
              />

              <ModelConfig
                label="Supported Mines"
                value={
                  activeModel
                    ? "Configured in model"
                    : "—"
                }
              />

              <ModelConfig
                label="Maximum Attempts"
                value={
                  activeModel
                    ? "Configured in model"
                    : "—"
                }
              />

              <ModelConfig
                label="Model Confidence"
                value={
                  activeModel?.confidence !==
                    null &&
                  activeModel?.confidence !==
                    undefined
                    ? "Enabled"
                    : "Not configured"
                }
              />

              <ModelConfig
                label="Signal Status"
                value={
                  activeModel
                    ? "Active"
                    : "—"
                }
              />

              <ModelConfig
                label="Prediction Output"
                value={
                  activeModel
                    ? "Safe Positions"
                    : "—"
                }
              />

            </div>

          </div>

          <div className="models-card">

            <div className="models-card-header">

              <div>
                <h2>Model Usage</h2>

                <p>
                  Current production model activity.
                </p>
              </div>

              <div className="models-card-icon">
                ◉
              </div>

            </div>

            <div className="models-usage-body">

              <div className="models-usage-number">
                —
              </div>

              <span className="models-usage-label">
                Evaluated signals
              </span>

              <div className="models-usage-progress">
                <span style={{ width: "0%" }} />
              </div>

              <div className="models-usage-row">
                <span>Signals generated</span>
                <strong>—</strong>
              </div>

              <div className="models-usage-row">
                <span>Signals evaluated</span>
                <strong>—</strong>
              </div>

              <div className="models-usage-row">
                <span>Pending evaluation</span>
                <strong>—</strong>
              </div>

              <div className="models-usage-row">
                <span>Model version</span>
                <strong>
                  {activeModel?.version ??
                    "—"}
                </strong>
              </div>

            </div>

          </div>

        </div>

        {/* AVAILABLE MODELS */}
        <div className="models-card models-list-card">

          <div className="models-card-header models-list-header">

            <div>
              <h2>Available Models</h2>

              <p>
                Registered model versions and their current
                deployment status.
              </p>
            </div>

            <span className="models-version-count">
              {models.length} versions
            </span>

          </div>

          {/* FILTERS */}
          <div className="models-filters">

            <div className="models-search">

              <span>⌕</span>

              <input
                type="text"
                placeholder="Search model or version..."
                value={search}
                onChange={(e) =>
                  setSearch(
                    e.target.value
                  )
                }
              />

            </div>

            <select
              className="models-filter-select"
              value={statusFilter}
              onChange={(e) =>
                setStatusFilter(
                  e.target.value
                )
              }
            >
              <option value="All">
                All Status
              </option>

              <option value="ACTIVE">
                Active
              </option>

              <option value="READY">
                Ready
              </option>

              <option value="ARCHIVED">
                Archived
              </option>
            </select>

            <button
              className="models-reset-button"
              onClick={() => {
                setSearch("");
                setStatusFilter("All");
              }}
            >
              Reset
            </button>

          </div>

          {/* LOADING */}
          {loading && (
            <div
              className="models-empty"
              style={{
                minHeight: 180,
              }}
            >
              <div>◌</div>

              <strong>
                Loading models
              </strong>

              <span>
                Retrieving registered model versions...
              </span>
            </div>
          )}

          {/* DESKTOP TABLE */}
          {!loading && (
            <div className="models-table-wrapper">

              <table className="models-table">

                <thead>
                  <tr>
                    <th>Model</th>
                    <th>Version</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Accuracy</th>
                    <th>Signals</th>
                    <th>Updated</th>
                    <th></th>
                  </tr>
                </thead>

                <tbody>

                  {filteredModels.map(
                    (model) => (
                      <tr key={model.id}>

                        <td>
                          <div className="models-table-name">

                            <div className="models-mini-icon">
                              AI
                            </div>

                            <div>
                              <strong>
                                {model.name}
                              </strong>

                              <span>
                                Created{" "}
                                {model.createdAt}
                              </span>
                            </div>

                          </div>
                        </td>

                        <td>
                          <span className="models-version">
                            {model.version}
                          </span>
                        </td>

                        <td>
                          <span className="models-type">
                            {model.type}
                          </span>
                        </td>

                        <td>
                          <ModelStatusBadge
                            status={model.status}
                          />
                        </td>

                        <td>

                          {model.accuracy !==
                          null ? (
                            <div className="models-table-accuracy">

                              <div>
                                <span
                                  style={{
                                    width: `${Math.min(
                                      Math.max(
                                        model.accuracy,
                                        0
                                      ),
                                      100
                                    )}%`,
                                  }}
                                />
                              </div>

                              <strong>
                                {formatAccuracy(
                                  model.accuracy
                                )}
                                %
                              </strong>

                            </div>
                          ) : (
                            <span className="models-not-available">
                              —
                            </span>
                          )}

                        </td>

                        <td>
                          <span className="models-signals">
                            {model.signals ??
                              "—"}
                          </span>
                        </td>

                        <td>
                          <span className="models-date">
                            {model.updatedAt}
                          </span>
                        </td>

                        <td>

                          <button
                            className="models-more-button"
                            onClick={() =>
                              openModel(
                                model.id
                              )
                            }
                            aria-label={`View ${model.version}`}
                          >
                            ⋮
                          </button>

                        </td>

                      </tr>
                    )
                  )}

                </tbody>

              </table>

              {filteredModels.length ===
                0 && (
                <div className="models-empty">

                  <div>⌕</div>

                  <strong>
                    No models found
                  </strong>

                  <span>
                    Try changing your search or status filter.
                  </span>

                </div>
              )}

            </div>
          )}

          {/* MOBILE */}
          {!loading && (
            <div className="models-mobile-list">

              {filteredModels.map(
                (model) => (
                  <div
                    className="models-mobile-item"
                    key={model.id}
                  >

                    <div className="models-mobile-top">

                      <div className="models-mobile-name">

                        <div className="models-mini-icon">
                          AI
                        </div>

                        <div>
                          <strong>
                            {model.version}
                          </strong>

                          <span>
                            {model.name}
                          </span>
                        </div>

                      </div>

                      <ModelStatusBadge
                        status={model.status}
                      />

                    </div>

                    <div className="models-mobile-grid">

                      <div>
                        <span>Type</span>
                        <strong>
                          {model.type}
                        </strong>
                      </div>

                      <div>
                        <span>Accuracy</span>
                        <strong>
                          {model.accuracy !==
                          null
                            ? `${formatAccuracy(
                                model.accuracy
                              )}%`
                            : "—"}
                        </strong>
                      </div>

                      <div>
                        <span>Signals</span>
                        <strong>
                          {model.signals ??
                            "—"}
                        </strong>
                      </div>

                      <div>
                        <span>Updated</span>
                        <strong>
                          {model.updatedAt}
                        </strong>
                      </div>

                    </div>

                    <button
                      className="models-mobile-action"
                      onClick={() =>
                        openModel(
                          model.id
                        )
                      }
                    >
                      View Model
                    </button>

                  </div>
                )
              )}

            </div>
          )}

          {/* PAGINATION */}
          <div className="models-pagination">

            <span>
              Showing{" "}
              {filteredModels.length} of{" "}
              {models.length} models
            </span>

            <div>
              <button disabled>
                Previous
              </button>

              <button className="active">
                1
              </button>

              <button disabled>
                2
              </button>

              <button disabled>
                Next
              </button>
            </div>

          </div>

        </div>

        {/* ACTIVITY */}
        <div className="models-card models-activity-card">

          <div className="models-card-header">

            <div>
              <h2>Model Activity</h2>

              <p>
                Recent changes and events across model versions.
              </p>
            </div>

            <button
              className="models-outline-button"
              onClick={loadModels}
            >
              Refresh
            </button>

          </div>

          <div className="models-activity-list">

            {activity.length === 0 ? (
              <div className="models-empty">
                <div>◎</div>

                <strong>
                  No model activity
                </strong>

                <span>
                  Activity will appear as models are created and changed.
                </span>
              </div>
            ) : (
              activity.map((item) => (
                <div
                  className="models-activity-item"
                  key={item.id}
                >

                  <div
                    className={`models-activity-icon ${item.type}`}
                  >
                    {item.type ===
                    "active"
                      ? "✓"
                      : item.type ===
                        "evaluation"
                      ? "◎"
                      : item.type ===
                        "archive"
                      ? "□"
                      : "⚙"}
                  </div>

                  <div className="models-activity-content">

                    <div className="models-activity-title">

                      <strong>
                        {item.event}
                      </strong>

                      <span>
                        {item.version}
                      </span>

                    </div>

                    <p>
                      {item.description}
                    </p>

                  </div>

                  <time>
                    {item.date}
                  </time>

                </div>
              ))
            )}

          </div>

        </div>

      </div>
    </AdminShell>
  );
}

/* =========================================================
   STAT
========================================================= */

function ModelStat({
  label,
  value,
  description,
  icon,
  type,
}: {
  label: string;
  value: string;
  description: string;
  icon: string;
  type:
    | "blue"
    | "green"
    | "purple"
    | "orange";
}) {
  return (
    <div className="models-stat-card">

      <div
        className={`models-stat-icon ${type}`}
      >
        {icon}
      </div>

      <div className="models-stat-content">

        <span>{label}</span>

        <strong>{value}</strong>

        <small>{description}</small>

      </div>

    </div>
  );
}

/* =========================================================
   CONFIG ITEM
========================================================= */

function ModelConfig({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="models-config-row">

      <span>{label}</span>

      <strong>{value}</strong>

    </div>
  );
}

/* =========================================================
   STATUS BADGE
========================================================= */

function ModelStatusBadge({
  status,
}: {
  status: ModelStatus;
}) {
  return (
    <span
      className={`models-status-badge ${status.toLowerCase()}`}
    >
      <span />
      {status}
    </span>
  );
}