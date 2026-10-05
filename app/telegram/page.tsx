"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import AdminShell from "@/components/layout/AdminShell";

/* ============================================================
   API
============================================================ */

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

/* ============================================================
   TYPES
============================================================ */

type TelegramMessageStatus =
  | "PUBLISHED"
  | "PENDING"
  | "FAILED";

type TelegramMessage = {
  id: string;
  signal_id: string;
  telegram_message_id: number | null;

  channel_id: string;
  channel_name: string | null;
  channel_username: string | null;

  status: TelegramMessageStatus;
  sync_status: "PENDING" | "SYNCED" | "FAILED";
  parse_status: "SUCCESS" | "PARTIAL" | "FAILED";

  message_text: string;

  attempts: number;
  error_message: string | null;

  views: number;
  forwards: number;

  published_at: string | null;
  synced_at: string | null;
  parsed_at: string | null;

  created_at: string;
  updated_at: string;

  signal_number?: string | null;
  game?: string | null;
  board_size?: number | null;
  mine_count?: number | null;
  confidence?: number | null;
  recommended_positions?: number[];
  model_version?: string | null;
  attempts_allowed?: number | null;
};

type TelegramConfiguration = {
  id: string;

  bot_name: string | null;

  channel_id: string | null;
  channel_name: string | null;
  channel_username: string | null;

  automatic_publishing: boolean;
  publish_confirmed_signals: boolean;
  publish_results: boolean;

  publishing_template: string | null;

  created_at: string;
  updated_at: string;
};

type TelegramStatusResponse = {
  configured: boolean;
  connected: boolean;

  bot_name: string | null;
  bot_username: string | null;

  channel_id: string | null;
  channel_username: string | null;
  channel_name?: string | null;

  checked_at?: string;
};

type TelegramStatistics = {
  published: number;
  pending: number;
  failed: number;
  total: number;
};

type TelegramMessagesResponse = {
  items?: TelegramMessage[];
  total?: number;
};

type TelegramTestResponse = {
  success: boolean;
  message: string;
  telegram_message_id?: number | null;
};

/* ============================================================
   HELPERS
============================================================ */

