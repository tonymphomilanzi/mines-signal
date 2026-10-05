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

/* =============================================================
   API
============================================================= */

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

/* =============================================================
   TYPES
============================================================= */

type MessageStatus =
  | "PUBLISHED"
  | "FAILED"
  | "PENDING";

type ParseStatus =
  | "SUCCESS"
  | "PARTIAL"
  | "FAILED";

type SyncStatus =
  | "SYNCED"
  | "PENDING"
  | "FAILED";

type TelegramMessage = {
  id: string;

  telegramMessageId:
    | number
    | null;

  channelId: string;
  channelName: string;
  channelUsername: string;

  status: MessageStatus;

  signalNumber: string;
  signalId: string;

  game: string;
  boardSize: number;
  mineCount: number;
  attempts: number;

  confidence:
    | number
    | null;

  recommendedPositions: number[];

  messageText: string;

  publishedAt: string;
  syncedAt: string;
  parsedAt: string;

  views: number;
  forwards: number;

  parseStatus: ParseStatus;
  syncStatus: SyncStatus;

  modelVersion: string;

  errorMessage:
    | string
    | null;

  createdAt: string;
  updatedAt: string;
};

/* =============================================================
   HELPERS
============================================================= */

function formatValue(
  value: unknown,
): string {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return "—";
  }

  return String(value);
}

function formatDate(
  value: string | null | undefined,
): string {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value;
  }

  return date.toLocaleString(
    undefined,
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    },
  );
}

function formatConfidence(
  value: number | null,
): string {
  if (value === null) {
    return "—";
  }

  return `${value}%`;
}

/* =============================================================
   API MAPPING
============================================================= */

function mapTelegramMessage(
  data: any,
): TelegramMessage {
  return {
    id: String(
      data.id,
    ),

    telegramMessageId:
      data.telegram_message_id ??
      null,

    channelId:
      data.channel_id ??
      "",

    channelName:
      data.channel_name ??
      "Telegram Channel",

    channelUsername:
      data.channel_username ??
      "—",

    status:
      data.status ??
      "PENDING",

    signalNumber:
      data.signal_number ??
      data.signal_id ??
      "—",

    signalId:
      data.signal_id ??
      "",

    game:
      data.game ??
      "Mines Classic",

    boardSize:
      Number(
        data.board_size ??
          5,
      ),

    mineCount:
      Number(
        data.mine_count ??
          0,
      ),

    attempts:
      Number(
        data.attempts_allowed ??
          data.attempts ??
          0,
      ),

    confidence:
      data.confidence !== null &&
      data.confidence !== undefined
        ? Number(
            data.confidence,
          )
        : null,

    recommendedPositions:
      Array.isArray(
        data.recommended_positions,
      )
        ? data.recommended_positions.map(
            (position: unknown) =>
              Number(position),
          )
        : [],

    messageText:
      data.message_text ??
      "",

    publishedAt:
      data.published_at ??
      "",

    syncedAt:
      data.synced_at ??
      "",

    parsedAt:
      data.parsed_at ??
      "",

    views:
      Number(
        data.views ??
          0,
      ),

    forwards:
      Number(
        data.forwards ??
          0,
      ),

    parseStatus:
      data.parse_status ??
      "SUCCESS",

    syncStatus:
      data.sync_status ??
      "PENDING",

    modelVersion:
      data.model_version ??
      "N/A",

    errorMessage:
      data.error_message ??
      null,

    createdAt:
      data.created_at ??
      "",

    updatedAt:
      data.updated_at ??
      "",
  };
}

/* =============================================================
   PAGE
============================================================= */

