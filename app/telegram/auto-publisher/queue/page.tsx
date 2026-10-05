"use client";

import { useEffect, useState } from "react";
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
  attempts: number;
  error_message: string | null;
  created_at: string;
};

function statusClasses(status: string) {
  switch (status) {
    case "QUEUED":
      return "bg-blue-50 text-blue-700 border-blue-200";

    case "PUBLISHING":
      return "bg-amber-50 text-amber-700 border-amber-200";

    case "PUBLISHED":
      return "bg-green-50 text-green-700 border-green-200";

    case "FAILED":
      return "bg-red-50 text-red-700 border-red-200";

    case "CANCELLED":
      return "bg-gray-100 text-gray-600 border-gray-200";

    case "DRAFT":
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

export default function AutoPublisherQueuePage() {
  const [posts, setPosts] = useState<AutoPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionId, setActionId] = useState<string | null>(
    null
  );

  async function loadQueue() {
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
          data?.detail || "Unable to load the queue."
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
          : "Unable to load the queue."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadQueue();
  }, []);

  async function performAction(
    postId: string,
    action: "queue" | "cancel" | "retry"
  ) {
    setActionId(postId);
    setError("");

    try {
      const response = await fetch(
        `${API_URL}/api/telegram/auto-posts/${postId}/${action}`,
        {
          method: "POST",
          credentials: "include",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            `Unable to ${action} this post.`
        );
      }

      await loadQueue();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : `Unable to ${action} this post.`
      );
    } finally {
      setActionId(null);
    }
  }

  const queuePosts = posts.filter(
    (post) =>
      post.status === "QUEUED" ||
      post.status === "PUBLISHING" ||
      post.status === "FAILED" ||
      post.status === "DRAFT"
  );

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
                Queue
              </span>
            </div>

            <h1 className="mt-2 text-2xl font-semibold text-gray-900">
              Publishing Queue
            </h1>

            <p className="mt-1 text-sm text-gray-500">
              Manage posts waiting to be processed by the
              Telegram Auto Publisher.
            </p>
          </div>

          <div className="flex gap-3">
            <button
              onClick={loadQueue}
              disabled={loading}
              className="rounded-lg border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              Refresh
            </button>

            <Link
              href="/telegram/auto-publisher/create"
              className="rounded-lg bg-gray-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-gray-800"
            >
              + Create Post
            </Link>
          </div>
        </div>

        {/* Summary */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {[
            {
              label: "Queued",
              value: posts.filter(
                (p) => p.status === "QUEUED"
              ).length,
            },
            {
              label: "Publishing",
              value: posts.filter(
                (p) => p.status === "PUBLISHING"
              ).length,
            },
            {
              label: "Failed",
              value: posts.filter(
                (p) => p.status === "FAILED"
              ).length,
            },
          ].map((item) => (
            <div
              key={item.label}
              className="rounded-xl border border-gray-200 bg-white p-5"
            >
              <p className="text-sm text-gray-500">
                {item.label}
              </p>

              <p className="mt-2 text-2xl font-semibold text-gray-900">
                {item.value}
              </p>
            </div>
          ))}
        </div>

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Queue table */}
        <div className="rounded-xl border border-gray-200 bg-white">
          <div className="flex flex-col gap-3 border-b border-gray-100 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-base font-semibold text-gray-900">
                Current Queue
              </h2>

              <p className="mt-1 text-sm text-gray-500">
                Posts currently available for publishing.
              </p>
            </div>

            <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600">
              {queuePosts.length} posts
            </span>
          </div>

          {loading ? (
            <div className="px-6 py-16 text-center text-sm text-gray-500">
              Loading publishing queue...
            </div>
          ) : queuePosts.length === 0 ? (
            <div className="px-6 py-16 text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-gray-100 text-xl">
                ✓
              </div>

              <h3 className="mt-4 text-sm font-semibold text-gray-900">
                Queue is empty
              </h3>

              <p className="mt-1 text-sm text-gray-500">
                There are no posts waiting for publishing.
              </p>

              <Link
                href="/telegram/auto-publisher/create"
                className="mt-5 inline-flex rounded-lg bg-gray-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-gray-800"
              >
                Create Auto Post
              </Link>
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
                      Scheduled
                    </th>

                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Attempts
                    </th>

                    <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Actions
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {queuePosts.map((post) => (
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
                          post.scheduled_at
                        )}
                      </td>

                      <td className="px-6 py-4 text-sm text-gray-600">
                        {post.attempts}
                      </td>

                      <td className="px-6 py-4">
                        <div className="flex justify-end gap-2">
                          {post.status === "DRAFT" && (
                            <button
                              onClick={() =>
                                performAction(
                                  post.id,
                                  "queue"
                                )
                              }
                              disabled={
                                actionId === post.id
                              }
                              className="rounded-lg bg-gray-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-gray-800 disabled:opacity-50"
                            >
                              Queue
                            </button>
                          )}

                          {post.status === "FAILED" && (
                            <button
                              onClick={() =>
                                performAction(
                                  post.id,
                                  "retry"
                                )
                              }
                              disabled={
                                actionId === post.id
                              }
                              className="rounded-lg bg-gray-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-gray-800 disabled:opacity-50"
                            >
                              Retry
                            </button>
                          )}

                          {(post.status === "QUEUED" ||
                            post.status === "FAILED" ||
                            post.status === "DRAFT") && (
                            <button
                              onClick={() =>
                                performAction(
                                  post.id,
                                  "cancel"
                                )
                              }
                              disabled={
                                actionId === post.id
                              }
                              className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-50"
                            >
                              Cancel
                            </button>
                          )}
                        </div>
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
 
