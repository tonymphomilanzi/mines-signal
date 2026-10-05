"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import AdminShell from "@/components/layout/AdminShell";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type AutoPost = {
  id: string;
  title: string;
  content_type: string;
  status: string;
  is_active: boolean;
  scheduled_at: string | null;
  published_at: string | null;
  telegram_message_id: number | null;
  channel_id: string | null;
  channel_username: string | null;
  attempts: number;
  error_message: string | null;
  created_at: string;
};

function statusClasses(status: string) {
  switch (status) {
    case "PUBLISHED":
      return "bg-green-50 text-green-700 border-green-200";

    case "FAILED":
      return "bg-red-50 text-red-700 border-red-200";

    case "CANCELLED":
      return "bg-gray-100 text-gray-600 border-gray-200";

    case "PUBLISHING":
      return "bg-amber-50 text-amber-700 border-amber-200";

    case "QUEUED":
      return "bg-blue-50 text-blue-700 border-blue-200";

    default:
      return "bg-gray-50 text-gray-600 border-gray-200";
  }
}

function formatDate(value: string | null) {
  if (!value) return "—";

  return new Date(value).toLocaleString();
}

function contentTypeLabel(type: string) {
  switch (type) {
    case "MESSAGE":
      return "Message";
    case "LINK":
      return "Link";
    case "VIDEO":
      return "Video";
    case "IMAGE":
      return "Image";
    default:
      return type;
  }
}

