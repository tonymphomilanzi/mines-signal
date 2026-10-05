"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import AdminShell from "@/components/layout/AdminShell";

/* ============================================================
   API CONFIGURATION
============================================================ */

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";


/* ============================================================
   TYPES
============================================================ */

type AdminRole =
  | "SUPER ADMINISTRATOR"
  | "ADMINISTRATOR"
  | "MODERATOR"
  | "SUPPORT";

type BackendAdminRole =
  | "SUPER_ADMINISTRATOR"
  | "ADMINISTRATOR"
  | "MODERATOR"
  | "SUPPORT";

type AdminStatus =
  | "ACTIVE"
  | "INACTIVE"
  | "PENDING";


type BackendAdministrator = {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  role: BackendAdminRole;
  status: AdminStatus;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
  updated_at: string;
};


type AdministratorsResponse = {
  items: BackendAdministrator[];
  total: number;
};


type Administrator = {
  id: string;
  name: string;
  email: string;
  initials: string;
  role: AdminRole;
  status: AdminStatus;
  lastLogin: string;
  createdAt: string;
};


/* ============================================================
   HELPERS
============================================================ */

function getInitials(
  firstName: string,
  lastName: string
): string {
  const first =
    firstName?.trim().charAt(0) || "";

  const last =
    lastName?.trim().charAt(0) || "";

  return `${first}${last}`.toUpperCase();
}


function convertRole(
  role: BackendAdminRole
): AdminRole {
  switch (role) {
    case "SUPER_ADMINISTRATOR":
      return "SUPER ADMINISTRATOR";

    case "ADMINISTRATOR":
      return "ADMINISTRATOR";

    case "MODERATOR":
      return "MODERATOR";

    case "SUPPORT":
      return "SUPPORT";

    default:
      return "ADMINISTRATOR";
  }
}


function formatLastLogin(
  value: string | null
): string {
  if (!value) {
    return "Never";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Never";
  }

  const now = new Date();

  const isToday =
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate();

  const yesterday = new Date(now);

  yesterday.setDate(
    yesterday.getDate() - 1
  );

  const isYesterday =
    date.getFullYear() ===
      yesterday.getFullYear() &&
    date.getMonth() ===
      yesterday.getMonth() &&
    date.getDate() ===
      yesterday.getDate();

  const time = date.toLocaleTimeString(
    undefined,
    {
      hour: "2-digit",
      minute: "2-digit",
    }
  );

  if (isToday) {
    return `Today, ${time}`;
  }

  if (isYesterday) {
    return `Yesterday, ${time}`;
  }

  return `${date.toLocaleDateString(
    undefined,
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
    }
  )}, ${time}`;
}


function formatCreatedDate(
  value: string
): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "-";
  }

  return date.toLocaleDateString(
    undefined,
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
    }
  );
}


function convertAdministrator(
  admin: BackendAdministrator
): Administrator {
  return {
    id: admin.id,

    name: `${admin.first_name} ${admin.last_name}`,

    email: admin.email,

    initials: getInitials(
      admin.first_name,
      admin.last_name
    ),

    role: convertRole(admin.role),

    status: admin.status,

    lastLogin: formatLastLogin(
      admin.last_login_at
    ),

    createdAt: formatCreatedDate(
      admin.created_at
    ),
  };
}


/* ============================================================
   PAGE
============================================================ */