function formatDate(
  value: string | null | undefined,
): string {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getSignalNumber(
  message: TelegramMessage,
): string {
  return (
    message.signal_number ||
    message.signal_id ||
    "Unknown"
  );
}

function getChannelUsername(
  message: TelegramMessage,
): string {
  const username =
    message.channel_username;

  if (!username) {
    return "—";
  }

  return username.startsWith("@")
    ? username
    : `@${username}`;
}

function getStatusLabel(
  status: TelegramMessageStatus,
): "Published" | "Pending" | "Failed" {
  switch (status) {
    case "PUBLISHED":
      return "Published";

    case "PENDING":
      return "Pending";

    case "FAILED":
      return "Failed";

    default:
      return "Pending";
  }
}

/* ============================================================
   PAGE
============================================================ */

export default function TelegramPage() {
  const [messages, setMessages] =
    useState<TelegramMessage[]>([]);

  const [configuration, setConfiguration] =
    useState<TelegramConfiguration | null>(
      null,
    );

  const [telegram, setTelegram] =
    useState<TelegramStatusResponse>({
      configured: false,
      connected: false,
      bot_name: null,
      bot_username: null,
      channel_id: null,
      channel_username: null,
      channel_name: null,
    });

  const [statistics, setStatistics] =
    useState<TelegramStatistics>({
      published: 0,
      pending: 0,
      failed: 0,
      total: 0,
    });

  const [loading, setLoading] =
    useState(true);

  const [refreshing, setRefreshing] =
    useState(false);

  const [testSending, setTestSending] =
    useState(false);

  const [savingPublishing, setSavingPublishing] =
    useState(false);

  const [search, setSearch] =
    useState("");

  const [statusFilter, setStatusFilter] =
    useState("All");

  const [error, setError] =
    useState<string | null>(null);

  /* ==========================================================
     API REQUEST
  ========================================================== */

  const apiRequest = useCallback(
    async <T,>(
      path: string,
      options: RequestInit = {},
    ): Promise<T> => {
      const response = await fetch(
        `${API_URL}${path}`,
        {
          ...options,
          credentials: "include",
          headers: {
            "Content-Type":
              "application/json",
            ...(options.headers || {}),
          },
          cache: "no-store",
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
            message = data.detail;
          } else if (
            typeof data?.message ===
            "string"
          ) {
            message = data.message;
          }
        } catch {
          // Keep the default HTTP error.
        }

        throw new Error(message);
      }

      return response.json();
    },
    [],
  );

  /* ==========================================================
     LOAD TELEGRAM DATA
  ========================================================== */

  const loadTelegramData =
    useCallback(
      async (
        showSpinner = true,
      ) => {
        if (showSpinner) {
          setRefreshing(true);
        }

        setError(null);

        try {
          const [
            statusData,
            configData,
            messagesData,
            statisticsData,
          ] = await Promise.all([
            apiRequest<TelegramStatusResponse>(
              "/api/telegram/status",
            ),

            apiRequest<TelegramConfiguration>(
              "/api/telegram/config",
            ),

            apiRequest<
              | TelegramMessage[]
              | TelegramMessagesResponse
            >(
              "/api/telegram?limit=100",
            ),

            apiRequest<TelegramStatistics>(
              "/api/telegram/statistics",
            ),
          ]);

          setTelegram(statusData);

          setConfiguration(configData);

          const messageItems =
            Array.isArray(messagesData)
              ? messagesData
              : messagesData.items || [];

          setMessages(messageItems);

          setStatistics(
            statisticsData,
          );
        } catch (err) {
          const message =
            err instanceof Error
              ? err.message
              : "Unable to load Telegram data.";

          setError(message);
        } finally {
          setLoading(false);
          setRefreshing(false);
        }
      },
      [apiRequest],
    );

  /* ==========================================================
     INITIAL LOAD
  ========================================================== */

  useEffect(() => {
    void loadTelegramData(true);
  }, [loadTelegramData]);

  /* ==========================================================
     AUTOMATIC PUBLISHING
  ========================================================== */

  const toggleAutomaticPublishing =
    async () => {
      if (!configuration) {
        return;
      }

      const nextValue =
        !configuration.automatic_publishing;

      setSavingPublishing(true);
      setError(null);

      try {
        const updated =
          await apiRequest<TelegramConfiguration>(
            "/api/telegram/config",
            {
              method: "PATCH",
              body: JSON.stringify({
                automatic_publishing:
                  nextValue,
              }),
            },
          );

        setConfiguration(updated);
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : "Unable to update publishing settings.";

        setError(message);
      } finally {
        setSavingPublishing(false);
      }
    };

  /* ==========================================================
     TEST MESSAGE
  ========================================================== */

  const sendTestMessage =
    async () => {
      if (testSending) {
        return;
      }

      setTestSending(true);
      setError(null);

      try {
        const response =
          await apiRequest<TelegramTestResponse>(
            "/api/telegram/test",
            {
              method: "POST",
              body: JSON.stringify({
                message:
                  "🧪 <b>Mines Lab Telegram Test</b>\n\n"
                  + "Telegram publishing is connected successfully.\n\n"
                  + "This is an administrator test message.",
              }),
            },
          );

        window.alert(
          response.message ||
            "Test message sent successfully.",
        );

        await loadTelegramData(false);
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : "Unable to send Telegram test message.";

        setError(message);
      } finally {
        setTestSending(false);
      }
    };

  /* ==========================================================
     FILTERING
  ========================================================== */

  const filteredMessages =
    useMemo(() => {
      const normalizedSearch =
        search
          .trim()
          .toLowerCase();

      return messages.filter(
        (message) => {
          const signalNumber =
            getSignalNumber(
              message,
            ).toLowerCase();

          const messageId =
            message.telegram_message_id
              ? String(
                  message.telegram_message_id,
                ).toLowerCase()
              : "";

          const channel =
            getChannelUsername(
              message,
            ).toLowerCase();

          const matchesSearch =
            normalizedSearch === "" ||
            signalNumber.includes(
              normalizedSearch,
            ) ||
            messageId.includes(
              normalizedSearch,
            ) ||
            channel.includes(
              normalizedSearch,
            );

          const matchesStatus =
            statusFilter === "All" ||
            getStatusLabel(
              message.status,
            ) === statusFilter;

          return (
            matchesSearch &&
            matchesStatus
          );
        },
      );
    }, [
      messages,
      search,
      statusFilter,
    ]);

  /* ==========================================================
     CONNECTION DISPLAY
  ========================================================== */

  const connectionLabel =
    telegram.connected
      ? "Connected"
      : "Disconnected";

  const connectionClass =
    telegram.connected
      ? "connected"
      : "disconnected";

  const botUsername =
    telegram.bot_username ||
    "—";

  const channelUsername =
    telegram.channel_username ||
    configuration?.channel_username ||
    "—";

  const channelName =
    telegram.channel_name ||
    configuration?.channel_name ||
    "Telegram Channel";

  /* ==========================================================
     RENDER
  ========================================================== */

  return (
    <AdminShell>
      <div className="telegram-page">

        {/* ==================================================
            HEADER
        ================================================== */}

        <div className="telegram-page-header">

          <div>

            <div className="telegram-breadcrumb">
              System / Telegram
            </div>

            <h1>
              Telegram
            </h1>

            <p>
              Manage Telegram publishing,
              channel connections, and
              signal delivery.
            </p>

          </div>

          <button
            className="telegram-primary-button"
            onClick={sendTestMessage}
            disabled={testSending}
          >
            <span className="telegram-button-icon">
              {testSending
                ? "⟳"
                : "➤"}
            </span>

            {testSending
              ? "Sending Test..."
              : "Send Test Message"}
          </button>

        </div>

        {/* ==================================================
            ERROR
        ================================================== */}

        {error && (
          <div
            style={{
              marginBottom: "18px",
              padding: "12px 15px",
              borderRadius: "12px",
              border:
                "1px solid rgba(239,68,68,.25)",
              background:
                "rgba(239,68,68,.08)",
              color: "#fca5a5",
              fontSize: "13px",
            }}
          >
            {error}
          </div>
        )}

        {/* ==================================================
            CONNECTION
        ================================================== */}

        <div className="telegram-connection-card">

          <div className="telegram-connection-main">

            <div className="telegram-logo">

              <svg
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M21.5 3.7L18.25 20.2C18 21.35 17.35 21.65 16.4 21.1L11.2 17.25L8.7 19.65C8.42 19.93 8.18 20.17 7.62 20.17L7.99 14.88L17.61 6.19C18.03 5.82 17.52 5.62 16.96 6L5.06 13.49L-0.02 11.9C-1.13 11.55-1.15 10.79 0.21 10.25L20.07 2.59C20.99 2.26 21.79 2.8 21.5 3.7Z"
                  fill="currentColor"
                />
              </svg>

            </div>

            <div className="telegram-connection-info">

              <div className="telegram-connection-title-row">

                <h2>
                  Telegram Bot
                </h2>

                <span
                  className={`telegram-online-badge ${connectionClass}`}
                >
                  <span className="telegram-status-dot" />
                  {loading
                    ? "Checking..."
                    : connectionLabel}
                </span>

              </div>

              <p>
                {telegram.connected
                  ? "Your Telegram bot is connected and ready to publish signals."
                  : "The Telegram bot connection requires attention."}
              </p>

              <div className="telegram-connection-details">

                <span>
                  <strong>
                    Bot:
                  </strong>{" "}
                  {botUsername}
                </span>

                <span>
                  <strong>
                    Channel:
                  </strong>{" "}
                  {channelUsername}
                </span>

                <span>
                  <strong>
                    Last check:
                  </strong>{" "}
                  {telegram.checked_at
                    ? formatDate(
                        telegram.checked_at,
                      )
                    : "—"}
                </span>

              </div>

            </div>

          </div>

          <button
            className="telegram-outline-button"
            onClick={() =>
              void loadTelegramData(true)
            }
            disabled={refreshing}
          >
            {refreshing
              ? "Refreshing..."
              : "Refresh"}
          </button>

        </div>

        {/* ==================================================
            STATS
        ================================================== */}

        <div className="telegram-stats-grid">

          <TelegramStat
            label="Published Today"
            value={
              loading
                ? "—"
                : statistics.published.toLocaleString()
            }
            description="Successfully published"
            icon="➤"
            type="blue"
          />

          <TelegramStat
            label="Queued"
            value={
              loading
                ? "—"
                : statistics.pending.toLocaleString()
            }
            description="Waiting to publish"
            icon="◷"
            type="orange"
          />

          <TelegramStat
            label="Failed"
            value={
              loading
                ? "—"
                : statistics.failed.toLocaleString()
            }
            description="Requires attention"
            icon="!"
            type="red"
          />

          <TelegramStat
            label="Total Published"
            value={
              loading
                ? "—"
                : statistics.total.toLocaleString()
            }
            description="All recorded messages"
            icon="✓"
            type="green"
          />

        </div>

        {/* ==================================================
            PUBLISHING SETTINGS + CHANNEL
        ================================================== */}

        <div className="telegram-section-grid">

          {/* PUBLISHING SETTINGS */}

          <div className="telegram-card">

            <div className="telegram-card-header">

              <div>

                <h2>
                  Publishing Settings
                </h2>

                <p>
                  Control how signals are
                  delivered to Telegram.
                </p>

              </div>

              <div className="telegram-card-header-icon">
                ⚙
              </div>

            </div>

            <div className="telegram-settings-list">

              {/* AUTOMATIC PUBLISHING */}

              <div className="telegram-setting-row">

                <div>

                  <strong>
                    Automatic Publishing
                  </strong>

                  <span>
                    Automatically publish confirmed
                    signals to Telegram.
                  </span>

                </div>

                <button
                  className={`telegram-switch ${
                    configuration?.automatic_publishing
                      ? "active"
                      : ""
                  }`}
                  onClick={
                    toggleAutomaticPublishing
                  }
                  disabled={
                    savingPublishing ||
                    !configuration
                  }
                  aria-label="Toggle automatic publishing"
                >
                  <span />
                </button>

              </div>

              {/* CHANNEL */}

              <div className="telegram-setting-row">

                <div>

                  <strong>
                    Default Channel
                  </strong>

                  <span>
                    Channel used for signal
                    publishing.
                  </span>

                </div>

                <div className="telegram-select-value">
                  {channelUsername}
                  <span>
                    ⌄
                  </span>
                </div>

              </div>

              {/* CONFIRMED */}

              <div className="telegram-setting-row">

                <div>

                  <strong>
                    Publish Confirmed Signals
                  </strong>

                  <span>
                    Only signals marked as
                    confirmed will be published.
                  </span>

                </div>

                <span
                  className={
                    configuration?.publish_confirmed_signals
                      ? "telegram-enabled-label"
                      : "telegram-disabled-label"
                  }
                >
                  {configuration?.publish_confirmed_signals
                    ? "Enabled"
                    : "Disabled"}
                </span>

              </div>

              {/* RESULTS */}

              <div className="telegram-setting-row">

                <div>

                  <strong>
                    Publish Results
                  </strong>

                  <span>
                    Send completed signal results
                    to Telegram.
                  </span>

                </div>

                <span
                  className={
                    configuration?.publish_results
                      ? "telegram-enabled-label"
                      : "telegram-disabled-label"
                  }
                >
                  {configuration?.publish_results
                    ? "Enabled"
                    : "Disabled"}
                </span>

              </div>

            </div>

          </div>

          {/* CHANNEL INFO */}

          <div className="telegram-card">

            <div className="telegram-card-header">

              <div>

                <h2>
                  Channel Information
                </h2>

                <p>
                  Current Telegram destination
                  details.
                </p>

              </div>

              <div className="telegram-card-header-icon">
                #
              </div>

            </div>

            <div className="telegram-channel-profile">

              <div className="telegram-channel-avatar">
                M
              </div>

              <div>

                <strong>
                  {channelName}
                </strong>

                <span>
                  {channelUsername}
                </span>

              </div>

              <span className="telegram-channel-active">
                {telegram.configured
                  ? "Active"
                  : "Not Configured"}
              </span>

            </div>

            <div className="telegram-channel-details">

              <div className="telegram-detail-item">

                <span>
                  Channel type
                </span>

                <strong>
                  Telegram Channel
                </strong>

              </div>

              <div className="telegram-detail-item">

                <span>
                  Channel ID
                </span>

                <strong>
                  {telegram.channel_id ||
                    configuration?.channel_id ||
                    "—"}
                </strong>

              </div>

              <div className="telegram-detail-item">

                <span>
                  Bot
                </span>

                <strong>
                  {botUsername}
                </strong>

              </div>

              <div className="telegram-detail-item">

                <span>
                  Publishing status
                </span>

                <strong
                  className={
                    telegram.connected
                      ? "telegram-text-success"
                      : ""
                  }
                >
                  {telegram.connected
                    ? "Operational"
                    : "Disconnected"}
                </strong>

              </div>

            </div>

          </div>

        </div>

        {/* ==================================================
            RECENT ACTIVITY
        ================================================== */}

        <div className="telegram-card telegram-activity-card">

          <div className="telegram-card-header telegram-activity-header">

            <div>

              <h2>
                Recent Telegram Activity
              </h2>

              <p>
                Signals and messages recently
                processed by the Telegram
                publisher.
              </p>

            </div>

            <button
              className="telegram-outline-button"
              onClick={() =>
                void loadTelegramData(true)
              }
            >
              {refreshing
                ? "Refreshing..."
                : "Refresh"}
            </button>

          </div>

          {/* FILTERS */}

          <div className="telegram-filters">

            <div className="telegram-search">

              <span>
                ⌕
              </span>

              <input
                type="text"
                placeholder="Search signal or message ID..."
                value={search}
                onChange={(e) =>
                  setSearch(
                    e.target.value,
                  )
                }
              />

            </div>

            <select
              value={statusFilter}
              onChange={(e) =>
                setStatusFilter(
                  e.target.value,
                )
              }
              className="telegram-filter-select"
            >

              <option value="All">
                All Status
              </option>

              <option value="Published">
                Published
              </option>

              <option value="Pending">
                Pending
              </option>

              <option value="Failed">
                Failed
              </option>

            </select>

            <button
              className="telegram-reset-button"
              onClick={() => {
                setSearch("");
                setStatusFilter("All");
              }}
            >
              Reset
            </button>

          </div>

          {/* DESKTOP TABLE */}

          <div className="telegram-table-wrapper">

            <table className="telegram-table">

              <thead>

                <tr>

                  <th>
                    Signal
                  </th>

                  <th>
                    Message ID
                  </th>

                  <th>
                    Channel
                  </th>

                  <th>
                    Status
                  </th>

                  <th>
                    Attempts
                  </th>

                  <th>
                    Published
                  </th>

                  <th />

                </tr>

              </thead>

              <tbody>

                {filteredMessages.map(
                  (message) => (
                    <tr key={message.id}>

                      <td>

                        <span className="telegram-signal-number">
                          {getSignalNumber(
                            message,
                          )}
                        </span>

                      </td>

                      <td>

                        <span className="telegram-message-id">

                          {message.telegram_message_id
                            ? `#${message.telegram_message_id}`
                            : "—"}

                        </span>

                      </td>

                      <td>

                        <span className="telegram-channel-text">
                          {getChannelUsername(
                            message,
                          )}
                        </span>

                      </td>

                      <td>

                        <TelegramStatusBadge
                          status={getStatusLabel(
                            message.status,
                          )}
                        />

                      </td>

                      <td>

                        <span className="telegram-attempts">
                          {message.attempts}
                        </span>

                      </td>

                      <td>

                        <span className="telegram-date">

                          {formatDate(
                            message.published_at,
                          )}

                        </span>

                      </td>

                      <td>

                        <button
                          className="telegram-more-button"
                          type="button"
                          onClick={() =>
                            window.location.href =
                              `/telegram/messages/${message.id}`
                          }
                          title="View message"
                        >
                          ⋮
                        </button>

                      </td>

                    </tr>
                  ),
                )}

              </tbody>

            </table>

            {loading && (
              <div className="telegram-empty-state">

                <div>
                  ⟳
                </div>

                <strong>
                  Loading Telegram activity
                </strong>

                <span>
                  Fetching live messages from
                  the Telegram service.
                </span>

              </div>
            )}

            {!loading &&
              filteredMessages.length === 0 && (
                <div className="telegram-empty-state">

                  <div>
                    ⌕
                  </div>

                  <strong>
                    No Telegram activity found
                  </strong>

                  <span>
                    Try changing your search
                    or filter.
                  </span>

                </div>
              )}

          </div>

          {/* MOBILE */}

          <div className="telegram-mobile-list">

            {filteredMessages.map(
              (message) => (
                <div
                  className="telegram-mobile-item"
                  key={message.id}
                >

                  <div className="telegram-mobile-top">

                    <div>

                      <strong>
                        {getSignalNumber(
                          message,
                        )}
                      </strong>

                      <span>
                        {message.telegram_message_id
                          ? `#${message.telegram_message_id}`
                          : "No Telegram ID"}
                      </span>

                    </div>

                    <TelegramStatusBadge
                      status={getStatusLabel(
                        message.status,
                      )}
                    />

                  </div>

                  <div className="telegram-mobile-details">

                    <div>

                      <span>
                        Channel
                      </span>

                      <strong>
                        {getChannelUsername(
                          message,
                        )}
                      </strong>

                    </div>

                    <div>

                      <span>
                        Attempts
                      </span>

                      <strong>
                        {message.attempts}
                      </strong>

                    </div>

                    <div>

                      <span>
                        Published
                      </span>

                      <strong>
                        {formatDate(
                          message.published_at,
                        )}
                      </strong>

                    </div>

                  </div>

                  <button
                    className="telegram-mobile-action"
                    type="button"
                    onClick={() =>
                      window.location.href =
                        `/telegram/messages/${message.id}`
                    }
                  >
                    View Message
                  </button>

                </div>
              ),
            )}

          </div>

          {/* PAGINATION */}

          <div className="telegram-pagination">

            <span>
              Showing{" "}
              {filteredMessages.length}{" "}
              of{" "}
              {messages.length}{" "}
              messages
            </span>

            <div>

              <button
                disabled
              >
                Previous
              </button>

              <button className="active">
                1
              </button>

              <button disabled>
                Next
              </button>

            </div>

          </div>

        </div>

      </div>
    </AdminShell>
  );
}

/* ============================================================
   STAT CARD
============================================================ */

function TelegramStat({
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
    | "orange"
    | "red"
    | "green";
}) {
  return (
    <div className="telegram-stat-card">

      <div
        className={`telegram-stat-icon ${type}`}
      >
        {icon}
      </div>

      <div className="telegram-stat-content">

        <span>
          {label}
        </span>

        <strong>
          {value}
        </strong>

        <small>
          {description}
        </small>

      </div>

    </div>
  );
}

/* ============================================================
   STATUS BADGE
============================================================ */

function TelegramStatusBadge({
  status,
}: {
  status:
    | "Published"
    | "Pending"
    | "Failed";
}) {
  return (
    <span
      className={`telegram-status-badge ${status.toLowerCase()}`}
    >

      <span />

      {status}

    </span>
  );
} 