export default function AutoPublisherHistoryPage() {
  const [posts, setPosts] = useState<AutoPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [statusFilter, setStatusFilter] =
    useState("ALL");

  const [typeFilter, setTypeFilter] =
    useState("ALL");

  async function loadHistory() {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `${API_URL}/api/telegram/auto-posts`,
        {
          credentials: "include",
          cache: "no-store",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Unable to load publishing history."
        );
      }

      const items = Array.isArray(data)
        ? data
        : data.items || data.data || [];

      setPosts(items);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load publishing history."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadHistory();
  }, []);

  const history = useMemo(() => {
    return posts.filter((post) => {
      const statusMatches =
        statusFilter === "ALL" ||
        post.status === statusFilter;

      const typeMatches =
        typeFilter === "ALL" ||
        post.content_type === typeFilter;

      return statusMatches && typeMatches;
    });
  }, [posts, statusFilter, typeFilter]);

  const publishedCount = posts.filter(
    (post) => post.status === "PUBLISHED"
  ).length;

  const failedCount = posts.filter(
    (post) => post.status === "FAILED"
  ).length;

  const cancelledCount = posts.filter(
    (post) => post.status === "CANCELLED"
  ).length;

  async function retryPost(postId: string) {
    setError("");

    try {
      const response = await fetch(
        `${API_URL}/api/telegram/auto-posts/${postId}/retry`,
        {
          method: "POST",
          credentials: "include",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Unable to retry this post."
        );
      }

      await loadHistory();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to retry this post."
      );
    }
  }

  return (
    <AdminShell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <Link
                href="/telegram/auto-publisher"
                className="hover:text-gray-900"
              >
                Auto Publisher
              </Link>

              <span>/</span>

              <span className="text-gray-900">
                History
              </span>
            </div>

            <h1 className="mt-2 text-2xl font-semibold text-gray-900">
              Publishing History
            </h1>

            <p className="mt-1 text-sm text-gray-500">
              Review the publishing activity and delivery
              results of your Auto Publisher posts.
            </p>
          </div>

          <button
            onClick={loadHistory}
            disabled={loading}
            className="rounded-lg border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            Refresh
          </button>
        </div>

        {/* Summary cards */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="rounded-xl border border-gray-200 bg-white p-5">
            <p className="text-sm text-gray-500">
              Published
            </p>

            <p className="mt-2 text-2xl font-semibold text-gray-900">
              {publishedCount}
            </p>

            <p className="mt-1 text-xs text-gray-400">
              Successfully delivered
            </p>
          </div>

          <div className="rounded-xl border border-gray-200 bg-white p-5">
            <p className="text-sm text-gray-500">
              Failed
            </p>

            <p className="mt-2 text-2xl font-semibold text-gray-900">
              {failedCount}
            </p>

            <p className="mt-1 text-xs text-gray-400">
              Require attention
            </p>
          </div>

          <div className="rounded-xl border border-gray-200 bg-white p-5">
            <p className="text-sm text-gray-500">
              Cancelled
            </p>

            <p className="mt-2 text-2xl font-semibold text-gray-900">
              {cancelledCount}
            </p>

            <p className="mt-1 text-xs text-gray-400">
              Removed from publishing
            </p>
          </div>
        </div>

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Filters */}
        <div className="rounded-xl border border-gray-200 bg-white p-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h2 className="text-base font-semibold text-gray-900">
                Activity
              </h2>

              <p className="mt-1 text-sm text-gray-500">
                Filter publishing activity by status and
                content type.
              </p>
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1.5 block text-xs font-medium text-gray-500">
                  Status
                </label>

                <select
                  value={statusFilter}
                  onChange={(e) =>
                    setStatusFilter(e.target.value)
                  }
                  className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 outline-none focus:border-gray-400 focus:ring-2 focus:ring-gray-100"
                >
                  <option value="ALL">All statuses</option>
                  <option value="PUBLISHED">
                    Published
                  </option>
                  <option value="FAILED">
                    Failed
                  </option>
                  <option value="CANCELLED">
                    Cancelled
                  </option>
                  <option value="QUEUED">
                    Queued
                  </option>
                  <option value="PUBLISHING">
                    Publishing
                  </option>
                </select>
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-medium text-gray-500">
                  Content Type
                </label>

                <select
                  value={typeFilter}
                  onChange={(e) =>
                    setTypeFilter(e.target.value)
                  }
                  className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 outline-none focus:border-gray-400 focus:ring-2 focus:ring-gray-100"
                >
                  <option value="ALL">
                    All content
                  </option>
                  <option value="MESSAGE">
                    Message
                  </option>
                  <option value="LINK">
                    Link
                  </option>
                  <option value="VIDEO">
                    Video
                  </option>
                  <option value="IMAGE">
                    Image
                  </option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* History table */}
        <div className="rounded-xl border border-gray-200 bg-white">
          <div className="flex items-center justify-between border-b border-gray-100 px-6 py-5">
            <div>
              <h2 className="text-base font-semibold text-gray-900">
                Publishing Activity
              </h2>

              <p className="mt-1 text-sm text-gray-500">
                {history.length} matching records
              </p>
            </div>
          </div>

          {loading ? (
            <div className="px-6 py-16 text-center text-sm text-gray-500">
              Loading publishing history...
            </div>
          ) : history.length === 0 ? (
            <div className="px-6 py-16 text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-gray-100">
                <span className="text-lg text-gray-500">
                  ▣
                </span>
              </div>

              <h3 className="mt-4 text-sm font-semibold text-gray-900">
                No publishing activity
              </h3>

              <p className="mt-1 text-sm text-gray-500">
                No records match the selected filters.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50/70">
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Post
                    </th>

                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Type
                    </th>

                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Status
                    </th>

                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Published
                    </th>

                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Telegram ID
                    </th>

                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Attempts
                    </th>

                    <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Action
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {history.map((post) => (
                    <tr
                      key={post.id}
                      className="border-b border-gray-100 last:border-0 hover:bg-gray-50/50"
                    >
                      <td className="px-6 py-4">
                        <Link
                          href={`/telegram/auto-publisher/${post.id}`}
                          className="font-medium text-gray-900 hover:text-gray-600"
                        >
                          {post.title}
                        </Link>

                        {post.error_message && (
                          <p className="mt-1 max-w-xs truncate text-xs text-red-500">
                            {post.error_message}
                          </p>
                        )}
                      </td>

                      <td className="px-6 py-4 text-sm text-gray-600">
                        {contentTypeLabel(
                          post.content_type
                        )}
                      </td>

                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-medium ${statusClasses(
                            post.status
                          )}`}
                        >
                          {post.status}
                        </span>
                      </td>

                      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                        {formatDate(
                          post.published_at
                        )}
                      </td>

                      <td className="px-6 py-4 text-sm text-gray-500">
                        {post.telegram_message_id ??
                          "—"}
                      </td>

                      <td className="px-6 py-4 text-sm text-gray-600">
                        {post.attempts}
                      </td>

                      <td className="px-6 py-4 text-right">
                        {post.status === "FAILED" ? (
                          <button
                            onClick={() =>
                              retryPost(post.id)
                            }
                            className="rounded-lg bg-gray-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-gray-800"
                          >
                            Retry
                          </button>
                        ) : (
                          <Link
                            href={`/telegram/auto-publisher/${post.id}`}
                            className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50"
                          >
                            View
                          </Link>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </AdminShell>
  );
}
 