export default function TelegramMessageDetailsPage() {
  const params =
    useParams();

  const router =
    useRouter();

  const messageId =
    String(
      params?.id ?? "",
    );

  const [message, setMessage] =
    useState<TelegramMessage | null>(
      null,
    );

  const [loading, setLoading] =
    useState(true);

  const [retrying, setRetrying] =
    useState(false);

  const [error, setError] =
    useState<string | null>(
      null,
    );

  const [retrySuccess, setRetrySuccess] =
    useState<string | null>(
      null,
    );

  /* ===========================================================
     API REQUEST
  =========================================================== */

  const apiRequest =
    useCallback(
      async <T,>(
        path: string,
        options: RequestInit = {},
      ): Promise<T> => {
        const response =
          await fetch(
            `${API_URL}${path}`,
            {
              ...options,

              credentials:
                "include",

              headers: {
                "Content-Type":
                  "application/json",

                ...(options.headers ||
                  {}),
              },

              cache:
                "no-store",
            },
          );

        if (!response.ok) {
          let message =
            `Request failed (${response.status})`;

          try {
            const data =
              await response.json();

            if (
              typeof data?.detail ===
              "string"
            ) {
              message =
                data.detail;
            } else if (
              typeof data?.message ===
              "string"
            ) {
              message =
                data.message;
            }
          } catch {
            // Keep default message.
          }

          throw new Error(
            message,
          );
        }

        return response.json();
      },
      [],
    );

  /* ===========================================================
     LOAD MESSAGE
  =========================================================== */

  const loadMessage =
    useCallback(
      async () => {
        if (!messageId) {
          setLoading(false);
          return;
        }

        setLoading(true);
        setError(null);

        try {
          const data =
            await apiRequest<any>(
              `/api/telegram/messages/${messageId}`,
            );

          setMessage(
            mapTelegramMessage(
              data,
            ),
          );
        } catch (err) {
          const message =
            err instanceof Error
              ? err.message
              : "Unable to load Telegram message.";

          setError(message);
          setMessage(null);
        } finally {
          setLoading(false);
        }
      },
      [
        apiRequest,
        messageId,
      ],
    );

  /* ===========================================================
     INITIAL LOAD
  =========================================================== */

  useEffect(() => {
    void loadMessage();
  }, [loadMessage]);

  /* ===========================================================
     RETRY SYNC
  =========================================================== */

  const retrySync =
    async () => {
      if (
        !message ||
        retrying
      ) {
        return;
      }

      setRetrying(true);
      setError(null);
      setRetrySuccess(null);

      try {
        const response =
          await apiRequest<any>(
            `/api/telegram/messages/${message.id}/retry`,
            {
              method: "POST",
            },
          );

        const successMessage =
          response?.message ||
          "Telegram message was successfully retried.";

        setRetrySuccess(
          successMessage,
        );

        await loadMessage();
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : "Telegram retry failed.";

        setError(message);
      } finally {
        setRetrying(false);
      }
    };

  /* ===========================================================
     LOADING
  =========================================================== */

  if (loading) {
    return (
      <AdminShell>
        <div className="telegram-message-not-found">

          <div className="telegram-message-not-found-icon">
            <span>
              ⟳
            </span>
          </div>

          <h1>
            Loading Message
          </h1>

          <p>
            Loading the Telegram
            message from the backend.
          </p>

        </div>
      </AdminShell>
    );
  }

  /* ===========================================================
     NOT FOUND / ERROR
  =========================================================== */

  if (!message) {
    return (
      <AdminShell>
        <div className="telegram-message-not-found">

          <div className="telegram-message-not-found-icon">
            <span>
              ✉
            </span>
          </div>

          <h1>
            Message Not Found
          </h1>

          <p>
            {error ||
              "The Telegram message you are looking for could not be found."}
          </p>

          <button
            type="button"
            className="admin-btn admin-btn-primary"
            onClick={() =>
              router.push(
                "/telegram",
              )
            }
          >
            Back to Telegram
          </button>

        </div>
      </AdminShell>
    );
  }

  const parsedSuccessfully =
    message.parseStatus ===
    "SUCCESS";

  const isFailed =
    message.status ===
    "FAILED";

  const isSynced =
    message.syncStatus ===
    "SYNCED";

  return (
    <AdminShell>

      <div className="telegram-message-details-page">

        {/* ===================================================
            HEADER
        ==================================================== */}

        <div className="telegram-message-details-header">

          <div className="telegram-message-header-left">

            <button
              type="button"
              className="telegram-message-back"
              onClick={() =>
                router.push(
                  "/telegram",
                )
              }
              aria-label="Back to Telegram"
            >
              ←
            </button>

            <div>

              <div className="telegram-message-breadcrumb">

                Telegram

                <span>
                  /
                </span>

                Messages

                <span>
                  /
                </span>

                {message.id}

              </div>

              <div className="telegram-message-title-row">

                <div className="telegram-message-title-icon">
                  <span>
                    ✈
                  </span>
                </div>

                <div>

                  <h1>
                    Telegram Message
                  </h1>

                  <p>
                    {message.signalNumber}
                    {" · "}
                    Message #
                    {formatValue(
                      message.telegramMessageId,
                    )}
                  </p>

                </div>

              </div>

            </div>

          </div>

          <div className="telegram-message-header-actions">

            <button
              type="button"
              className="admin-btn admin-btn-secondary"
              onClick={() =>
                router.push(
                  `/signals/${message.signalId}`,
                )
              }
            >
              View Signal
            </button>

            {isFailed && (
              <button
                type="button"
                className="admin-btn admin-btn-primary"
                onClick={
                  retrySync
                }
                disabled={
                  retrying
                }
              >
                {retrying
                  ? "Retrying..."
                  : "Retry Sync"}
              </button>
            )}

          </div>

        </div>

        {/* ===================================================
            FEEDBACK
        ==================================================== */}

        {error && (
          <div
            style={{
              marginBottom:
                "18px",
              padding:
                "13px 16px",
              borderRadius:
                "12px",
              border:
                "1px solid rgba(239,68,68,.25)",
              background:
                "rgba(239,68,68,.08)",
              color:
                "#fca5a5",
              fontSize:
                "13px",
            }}
          >
            {error}
          </div>
        )}

        {retrySuccess && (
          <div
            style={{
              marginBottom:
                "18px",
              padding:
                "13px 16px",
              borderRadius:
                "12px",
              border:
                "1px solid rgba(34,197,94,.25)",
              background:
                "rgba(34,197,94,.08)",
              color:
                "#86efac",
              fontSize:
                "13px",
            }}
          >
            {retrySuccess}
          </div>
        )}

        {/* ===================================================
            SUMMARY
        ==================================================== */}

        <div className="telegram-message-summary-grid">

          <TelegramMessageStat
            label="Message Status"
            value={
              message.status
            }
            icon="✓"
            tone={
              message.status ===
              "FAILED"
                ? "danger"
                : message.status ===
                    "PENDING"
                  ? "warning"
                  : "success"
            }
          />

          <TelegramMessageStat
            label="Confidence"
            value={formatConfidence(
              message.confidence,
            )}
            icon="◈"
            tone="primary"
          />

          <TelegramMessageStat
            label="Views"
            value={message.views.toLocaleString()}
            icon="◉"
            tone="neutral"
          />

          <TelegramMessageStat
            label="Forwards"
            value={message.forwards.toLocaleString()}
            icon="↗"
            tone="neutral"
          />

        </div>

        {/* ===================================================
            MAIN GRID
        ==================================================== */}

        <div className="telegram-message-main-grid">

          {/* =================================================
              LEFT COLUMN
          ================================================== */}

          <div className="telegram-message-main-column">

            {/* MESSAGE OVERVIEW */}

            <section className="admin-card">

              <div className="admin-card-header">

                <div>

                  <h2>
                    Message Overview
                  </h2>

                  <p>
                    Telegram publishing and synchronization
                    information.
                  </p>

                </div>

                <TelegramStatusBadge
                  status={
                    message.status
                  }
                />

              </div>

              <div className="telegram-message-info-grid">

                <TelegramInfo
                  label="Message ID"
                  value={
                    message.id
                  }
                />

                <TelegramInfo
                  label="Telegram Message ID"
                  value={
                    message.telegramMessageId !==
                    null
                      ? `#${message.telegramMessageId}`
                      : "—"
                  }
                />

                <TelegramInfo
                  label="Channel"
                  value={
                    message.channelName
                  }
                />

                <TelegramInfo
                  label="Channel Username"
                  value={
                    message.channelUsername
                  }
                />

                <TelegramInfo
                  label="Channel ID"
                  value={
                    message.channelId
                  }
                />

                <TelegramInfo
                  label="Signal"
                  value={
                    message.signalNumber
                  }
                  accent
                />

                <TelegramInfo
                  label="Published"
                  value={formatDate(
                    message.publishedAt,
                  )}
                />

                <TelegramInfo
                  label="Model Version"
                  value={
                    message.modelVersion
                  }
                />

              </div>

            </section>

            {/* MESSAGE CONTENT */}

            <section className="admin-card">

              <div className="admin-card-header">

                <div>

                  <h2>
                    Message Content
                  </h2>

                  <p>
                    Original Telegram message
                    content.
                  </p>

                </div>

                <span className="telegram-live-badge">
                  Telegram
                </span>

              </div>

              <div className="telegram-message-content-wrapper">

                <div className="telegram-message-content-top">

                  <div className="telegram-channel-avatar">
                    ✈
                  </div>

                  <div>

                    <strong>
                      {
                        message.channelName
                      }
                    </strong>

                    <span>
                      {
                        message.channelUsername
                      }
                    </span>

                  </div>

                </div>

                <div className="telegram-message-content">

                  {message.messageText
                    .split("\n")
                    .map(
                      (
                        line,
                        index,
                      ) => (
                        <div
                          key={`${index}-${line}`}
                          className={
                            line.trim() ===
                            ""
                              ? "telegram-message-empty-line"
                              : ""
                          }
                        >
                          {line ||
                            "\u00A0"}
                        </div>
                      ),
                    )}

                </div>

                <div className="telegram-message-content-footer">

                  <span>
                    {formatDate(
                      message.publishedAt,
                    )}
                  </span>

                  <span>
                    ✓✓
                  </span>

                </div>

              </div>

            </section>

            {/* PARSED SIGNAL */}

            <section className="admin-card">

              <div className="admin-card-header">

                <div>

                  <h2>
                    Parsed Signal
                  </h2>

                  <p>
                    Structured data extracted
                    from the Telegram message.
                  </p>

                </div>

                <span
                  className={`telegram-parse-badge ${
                    parsedSuccessfully
                      ? "success"
                      : "failed"
                  }`}
                >
                  {
                    message.parseStatus
                  }
                </span>

              </div>

              <div className="telegram-parsed-grid">

                <TelegramInfo
                  label="Signal Number"
                  value={
                    message.signalNumber
                  }
                  accent
                />

                <TelegramInfo
                  label="Game"
                  value={
                    message.game
                  }
                />

                <TelegramInfo
                  label="Board Size"
                  value={`${message.boardSize} × ${message.boardSize}`}
                />

                <TelegramInfo
                  label="Mine Count"
                  value={`${message.mineCount} mines`}
                />

                <TelegramInfo
                  label="Attempts"
                  value={`${message.attempts}`}
                />

                <TelegramInfo
                  label="Model Confidence"
                  value={formatConfidence(
                    message.confidence,
                  )}
                  accent
                />

              </div>

            </section>

            {/* BOARD */}

            <section className="admin-card">

              <div className="admin-card-header">

                <div>

                  <h2>
                    Recommended Board
                  </h2>

                  <p>
                    Positions parsed from the
                    Telegram message.
                  </p>

                </div>

                <span className="telegram-board-size">
                  {message.boardSize} ×{" "}
                  {message.boardSize}
                </span>

              </div>

              <TelegramBoard
                positions={
                  message.recommendedPositions
                }
                boardSize={
                  message.boardSize
                }
              />

              <div className="telegram-board-legend">

                <div>

                  <span className="telegram-legend-star">
                    ★
                  </span>

                  Recommended position

                </div>

                <div>

                  <span className="telegram-legend-empty">
                    •
                  </span>

                  Other position

                </div>

              </div>

              <div className="telegram-board-note">

                <span>
                  i
                </span>

                <p>
                  The highlighted cells represent
                  positions parsed from this message.
                  They are stored as recommendations
                  and should not be treated as
                  guaranteed outcomes.
                </p>

              </div>

            </section>

            {/* SIGNAL RELATIONSHIP */}

            <section className="admin-card">

              <div className="admin-card-header">

                <div>

                  <h2>
                    Signal Relationship
                  </h2>

                  <p>
                    Connection between this Telegram
                    message and the internal signal.
                  </p>

                </div>

              </div>

              <div className="telegram-signal-link-card">

                <div className="telegram-signal-link-icon">
                  #
                </div>

                <div className="telegram-signal-link-content">

                  <strong>
                    {
                      message.signalNumber
                    }
                  </strong>

                  <span>
                    {
                      message.game
                    }
                    {" · "}
                    {
                      message.mineCount
                    }{" "}
                    mines
                    {" · "}
                    {
                      message.attempts
                    }{" "}
                    attempts
                  </span>

                </div>

                <button
                  type="button"
                  onClick={() =>
                    router.push(
                      `/signals/${message.signalId}`,
                    )
                  }
                >
                  View Signal →
                </button>

              </div>

            </section>

          </div>

          {/* =================================================
              RIGHT COLUMN
          ================================================== */}

          <aside className="telegram-message-side-column">

            {/* PUBLISHING */}

            <section className="admin-card">

              <div className="admin-card-header">

                <div>

                  <h2>
                    Publishing
                  </h2>

                  <p>
                    Telegram delivery status.
                  </p>

                </div>

              </div>

              <div className="telegram-publishing-status">

                <div
                  className={`telegram-publishing-icon ${
                    isSynced
                      ? "success"
                      : "failed"
                  }`}
                >
                  {isSynced
                    ? "✓"
                    : "!"}
                </div>

                <div>

                  <strong>
                    {isSynced
                      ? "Message synced"
                      : isFailed
                        ? "Sync requires attention"
                        : "Message pending"}
                  </strong>

                  <span>
                    {isSynced
                      ? "Telegram data is synchronized."
                      : isFailed
                        ? "The message could not be synchronized."
                        : "Telegram message is waiting for synchronization."}
                  </span>

                </div>

              </div>

              <div className="telegram-side-info-list">

                <TelegramSideInfo
                  label="Published"
                  value={formatDate(
                    message.publishedAt,
                  )}
                />

                <TelegramSideInfo
                  label="Synced"
                  value={formatDate(
                    message.syncedAt,
                  )}
                />

                <TelegramSideInfo
                  label="Parsed"
                  value={formatDate(
                    message.parsedAt,
                  )}
                />

                <TelegramSideInfo
                  label="Message ID"
                  value={
                    message.telegramMessageId !==
                    null
                      ? `#${message.telegramMessageId}`
                      : "—"
                  }
                />

                <TelegramSideInfo
                  label="Attempts"
                  value={String(
                    message.attempts,
                  )}
                />

              </div>

              {message.errorMessage && (
                <div
                  style={{
                    marginTop:
                      "16px",
                    padding:
                      "12px",
                    borderRadius:
                      "10px",
                    background:
                      "rgba(239,68,68,.07)",
                    border:
                      "1px solid rgba(239,68,68,.18)",
                  }}
                >

                  <span
                    style={{
                      display:
                        "block",
                      marginBottom:
                        "5px",
                      fontSize:
                        "11px",
                      color:
                        "#fca5a5",
                      fontWeight:
                        700,
                      textTransform:
                        "uppercase",
                    }}
                  >
                    Error
                  </span>

                  <p
                    style={{
                      margin:
                        0,
                      fontSize:
                        "12px",
                      lineHeight:
                        1.5,
                      color:
                        "rgba(255,255,255,.65)",
                    }}
                  >
                    {
                      message.errorMessage
                    }
                  </p>

                </div>
              )}

            </section>

            {/* PARSER STATUS */}

            <section className="admin-card">

              <div className="admin-card-header">

                <div>

                  <h2>
                    Parser Status
                  </h2>

                  <p>
                    Message processing pipeline.
                  </p>

                </div>

              </div>

              <div className="telegram-processing-list">

                <TelegramProcessingStep
                  label="Message published"
                  status="complete"
                  time={formatDate(
                    message.publishedAt,
                  )}
                />

                <TelegramProcessingStep
                  label="Message synchronized"
                  status={
                    message.syncStatus ===
                    "SYNCED"
                      ? "complete"
                      : message.syncStatus ===
                          "FAILED"
                        ? "failed"
                        : "pending"
                  }
                  time={formatDate(
                    message.syncedAt,
                  )}
                />

                <TelegramProcessingStep
                  label="Signal parsed"
                  status={
                    message.parseStatus ===
                    "SUCCESS"
                      ? "complete"
                      : message.parseStatus ===
                          "FAILED"
                        ? "failed"
                        : "pending"
                  }
                  time={formatDate(
                    message.parsedAt,
                  )}
                />

                <TelegramProcessingStep
                  label="Signal linked"
                  status={
                    message.signalId
                      ? "complete"
                      : "pending"
                  }
                />

              </div>

            </section>

            {/* MESSAGE METRICS */}

            <section className="admin-card">

              <div className="admin-card-header">

                <div>

                  <h2>
                    Message Metrics
                  </h2>

                  <p>
                    Telegram engagement information.
                  </p>

                </div>

              </div>

              <div className="telegram-metric-list">

                <TelegramMetric
                  label="Views"
                  value={message.views.toLocaleString()}
                />

                <TelegramMetric
                  label="Forwards"
                  value={message.forwards.toLocaleString()}
                />

                <TelegramMetric
                  label="Recommended cells"
                  value={`${message.recommendedPositions.length}`}
                />

                <TelegramMetric
                  label="Mine configuration"
                  value={`${message.mineCount}`}
                />

              </div>

            </section>

            {/* SYSTEM INFORMATION */}

            <section className="admin-card">

              <div className="admin-card-header">

                <div>

                  <h2>
                    System Information
                  </h2>

                  <p>
                    Internal message identifiers.
                  </p>

                </div>

              </div>

              <div className="telegram-system-info">

                <TelegramSystemRow
                  label="Record ID"
                  value={message.id}
                />

                <TelegramSystemRow
                  label="Signal ID"
                  value={message.signalId}
                />

                <TelegramSystemRow
                  label="Model"
                  value={message.modelVersion}
                />

                <TelegramSystemRow
                  label="Channel ID"
                  value={message.channelId}
                />

              </div>

            </section>

          </aside>

        </div>

        {/* ===================================================
            ACTIVITY
        ==================================================== */}

        <section className="admin-card telegram-message-activity-card">

          <div className="admin-card-header">

            <div>

              <h2>
                Message Activity
              </h2>

              <p>
                Processing and synchronization
                history.
              </p>

            </div>

          </div>

          <div className="telegram-activity-timeline">

            <TelegramActivity
              icon="✈"
              title="Telegram message published"
              description={`Message was published to ${message.channelName}.`}
              time={formatDate(
                message.publishedAt,
              )}
              status="success"
            />

            <TelegramActivity
              icon="↻"
              title="Message synchronized"
              description={
                message.syncStatus ===
                "SYNCED"
                  ? "Telegram message metadata was synchronized successfully."
                  : message.errorMessage ||
                    "Telegram synchronization failed."
              }
              time={formatDate(
                message.syncedAt,
              )}
              status={
                message.syncStatus ===
                "SYNCED"
                  ? "success"
                  : message.syncStatus ===
                      "FAILED"
                    ? "failed"
                    : "pending"
              }
            />

            <TelegramActivity
              icon="⌁"
              title="Signal parser executed"
              description={
                message.parseStatus ===
                "SUCCESS"
                  ? `Signal ${message.signalNumber} was successfully parsed.`
                  : "Signal parsing did not complete successfully."
              }
              time={formatDate(
                message.parsedAt,
              )}
              status={
                message.parseStatus ===
                "SUCCESS"
                  ? "success"
                  : message.parseStatus ===
                      "FAILED"
                    ? "failed"
                    : "pending"
              }
            />

            <TelegramActivity
              icon="#"
              title="Signal linked"
              description={
                message.signalId
                  ? `Message linked to internal signal ${message.signalNumber}.`
                  : "No internal signal is linked to this message."
              }
              time={message.signalId
                ? formatDate(
                    message.createdAt,
                  )
                : "—"}
              status={
                message.signalId
                  ? "success"
                  : "pending"
              }
            />

          </div>

        </section>

      </div>

    </AdminShell>
  );
}