export default function AdministratorsPage() {
  const router = useRouter();


  /* ============================================================
     FILTER STATE
  ============================================================ */

  const [search, setSearch] = useState("");

  const [roleFilter, setRoleFilter] =
    useState("ALL");

  const [statusFilter, setStatusFilter] =
    useState("ALL");

  const [page, setPage] = useState(1);


  /* ============================================================
     DATA STATE
  ============================================================ */

  const [administrators, setAdministrators] =
    useState<Administrator[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [actionLoading, setActionLoading] =
    useState<string | null>(null);


  /* ============================================================
     LOAD ADMINISTRATORS
  ============================================================ */

  const loadAdministrators =
    async () => {
      try {
        setLoading(true);
        setError("");

        const endpoint =
          `${API_URL}/api/administrators`;

        console.log(
          "Loading administrators from:",
          endpoint
        );

        const response =
          await fetch(endpoint, {
            method: "GET",

            headers: {
              Accept: "application/json",
            },

            cache: "no-store",
          });


        if (!response.ok) {
          let message =
            `Request failed with status ${response.status}`;

          try {
            const data =
              await response.json();

            if (data?.detail) {
              message = data.detail;
            }
          } catch {
            // Ignore JSON parsing errors.
          }

          throw new Error(message);
        }


        const data: AdministratorsResponse =
          await response.json();


        if (
          !data ||
          !Array.isArray(data.items)
        ) {
          throw new Error(
            "The API returned an invalid administrators response."
          );
        }


        const converted =
          data.items.map(
            convertAdministrator
          );


        setAdministrators(converted);

      } catch (err) {
        console.error(
          "Failed to load administrators:",
          err
        );


        if (
          err instanceof TypeError &&
          err.message === "Failed to fetch"
        ) {
          setError(
            "Unable to connect to the API server. Make sure FastAPI is running on http://127.0.0.1:8000."
          );
        } else {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load administrators."
          );
        }

      } finally {
        setLoading(false);
      }
    };


  /* ============================================================
     INITIAL LOAD
  ============================================================ */

  useEffect(() => {
    void loadAdministrators();
  }, []);


  /* ============================================================
     FILTERED ADMINISTRATORS
  ============================================================ */

  const filteredAdmins =
    useMemo(() => {
      return administrators.filter(
        (admin) => {
          const searchValue =
            search.toLowerCase().trim();

          const matchesSearch =
            admin.name
              .toLowerCase()
              .includes(searchValue) ||
            admin.email
              .toLowerCase()
              .includes(searchValue);


          const matchesRole =
            roleFilter === "ALL" ||
            admin.role === roleFilter;


          const matchesStatus =
            statusFilter === "ALL" ||
            admin.status === statusFilter;


          return (
            matchesSearch &&
            matchesRole &&
            matchesStatus
          );
        }
      );
    }, [
      administrators,
      search,
      roleFilter,
      statusFilter,
    ]);


  /* ============================================================
     RESET FILTERS
  ============================================================ */

  const resetFilters = () => {
    setSearch("");
    setRoleFilter("ALL");
    setStatusFilter("ALL");
    setPage(1);
  };


  /* ============================================================
     SUMMARY
  ============================================================ */

  const activeAdmins =
    administrators.filter(
      (admin) =>
        admin.status === "ACTIVE"
    ).length;


  const superAdmins =
    administrators.filter(
      (admin) =>
        admin.role ===
        "SUPER ADMINISTRATOR"
    ).length;


  const pendingAdmins =
    administrators.filter(
      (admin) =>
        admin.status === "PENDING"
    ).length;


  /* ============================================================
     ACTIVATE ADMINISTRATOR
  ============================================================ */

  const activateAdmin =
    async (
      id: string
    ) => {
      try {
        setActionLoading(id);

        const response =
          await fetch(
            `${API_URL}/api/administrators/${id}/activate`,
            {
              method: "PATCH",

              headers: {
                Accept:
                  "application/json",
              },
            }
          );


        if (!response.ok) {
          let message =
            "Failed to activate administrator.";

          try {
            const data =
              await response.json();

            if (data?.detail) {
              message = data.detail;
            }
          } catch {
            // Ignore parsing error.
          }

          throw new Error(message);
        }


        await loadAdministrators();

      } catch (err) {
        console.error(
          "Failed to activate administrator:",
          err
        );

        window.alert(
          err instanceof Error
            ? err.message
            : "Failed to activate administrator."
        );

      } finally {
        setActionLoading(null);
      }
    };


  /* ============================================================
     DEACTIVATE ADMINISTRATOR
  ============================================================ */

  const deactivateAdmin =
    async (
      id: string
    ) => {
      try {
        setActionLoading(id);

        const response =
          await fetch(
            `${API_URL}/api/administrators/${id}/deactivate`,
            {
              method: "PATCH",

              headers: {
                Accept:
                  "application/json",
              },
            }
          );


        if (!response.ok) {
          let message =
            "Failed to deactivate administrator.";

          try {
            const data =
              await response.json();

            if (data?.detail) {
              message = data.detail;
            }
          } catch {
            // Ignore parsing error.
          }

          throw new Error(message);
        }


        await loadAdministrators();

      } catch (err) {
        console.error(
          "Failed to deactivate administrator:",
          err
        );

        window.alert(
          err instanceof Error
            ? err.message
            : "Failed to deactivate administrator."
        );

      } finally {
        setActionLoading(null);
      }
    };


  /* ============================================================
     DELETE ADMINISTRATOR
  ============================================================ */

  const deleteAdmin =
    async (
      id: string,
      name: string
    ) => {
      const confirmed =
        window.confirm(
          `Are you sure you want to delete ${name}?`
        );


      if (!confirmed) {
        return;
      }


      try {
        setActionLoading(id);

        const response =
          await fetch(
            `${API_URL}/api/administrators/${id}`,
            {
              method: "DELETE",

              headers: {
                Accept:
                  "application/json",
              },
            }
          );


        if (!response.ok) {
          let message =
            "Failed to delete administrator.";

          try {
            const data =
              await response.json();

            if (data?.detail) {
              message = data.detail;
            }
          } catch {
            // Ignore parsing error.
          }

          throw new Error(message);
        }


        await loadAdministrators();

      } catch (err) {
        console.error(
          "Failed to delete administrator:",
          err
        );

        window.alert(
          err instanceof Error
            ? err.message
            : "Failed to delete administrator."
        );

      } finally {
        setActionLoading(null);
      }
    };


  /* ============================================================
     ACTION MENU
  ============================================================ */

  const handleAdminAction =
    (
      admin: Administrator
    ) => {
      if (
        actionLoading === admin.id
      ) {
        return;
      }


      let action = "";


      if (
        admin.status === "ACTIVE"
      ) {
        action =
          window.prompt(
            `Choose action for ${admin.name}:\n\n1 - Deactivate\n2 - Delete`
          ) || "";
      } else {
        action =
          window.prompt(
            `Choose action for ${admin.name}:\n\n1 - Activate\n2 - Delete`
          ) || "";
      }


      if (
        admin.status === "ACTIVE"
      ) {
        if (action === "1") {
          void deactivateAdmin(
            admin.id
          );
        }

        if (action === "2") {
          void deleteAdmin(
            admin.id,
            admin.name
          );
        }

        return;
      }


      if (action === "1") {
        void activateAdmin(
          admin.id
        );
      }


      if (action === "2") {
        void deleteAdmin(
          admin.id,
          admin.name
        );
      }
    };


  /* ============================================================
     CREATE ADMINISTRATOR
  ============================================================ */

  const handleCreateAdministrator =
    () => {
      router.push(
        "/adminstrators/create"
      );
    };


  /* ============================================================
     BUILD
  ============================================================ */

  return (
    <AdminShell>

      <div className="administrators-page">

        {/* =====================================================
            HEADER
        ====================================================== */}

        <div className="administrators-header">

          <div>

            <div className="administrators-breadcrumb">
              System <span>/</span>{" "}
              Administrators
            </div>

            <h1>
              Administrators
            </h1>

            <p>
              Manage administrator accounts,
              roles, and system access.
            </p>

          </div>


          <button
            className="administrators-primary-button"
            onClick={
              handleCreateAdministrator
            }
          >
            <span>+</span>
            Create Administrator
          </button>

        </div>


        {/* =====================================================
            SUMMARY CARDS
        ====================================================== */}

        <div className="administrators-stats">

          <AdminStat
            label="Total Administrators"
            value={
              administrators.length.toString()
            }
            icon="👥"
            tone="blue"
          />


          <AdminStat
            label="Active"
            value={
              activeAdmins.toString()
            }
            icon="✓"
            tone="green"
          />


          <AdminStat
            label="Super Administrators"
            value={
              superAdmins.toString()
            }
            icon="★"
            tone="purple"
          />


          <AdminStat
            label="Pending"
            value={
              pendingAdmins.toString()
            }
            icon="!"
            tone="orange"
          />

        </div>


        {/* =====================================================
            MAIN CARD
        ====================================================== */}

        <section className="administrators-card">

          <div className="administrators-card-header">

            <div>

              <h2>
                Administrator Accounts
              </h2>

              <p>
                View and manage users with
                administrative access.
              </p>

            </div>


            <div className="administrators-count">
              {filteredAdmins.length} accounts
            </div>

          </div>


          {/* =================================================
              FILTERS
          ================================================== */}

          <div className="administrators-filters">

            <div className="administrators-search">

              <span>
                ⌕
              </span>

              <input
                type="text"
                placeholder="Search administrators..."
                value={search}
                onChange={(e) => {
                  setSearch(
                    e.target.value
                  );

                  setPage(1);
                }}
              />

            </div>


            <select
              value={roleFilter}
              onChange={(e) => {
                setRoleFilter(
                  e.target.value
                );

                setPage(1);
              }}
            >

              <option value="ALL">
                All Roles
              </option>

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


            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(
                  e.target.value
                );

                setPage(1);
              }}
            >

              <option value="ALL">
                All Statuses
              </option>

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


            <button
              className="administrators-reset"
              onClick={
                resetFilters
              }
            >
              Reset
            </button>

          </div>


          {/* =================================================
              ERROR
          ================================================== */}

          {error && (
            <div
              style={{
                margin:
                  "0 20px 16px",
                padding:
                  "12px 16px",
                borderRadius:
                  "10px",
                background:
                  "#FEF2F2",
                color:
                  "#B91C1C",
                fontSize:
                  "13px",
              }}
            >
              {error}
            </div>
          )}


          {/* =================================================
              DESKTOP TABLE
          ================================================== */}

          {!loading && (
            <div className="administrators-table-wrapper">

              <table className="administrators-table">

                <thead>

                  <tr>

                    <th>
                      Administrator
                    </th>

                    <th>
                      Role
                    </th>

                    <th>
                      Status
                    </th>

                    <th>
                      Last Login
                    </th>

                    <th>
                      Created
                    </th>

                    <th></th>

                  </tr>

                </thead>


                <tbody>

                  {filteredAdmins.map(
                    (admin) => (
                      <tr
                        key={admin.id}
                      >

                        <td>

                          <div className="administrator-user">

                            <div className="administrator-avatar">
                              {admin.initials}
                            </div>

                            <div>

                              <strong>
                                {admin.name}
                              </strong>

                              <span>
                                {admin.email}
                              </span>

                            </div>

                          </div>

                        </td>


                        <td>

                          <RoleBadge
                            role={
                              admin.role
                            }
                          />

                        </td>


                        <td>

                          <StatusBadge
                            status={
                              admin.status
                            }
                          />

                        </td>


                        <td>

                          <span className="administrator-last-login">
                            {
                              admin.lastLogin
                            }
                          </span>

                        </td>


                        <td>

                          <span className="administrator-date">
                            {
                              admin.createdAt
                            }
                          </span>

                        </td>


                        <td>

                          <button
                            className="administrator-more"
                            onClick={() =>
                              handleAdminAction(
                                admin
                              )
                            }
                            disabled={
                              actionLoading ===
                              admin.id
                            }
                          >
                            ⋮
                          </button>

                        </td>

                      </tr>
                    )
                  )}

                </tbody>

              </table>

            </div>
          )}


          {/* =================================================
              MOBILE LIST
          ================================================== */}

          {!loading && (
            <div className="administrators-mobile-list">

              {filteredAdmins.map(
                (admin) => (
                  <div
                    className="administrator-mobile-card"
                    key={admin.id}
                  >

                    <div className="administrator-mobile-top">

                      <div className="administrator-user">

                        <div className="administrator-avatar">
                          {admin.initials}
                        </div>

                        <div>

                          <strong>
                            {admin.name}
                          </strong>

                          <span>
                            {admin.email}
                          </span>

                        </div>

                      </div>


                      <button
                        className="administrator-more"
                        onClick={() =>
                          handleAdminAction(
                            admin
                          )
                        }
                        disabled={
                          actionLoading ===
                          admin.id
                        }
                      >
                        ⋮
                      </button>

                    </div>


                    <div className="administrator-mobile-meta">

                      <RoleBadge
                        role={
                          admin.role
                        }
                      />

                      <StatusBadge
                        status={
                          admin.status
                        }
                      />

                    </div>


                    <div className="administrator-mobile-info">

                      <div>

                        <span>
                          Last Login
                        </span>

                        <strong>
                          {
                            admin.lastLogin
                          }
                        </strong>

                      </div>


                      <div>

                        <span>
                          Created
                        </span>

                        <strong>
                          {
                            admin.createdAt
                          }
                        </strong>

                      </div>

                    </div>

                  </div>
                )
              )}

            </div>
          )}


          {/* =================================================
              LOADING
          ================================================== */}

          {loading && (
            <div
              style={{
                padding:
                  "60px 20px",
                textAlign:
                  "center",
                color:
                  "#6B7785",
                fontSize:
                  "14px",
              }}
            >
              Loading administrators...
            </div>
          )}


          {/* =================================================
              EMPTY
          ================================================== */}

          {!loading &&
            filteredAdmins.length === 0 && (
              <div className="administrators-empty">

                <div>
                  ⌕
                </div>

                <h3>
                  No administrators found
                </h3>

                <p>
                  Try adjusting your
                  search or filter
                  options.
                </p>

                <button
                  onClick={
                    resetFilters
                  }
                >
                  Clear Filters
                </button>

              </div>
            )}


          {/* =================================================
              PAGINATION
          ================================================== */}

          {!loading &&
            filteredAdmins.length > 0 && (
              <div className="administrators-pagination">

                <span>
                  Showing{" "}
                  <strong>
                    1
                  </strong>
                  –{" "}
                  <strong>
                    {
                      filteredAdmins.length
                    }
                  </strong>{" "}
                  of{" "}
                  <strong>
                    {
                      filteredAdmins.length
                    }
                  </strong>
                </span>


                <div className="administrator-pagination-buttons">

                  <button
                    disabled={
                      page === 1
                    }
                    onClick={() =>
                      setPage(
                        Math.max(
                          1,
                          page - 1
                        )
                      )
                    }
                  >
                    ‹
                  </button>


                  <button className="active">
                    1
                  </button>


                  <button disabled>
                    ›
                  </button>

                </div>

              </div>
            )}

        </section>

      </div>

    </AdminShell>
  );
}


/* ============================================================
   ADMIN STAT
============================================================ */

function AdminStat({
  label,
  value,
  icon,
  tone,
}: {
  label: string;
  value: string;
  icon: string;
  tone:
    | "blue"
    | "green"
    | "purple"
    | "orange";
}) {
  return (
    <div className="administrator-stat">

      <div
        className={`administrator-stat-icon ${tone}`}
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


/* ============================================================
   ROLE BADGE
============================================================ */

function RoleBadge({
  role,
}: {
  role: AdminRole;
}) {
  const className =
    role
      .toLowerCase()
      .replaceAll(
        " ",
        "-"
      );

  return (
    <span
      className={`administrator-role-badge ${className}`}
    >
      {role}
    </span>
  );
}


/* ============================================================
   STATUS BADGE
============================================================ */

function StatusBadge({
  status,
}: {
  status: AdminStatus;
}) {
  return (
    <span
      className={`administrator-status-badge ${status.toLowerCase()}`}
    >
      <i />
      {status}
    </span>
  );
}