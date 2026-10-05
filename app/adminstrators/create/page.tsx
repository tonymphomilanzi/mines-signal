"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import AdminShell from "@/components/layout/AdminShell";

export default function CreateAdministratorPage() {
  const router = useRouter();

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] =
    useState(false);

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("ADMINISTRATOR");
  const [status, setStatus] = useState("ACTIVE");

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [permissions, setPermissions] = useState({
    dashboard: true,
    signals: true,
    telegram: true,
    results: true,
    models: false,
    performance: false,
    administrators: false,
    settings: false,
  });

  // Backend submission state.
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const togglePermission = (
    permission: keyof typeof permissions
  ) => {
    setPermissions((current) => ({
      ...current,
      [permission]: !current[permission],
    }));
  };

  const handleCreate = async () => {
    if (isSubmitting) return;

    setErrorMessage("");

    // -----------------------------------------
    // FRONTEND VALIDATION
    // -----------------------------------------

    if (!firstName.trim()) {
      setErrorMessage("First name is required.");
      return;
    }

    if (!lastName.trim()) {
      setErrorMessage("Last name is required.");
      return;
    }

    if (!email.trim()) {
      setErrorMessage("Email address is required.");
      return;
    }

    if (!password) {
      setErrorMessage("Password is required.");
      return;
    }

    if (password.length < 8) {
      setErrorMessage(
        "Password must be at least 8 characters."
      );
      return;
    }

    if (password !== confirmPassword) {
      setErrorMessage("Passwords do not match.");
      return;
    }

    // -----------------------------------------
    // ROLE CONVERSION
    // -----------------------------------------

    const apiRole =
      role === "SUPER ADMINISTRATOR"
        ? "SUPER_ADMINISTRATOR"
        : role;

    setIsSubmitting(true);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/administrators",
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify({
            first_name: firstName.trim(),
            last_name: lastName.trim(),
            email: email.trim(),
            role: apiRole,
            status,
            password,
            confirm_password: confirmPassword,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Failed to create administrator."
        );
      }

      // Administrator successfully created.
      router.push("/adminstrators");
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Something went wrong while creating the administrator."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AdminShell>
      <div className="create-administrator-page">

        {/* =====================================================
            HEADER
        ====================================================== */}

        <div className="create-administrator-header">

          <div>

            <div className="create-administrator-breadcrumb">
              System
              <span>/</span>
              Administrators
              <span>/</span>
              Create
            </div>

            <h1>Create Administrator</h1>

            <p>
              Create a new administrator account and configure
              system permissions.
            </p>

          </div>

          <button
            className="create-administrator-back"
            onClick={() => router.push("/administrators")}
          >
            ← Back to Administrators
          </button>

        </div>

        {/* =====================================================
            MAIN GRID
        ====================================================== */}

        <div className="create-administrator-grid">

          {/* ===================================================
              ACCOUNT INFORMATION
          ==================================================== */}

          <div className="create-administrator-main">

            <section className="create-administrator-card">

              <div className="create-card-header">

                <div className="create-card-icon blue">
                  👤
                </div>

                <div>
                  <h2>Account Information</h2>

                  <p>
                    Enter the administrator's basic account details.
                  </p>
                </div>

              </div>

              <div className="create-form-grid">

                <div className="create-field">

                  <label>
                    First Name <span>*</span>
                  </label>

                  <input
                    type="text"
                    placeholder="e.g. Winkford"
                    value={firstName}
                    onChange={(e) =>
                      setFirstName(e.target.value)
                    }
                  />

                </div>

                <div className="create-field">

                  <label>
                    Last Name <span>*</span>
                  </label>

                  <input
                    type="text"
                    placeholder="e.g. Mboma"
                    value={lastName}
                    onChange={(e) =>
                      setLastName(e.target.value)
                    }
                  />

                </div>

                <div className="create-field full">

                  <label>
                    Email Address <span>*</span>
                  </label>

                  <input
                    type="email"
                    placeholder="administrator@example.com"
                    value={email}
                    onChange={(e) =>
                      setEmail(e.target.value)
                    }
                  />

                  <small>
                    This email will be used to sign in to the
                    administrator panel.
                  </small>

                </div>

                <div className="create-field">

                  <label>
                    Administrator Role <span>*</span>
                  </label>

                  <select
                    value={role}
                    onChange={(e) =>
                      setRole(e.target.value)
                    }
                  >
                    <option value="SUPER ADMINISTRATOR">
                      Super Administrator
                    </option>

                    <option value="ADMINISTRATOR">
                      Administrator
                    </option>

                    <option value="MODERATOR">
                      Moderator
                    </option>

                    <option value="SUPPORT">
                      Support
                    </option>
                  </select>

                </div>

                <div className="create-field">

                  <label>
                    Account Status
                  </label>

                  <select
                    value={status}
                    onChange={(e) =>
                      setStatus(e.target.value)
                    }
                  >
                    <option value="ACTIVE">
                      Active
                    </option>

                    <option value="INACTIVE">
                      Inactive
                    </option>

                    <option value="PENDING">
                      Pending
                    </option>
                  </select>

                </div>

              </div>

            </section>

            {/* =================================================
                PASSWORD
            ================================================== */}

            <section className="create-administrator-card">

              <div className="create-card-header">

                <div className="create-card-icon purple">
                  🔒
                </div>

                <div>
                  <h2>Security</h2>

                  <p>
                    Set the initial password for this account.
                  </p>
                </div>

              </div>

              <div className="create-form-grid">

                <div className="create-field">

                  <label>
                    Password <span>*</span>
                  </label>

                  <div className="password-field">

                    <input
                      type={
                        showPassword
                          ? "text"
                          : "password"
                      }
                      placeholder="Enter password"
                      value={password}
                      onChange={(e) =>
                        setPassword(e.target.value)
                      }
                    />

                    <button
                      type="button"
                      onClick={() =>
                        setShowPassword(!showPassword)
                      }
                    >
                      {showPassword ? "Hide" : "Show"}
                    </button>

                  </div>

                  <small>
                    Use at least 8 characters with a mix of
                    letters and numbers.
                  </small>

                </div>

                <div className="create-field">

                  <label>
                    Confirm Password <span>*</span>
                  </label>

                  <div className="password-field">

                    <input
                      type={
                        showConfirmPassword
                          ? "text"
                          : "password"
                      }
                      placeholder="Confirm password"
                      value={confirmPassword}
                      onChange={(e) =>
                        setConfirmPassword(e.target.value)
                      }
                    />

                    <button
                      type="button"
                      onClick={() =>
                        setShowConfirmPassword(
                          !showConfirmPassword
                        )
                      }
                    >
                      {showConfirmPassword
                        ? "Hide"
                        : "Show"}
                    </button>

                  </div>

                </div>

              </div>

              <div className="password-strength">

                <div className="password-strength-header">

                  <span>Password Strength</span>

                  <strong>
                    {password.length >= 8
                      ? "Good"
                      : "Not set"}
                  </strong>

                </div>

                <div className="password-strength-bar">

                  <span
                    className={
                      password.length >= 8
                        ? "good"
                        : ""
                    }
                  />

                </div>

              </div>

            </section>

            {/* =================================================
                PERMISSIONS
            ================================================== */}

            <section className="create-administrator-card">

              <div className="create-card-header">

                <div className="create-card-icon green">
                  ✓
                </div>

                <div>
                  <h2>Permissions</h2>

                  <p>
                    Select which areas of the admin panel this
                    administrator can access.
                  </p>
                </div>

              </div>

              <div className="permissions-grid">

                <Permission
                  title="Dashboard"
                  description="View system overview and statistics."
                  enabled={permissions.dashboard}
                  onChange={() =>
                    togglePermission("dashboard")
                  }
                />

                <Permission
                  title="Signals"
                  description="Create and manage signals."
                  enabled={permissions.signals}
                  onChange={() =>
                    togglePermission("signals")
                  }
                />

                <Permission
                  title="Telegram"
                  description="Manage Telegram publishing."
                  enabled={permissions.telegram}
                  onChange={() =>
                    togglePermission("telegram")
                  }
                />

                <Permission
                  title="Signal Results"
                  description="Record and review signal outcomes."
                  enabled={permissions.results}
                  onChange={() =>
                    togglePermission("results")
                  }
                />

                <Permission
                  title="Models"
                  description="Manage signal engine models."
                  enabled={permissions.models}
                  onChange={() =>
                    togglePermission("models")
                  }
                />

                <Permission
                  title="Performance"
                  description="View system performance analytics."
                  enabled={permissions.performance}
                  onChange={() =>
                    togglePermission("performance")
                  }
                />

                <Permission
                  title="Administrators"
                  description="Manage administrator accounts."
                  enabled={permissions.administrators}
                  onChange={() =>
                    togglePermission("administrators")
                  }
                />

                <Permission
                  title="Settings"
                  description="Manage system configuration."
                  enabled={permissions.settings}
                  onChange={() =>
                    togglePermission("settings")
                  }
                />

              </div>

            </section>

          </div>

          {/* ===================================================
              PREVIEW
          ==================================================== */}

          <aside className="create-administrator-sidebar">

            <section className="administrator-preview-card">

              <div className="preview-label">
                ACCOUNT PREVIEW
              </div>

              <div className="preview-avatar">

                {firstName || lastName
                  ? `${firstName.charAt(0)}${lastName.charAt(
                      0
                    )}`.toUpperCase()
                  : "AD"}

              </div>

              <h3>

                {firstName || lastName
                  ? `${firstName} ${lastName}`.trim()
                  : "New Administrator"}

              </h3>

              <p>
                {email || "administrator@example.com"}
              </p>

              <div className="preview-role">
                {role}
              </div>

              <div className="preview-status">
                <span />
                {status}
              </div>

              <div className="preview-divider" />

              <div className="preview-details">

                <div>
                  <span>Access</span>

                  <strong>
                    {
                      Object.values(permissions).filter(
                        Boolean
                      ).length
                    } modules
                  </strong>
                </div>

                <div>
                  <span>2FA</span>
                  <strong>Enabled</strong>
                </div>

                <div>
                  <span>Account Type</span>
                  <strong>Administrator</strong>
                </div>

              </div>

            </section>

            <section className="administrator-notice">

              <div>ⓘ</div>

              <p>
                Administrator accounts provide access to
                sensitive system functions. Only grant
                permissions required for the administrator's
                role.
              </p>

            </section>

          </aside>

        </div>

        {/* =====================================================
            ERROR MESSAGE
        ====================================================== */}

        {errorMessage && (
          <div
            style={{
              marginTop: "18px",
              padding: "12px 16px",
              borderRadius: "10px",
              background: "#FEF2F2",
              border: "1px solid #FECACA",
              color: "#B91C1C",
              fontSize: "14px",
            }}
          >
            {errorMessage}
          </div>
        )}

        {/* =====================================================
            ACTIONS
        ====================================================== */}

        <div className="create-administrator-actions">

          <button
            className="create-cancel-button"
            onClick={() =>
              router.push("/administrators")
            }
            disabled={isSubmitting}
          >
            Cancel
          </button>

          <button
            className="create-submit-button"
            onClick={handleCreate}
            disabled={isSubmitting}
          >
            {isSubmitting
              ? "Creating..."
              : "Create Administrator"}
          </button>

        </div>

      </div>
    </AdminShell>
  );
}

/* ============================================================
   PERMISSION
============================================================ */

function Permission({
  title,
  description,
  enabled,
  onChange,
}: {
  title: string;
  description: string;
  enabled: boolean;
  onChange: () => void;
}) {
  return (
    <button
      type="button"
      className={`permission-item ${
        enabled ? "active" : ""
      }`}
      onClick={onChange}
    >

      <div className="permission-check">
        {enabled ? "✓" : ""}
      </div>

      <div>
        <strong>{title}</strong>
        <span>{description}</span>
      </div>

    </button>
  );
}