/* =============================================================
   STAT
============================================================= */

function TelegramMessageStat({
  label,
  value,
  icon,
  tone,
}: {
  label: string;
  value: string;
  icon: string;
  tone:
    | "primary"
    | "success"
    | "warning"
    | "danger"
    | "neutral";
}) {
  return (
    <div className="telegram-message-stat">

      <div
        className={`telegram-message-stat-icon ${tone}`}
      >
        {icon}
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

/* =============================================================
   STATUS BADGE
============================================================= */

function TelegramStatusBadge({
  status,
}: {
  status: MessageStatus;
}) {
  return (
    <span
      className={`telegram-message-status-badge ${status.toLowerCase()}`}
    >
      <i />
      {status}
    </span>
  );
}

/* =============================================================
   INFO
============================================================= */

function TelegramInfo({
  label,
  value,
  accent = false,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div className="telegram-info-item">

      <span>
        {label}
      </span>

      <strong
        className={
          accent
            ? "accent"
            : ""
        }
      >
        {value}
      </strong>

    </div>
  );
}

/* =============================================================
   SIDE INFO
============================================================= */

function TelegramSideInfo({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="telegram-side-info">

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

    </div>
  );
}

/* =============================================================
   BOARD
============================================================= */

function TelegramBoard({
  positions,
  boardSize,
}: {
  positions: number[];
  boardSize: number;
}) {
  const total =
    boardSize * boardSize;

  return (
    <div
      className="telegram-board"
      style={{
        gridTemplateColumns: `repeat(${boardSize}, minmax(0, 1fr))`,
      }}
    >

      {Array.from({
        length: total,
      }).map(
        (_, index) => {
          const position =
            index + 1;

          const highlighted =
            positions.includes(
              position,
            );

          return (
            <div
              key={position}
              className={`telegram-board-cell ${
                highlighted
                  ? "highlighted"
                  : ""
              }`}
            >

              {highlighted ? (
                <span>
                  ★
                </span>
              ) : (
                <small>
                  {position}
                </small>
              )}

            </div>
          );
        },
      )}

    </div>
  );
}

/* =============================================================
   PROCESSING STEP
============================================================= */

function TelegramProcessingStep({
  label,
  status,
  time,
}: {
  label: string;
  status:
    | "complete"
    | "failed"
    | "pending";
  time?: string;
}) {
  return (
    <div className="telegram-processing-step">

      <div
        className={`telegram-processing-icon ${status}`}
      >
        {status ===
        "complete"
          ? "✓"
          : status ===
              "failed"
            ? "!"
            : "•"}
      </div>

      <div className="telegram-processing-content">

        <strong>
          {label}
        </strong>

        {time && (
          <span>
            {time}
          </span>
        )}

      </div>

      <span
        className={`telegram-processing-status ${status}`}
      >
        {status ===
        "complete"
          ? "Complete"
          : status ===
              "failed"
            ? "Failed"
            : "Pending"}
      </span>

    </div>
  );
}

/* =============================================================
   METRIC
============================================================= */

function TelegramMetric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="telegram-metric">

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

    </div>
  );
}

/* =============================================================
   SYSTEM ROW
============================================================= */

function TelegramSystemRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="telegram-system-row">

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

    </div>
  );
}

/* =============================================================
   ACTIVITY
============================================================= */

function TelegramActivity({
  icon,
  title,
  description,
  time,
  status,
}: {
  icon: string;
  title: string;
  description: string;
  time: string;
  status:
    | "success"
    | "failed"
    | "pending";
}) {
  return (
    <div className="telegram-activity-item">

      <div
        className={`telegram-activity-icon ${status}`}
      >
        {icon}
      </div>

      <div className="telegram-activity-line" />

      <div className="telegram-activity-content">

        <div className="telegram-activity-title-row">

          <strong>
            {title}
          </strong>

          <span>
            {time}
          </span>

        </div>

        <p>
          {description}
        </p>

      </div>

    </div>
  );
} 
