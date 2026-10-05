"use client";

import { useState } from "react";
import AdminShell from "@/components/layout/AdminShell";

export default function SettingsPage() {
  const [autoPublish, setAutoPublish] = useState(true);
  const [requireConfirmation, setRequireConfirmation] = useState(true);
  const [telegramNotifications, setTelegramNotifications] = useState(true);
  const [adminNotifications, setAdminNotifications] = useState(true);
  const [resultNotifications, setResultNotifications] = useState(true);
  const [darkMode, setDarkMode] = useState(false);

  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);

    setTimeout(() => {
      setSaved(false);
    }, 2500);
  };

  return (
    <AdminShell>
      <div className="settings-page">

        {/* =====================================================
            PAGE HEADER
        ====================================================== */}

        <div className="settings-header">
          <div>
            <div className="settings-breadcrumb">
              System <span>/</span> Settings
            </div>

            <h1>Settings</h1>

            <p>
              Configure signal engine behavior, Telegram publishing,
              notifications, and system preferences.
            </p>
          </div>

          <div className="settings-header-actions">
            <button
              className="settings-secondary-button"
              onClick={() => window.location.reload()}
            >
              Reset
            </button>

            <button
              className="settings-primary-button"
              onClick={handleSave}
            >
              <span>✓</span>
              Save Changes
            </button>
          </div>
        </div>

        {/* =====================================================
            SAVE MESSAGE
        ====================================================== */}

        {saved && (
          <div className="settings-save-message">
            <div className="settings-save-icon">✓</div>

            <div>
              <strong>Settings saved</strong>
              <span>Your system preferences have been updated.</span>
            </div>
          </div>
        )}

        {/* =====================================================
            SYSTEM STATUS
        ====================================================== */}

        <div className="settings-status-card">

          <div className="settings-status-left">
            <div className="settings-status-icon">
              <span />
            </div>

            <div>
              <strong>System Operational</strong>

              <p>
                Mines Signal Engine is running normally.
              </p>
            </div>
          </div>

          <div className="settings-status-items">

            <div className="settings-status-item">
              <span className="settings-status-dot online" />
              Signal Engine
            </div>

            <div className="settings-status-item">
              <span className="settings-status-dot online" />
              Telegram
            </div>

            <div className="settings-status-item">
              <span className="settings-status-dot online" />
              Database
            </div>

          </div>
        </div>

        {/* =====================================================
            SETTINGS GRID
        ====================================================== */}

        <div className="settings-grid">

          {/* ===================================================
              GENERAL SETTINGS
          ==================================================== */}

          <section className="settings-card">

            <div className="settings-card-header">
              <div className="settings-card-icon blue">
                ⚙
              </div>

              <div>
                <h2>General Settings</h2>

                <p>
                  Basic configuration for the signal system.
                </p>
              </div>
            </div>

            <div className="settings-form">

              <div className="settings-field">
                <label>System Name</label>

                <input
                  type="text"
                  defaultValue="Mines Signal System"
                />
              </div>

              <div className="settings-field">
                <label>Environment</label>

                <select defaultValue="production">
                  <option value="production">Production</option>
                  <option value="staging">Staging</option>
                  <option value="development">Development</option>
                </select>
              </div>

              <div className="settings-field">
                <label>Default Timezone</label>

                <select defaultValue="Africa/Blantyre">
                  <option value="Africa/Blantyre">
                    Africa/Blantyre
                  </option>

                  <option value="UTC">
                    UTC
                  </option>

                  <option value="Africa/Johannesburg">
                    Africa/Johannesburg
                  </option>
                </select>
              </div>

              <div className="settings-field">
                <label>Language</label>

                <select defaultValue="en">
                  <option value="en">English</option>
                </select>
              </div>

            </div>
          </section>

          {/* ===================================================
              SIGNAL ENGINE
          ==================================================== */}

          <section className="settings-card">

            <div className="settings-card-header">

              <div className="settings-card-icon purple">
                ✦
              </div>

              <div>
                <h2>Signal Engine</h2>

                <p>
                  Control how signals are analyzed and generated.
                </p>
              </div>

            </div>

            <div className="settings-form">

              <div className="settings-field">
                <label>Default Model</label>

                <select defaultValue="v2.1.0">
                  <option value="v2.1.0">
                    v2.1.0 — Production
                  </option>

                  <option value="v2.0.0">
                    v2.0.0 — Archived
                  </option>

                  <option value="v2.2.0-beta">
                    v2.2.0-beta — Experimental
                  </option>
                </select>
              </div>

              <div className="settings-field">
                <label>Default Board Size</label>

                <select defaultValue="5x5">
                  <option value="5x5">5 × 5</option>
                </select>
              </div>

              <div className="settings-field">
                <label>Default Mine Count</label>

                <select defaultValue="3">
                  <option value="3">3 Mines</option>
                  <option value="5">5 Mines</option>
                  <option value="7">7 Mines</option>
                </select>
              </div>

              <div className="settings-field">
                <label>Maximum Attempts</label>

                <select defaultValue="3">
                  <option value="1">1 Attempt</option>
                  <option value="2">2 Attempts</option>
                  <option value="3">3 Attempts</option>
                  <option value="4">4 Attempts</option>
                  <option value="5">5 Attempts</option>
                </select>
              </div>

            </div>

            <div className="settings-divider" />

            <SettingToggle
              title="Require Signal Confirmation"
              description="Require an administrator to confirm a generated signal before publishing."
              enabled={requireConfirmation}
              onChange={setRequireConfirmation}
            />

          </section>

          {/* ===================================================
              TELEGRAM
          ==================================================== */}

          <section className="settings-card">

            <div className="settings-card-header">

              <div className="settings-card-icon telegram">
                ➤
              </div>

              <div>
                <h2>Telegram Publishing</h2>

                <p>
                  Configure automatic signal distribution.
                </p>
              </div>

            </div>

            <div className="telegram-connection">

              <div className="telegram-connection-icon">
                ➤
              </div>

              <div className="telegram-connection-info">
                <strong>Telegram Connected</strong>

                <span>
                  Bot connection is active
                </span>
              </div>

              <span className="settings-connected-badge">
                Connected
              </span>

            </div>

            <div className="settings-form">

              <div className="settings-field">
                <label>Bot Name</label>

                <input
                  type="text"
                  defaultValue="Mines Signal Bot"
                />
              </div>

              <div className="settings-field">
                <label>Channel</label>

                <input
                  type="text"
                  defaultValue="@mines_signals"
                />
              </div>

              <div className="settings-field full">
                <label>Publishing Template</label>

                <textarea
                  rows={5}
                  defaultValue={`👑 ENTRY CONFIRMED 👑

👇 Model Confidence 👇
🟩🟩🟩🟩🟩🟩🟩🟩🟩⬜️ {{confidence}}%

{{board}}

💣: {{mine_count}} mines
♻️: {{attempts}} ATTEMPTS`}
                />
              </div>

            </div>

            <div className="settings-divider" />

            <SettingToggle
              title="Automatic Publishing"
              description="Automatically publish confirmed signals to the configured Telegram channel."
              enabled={autoPublish}
              onChange={setAutoPublish}
            />

          </section>

          {/* ===================================================
              SIGNAL DEFAULTS
          ==================================================== */}

          <section className="settings-card">

            <div className="settings-card-header">

              <div className="settings-card-icon green">
                ✓
              </div>

              <div>
                <h2>Signal Defaults</h2>

                <p>
                  Default behavior for newly created signals.
                </p>
              </div>

            </div>

            <div className="settings-option-list">

              <SettingOption
                title="Signal Status"
                description="Initial status assigned to new signals."
                value="Draft"
              />

              <SettingOption
                title="Prediction Output"
                description="The primary prediction returned by the engine."
                value="Safe Positions"
              />

              <SettingOption
                title="Confidence Display"
                description="How model confidence is displayed in the admin panel."
                value="Percentage"
              />

              <SettingOption
                title="Board Representation"
                description="Visual format used for signal boards."
                value="5 × 5 Grid"
              />

            </div>

          </section>

          {/* ===================================================
              NOTIFICATIONS
          ==================================================== */}

          <section className="settings-card">

            <div className="settings-card-header">

              <div className="settings-card-icon orange">
                🔔
              </div>

              <div>
                <h2>Notifications</h2>

                <p>
                  Control administrative system notifications.
                </p>
              </div>

            </div>

            <div className="settings-toggle-list">

              <SettingToggle
                title="Telegram Notifications"
                description="Receive notifications when signals are published."
                enabled={telegramNotifications}
                onChange={setTelegramNotifications}
              />

              <SettingToggle
                title="Admin Notifications"
                description="Receive notifications about important system events."
                enabled={adminNotifications}
                onChange={setAdminNotifications}
              />

              <SettingToggle
                title="Result Notifications"
                description="Receive notifications when signal outcomes are recorded."
                enabled={resultNotifications}
                onChange={setResultNotifications}
              />

            </div>

          </section>

          {/* ===================================================
              SECURITY
          ==================================================== */}

          <section className="settings-card">

            <div className="settings-card-header">

              <div className="settings-card-icon red">
                🔒
              </div>

              <div>
                <h2>Security & Preferences</h2>

                <p>
                  Manage administrator security and interface preferences.
                </p>
              </div>

            </div>

            <div className="settings-security-list">

              <div className="settings-security-row">

                <div>
                  <strong>Administrator Password</strong>

                  <span>
                    Last changed 14 days ago
                  </span>
                </div>

                <button className="settings-outline-button">
                  Change Password
                </button>

              </div>

              <div className="settings-security-row">

                <div>
                  <strong>Two-Factor Authentication</strong>

                  <span>
                    Additional protection for administrator accounts
                  </span>
                </div>

                <span className="settings-enabled-badge">
                  Enabled
                </span>

              </div>

              <div className="settings-security-row">

                <div>
                  <strong>Interface Theme</strong>

                  <span>
                    Choose the preferred admin interface theme
                  </span>
                </div>

                <select
                  className="settings-small-select"
                  value={darkMode ? "dark" : "light"}
                  onChange={(e) =>
                    setDarkMode(e.target.value === "dark")
                  }
                >
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                </select>

              </div>

            </div>

          </section>

        </div>

        {/* =====================================================
            SYSTEM INFORMATION
        ====================================================== */}

        <section className="settings-card settings-system-card">

          <div className="settings-card-header">

            <div className="settings-card-icon gray">
              ⓘ
            </div>

            <div>
              <h2>System Information</h2>

              <p>
                Current Mines Signal System environment information.
              </p>
            </div>

          </div>

          <div className="system-info-grid">

            <SystemInfo
              label="Application"
              value="Mines Signal System"
            />

            <SystemInfo
              label="Version"
              value="1.0.0"
            />

            <SystemInfo
              label="Signal Engine"
              value="v2.1.0"
            />

            <SystemInfo
              label="Environment"
              value="Production"
            />

            <SystemInfo
              label="Database"
              value="PostgreSQL"
            />

            <SystemInfo
              label="Telegram"
              value="Connected"
            />

          </div>

        </section>

        {/* =====================================================
            BOTTOM ACTIONS
        ====================================================== */}

        <div className="settings-bottom-actions">

          <div>
            <strong>Unsaved changes?</strong>

            <span>
              Save your changes before leaving this page.
            </span>
          </div>

          <div className="settings-bottom-buttons">

            <button
              className="settings-secondary-button"
              onClick={() => window.location.reload()}
            >
              Cancel
            </button>

            <button
              className="settings-primary-button"
              onClick={handleSave}
            >
              Save Changes
            </button>

          </div>

        </div>

      </div>
    </AdminShell>
  );
}

/* ============================================================
   TOGGLE
============================================================ */

function SettingToggle({
  title,
  description,
  enabled,
  onChange,
}: {
  title: string;
  description: string;
  enabled: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <div className="settings-toggle-row">

      <div>
        <strong>{title}</strong>

        <span>{description}</span>
      </div>

      <button
        type="button"
        className={`settings-toggle ${
          enabled ? "active" : ""
        }`}
        onClick={() => onChange(!enabled)}
        aria-label={title}
      >
        <span />
      </button>

    </div>
  );
}

/* ============================================================
   OPTION
============================================================ */

function SettingOption({
  title,
  description,
  value,
}: {
  title: string;
  description: string;
  value: string;
}) {
  return (
    <div className="settings-option-row">

      <div>
        <strong>{title}</strong>

        <span>{description}</span>
      </div>

      <span className="settings-value-badge">
        {value}
      </span>

    </div>
  );
}

/* ============================================================
   SYSTEM INFO
============================================================ */

function SystemInfo({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="system-info-item">

      <span>{label}</span>

      <strong>{value}</strong>

    </div>
  );
}