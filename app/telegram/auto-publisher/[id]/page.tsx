"use client";

import { FormEvent, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

import AdminShell from "@/components/layout/AdminShell";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

type ContentType =
  | "MESSAGE"
  | "LINK"
  | "VIDEO"
  | "IMAGE";

type AutoPost = {
  id: string;
  title: string;
  content_type: ContentType;

  message: string | null;
  link_url: string | null;
  media_url: string | null;
  caption: string | null;

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
  updated_at: string;
};

function statusClasses(status: string) {
  switch (status) {
    case "PUBLISHED":
      return "border-green-200 bg-green-50 text-green-700";

    case "PUBLISHING":
      return "border-amber-200 bg-amber-50 text-amber-700";

    case "QUEUED":
      return "border-blue-200 bg-blue-50 text-blue-700";

    case "FAILED":
      return "border-red-200 bg-red-50 text-red-700";

    case "CANCELLED":
      return "border-gray-200 bg-gray-100 text-gray-600";

    case "DRAFT":
    default:
      return "border-gray-200 bg-gray-50 text-gray-600";
  }
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

function formatDate(value: string | null) {
  if (!value) {
    return "—";
  }

  return new Date(value).toLocaleString();
}

function toDateTimeLocal(
  value: string | null
) {
  if (!value) {
    return "";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  const year = date.getFullYear();
  const month = String(
    date.getMonth() + 1
  ).padStart(2, "0");
  const day = String(
    date.getDate()
  ).padStart(2, "0");
  const hours = String(
    date.getHours()
  ).padStart(2, "0");
  const minutes = String(
    date.getMinutes()
  ).padStart(2, "0");

  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

export default function AutoPublisherPostDetailsPage() {
  const params = useParams();
  const router = useRouter();

  const postId = params?.id as string;

  const [post, setPost] =
    useState<AutoPost | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [saving, setSaving] =
    useState(false);

  const [actionLoading, setActionLoading] =
    useState(false);

  const [deleting, setDeleting] =
    useState(false);

  const [error, setError] =
    useState("");

  const [success, setSuccess] =
    useState("");

  // ------------------------------------------------------------
  // FORM STATE
  // ------------------------------------------------------------

  const [title, setTitle] =
    useState("");

  const [contentType, setContentType] =
    useState<ContentType>("MESSAGE");

  const [message, setMessage] =
    useState("");

  const [linkUrl, setLinkUrl] =
    useState("");

  const [mediaUrl, setMediaUrl] =
    useState("");

  const [caption, setCaption] =
    useState("");

  const [isActive, setIsActive] =
    useState(true);

  const [scheduleEnabled, setScheduleEnabled] =
    useState(false);

  const [scheduledAt, setScheduledAt] =
    useState("");

  // ------------------------------------------------------------
  // LOAD POST
  // ------------------------------------------------------------

  async function loadPost() {
    if (!postId) {
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `${API_URL}/api/telegram/auto-posts/${postId}`,
        {
          method: "GET",
          credentials: "include",
          cache: "no-store",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Unable to load the auto post."
        );
      }

      setPost(data);

      setTitle(data.title || "");

      setContentType(
        data.content_type || "MESSAGE"
      );

      setMessage(data.message || "");

      setLinkUrl(data.link_url || "");

      setMediaUrl(data.media_url || "");

      setCaption(data.caption || "");

      setIsActive(
        data.is_active ?? true
      );

      setScheduleEnabled(
        Boolean(data.scheduled_at)
      );

      setScheduledAt(
        toDateTimeLocal(
          data.scheduled_at
        )
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load the auto post."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPost();
  }, [postId]);

  // ------------------------------------------------------------
  // PERMISSIONS
  // ------------------------------------------------------------

  const isPublished =
    post?.status === "PUBLISHED";

  const isPublishing =
    post?.status === "PUBLISHING";

  const canEdit =
    Boolean(post) &&
    post?.status !== "PUBLISHED";

  const canDelete =
    Boolean(post) &&
    post?.status !== "PUBLISHED";

  // ------------------------------------------------------------
  // UPDATE
  // ------------------------------------------------------------

  async function handleSave(
    event: FormEvent
  ) {
    event.preventDefault();

    if (!post || !canEdit) {
      return;
    }

    setError("");
    setSuccess("");

    if (!title.trim()) {
      setError(
        "Please enter a post title."
      );
      return;
    }

    if (
      contentType === "MESSAGE" &&
      !message.trim()
    ) {
      setError(
        "Please enter the message content."
      );
      return;
    }

    if (
      contentType === "LINK" &&
      !linkUrl.trim()
    ) {
      setError(
        "Please enter the link URL."
      );
      return;
    }

    if (
      (contentType === "VIDEO" ||
        contentType === "IMAGE") &&
      !mediaUrl.trim()
    ) {
      setError(
        "Please enter the media URL."
      );
      return;
    }

    setSaving(true);

    try {
      const payload = {
        title: title.trim(),

        content_type: contentType,

        message:
          contentType === "MESSAGE"
            ? message.trim()
            : null,

        link_url:
          contentType === "LINK"
            ? linkUrl.trim()
            : null,

        media_url:
          contentType === "VIDEO" ||
          contentType === "IMAGE"
            ? mediaUrl.trim()
            : null,

        caption:
          contentType === "VIDEO" ||
          contentType === "IMAGE"
            ? caption.trim() || null
            : null,

        is_active: isActive,

        scheduled_at:
          scheduleEnabled &&
          scheduledAt
            ? new Date(
                scheduledAt
              ).toISOString()
            : null,
      };

      const response = await fetch(
        `${API_URL}/api/telegram/auto-posts/${post.id}`,
        {
          method: "PATCH",
          credentials: "include",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify(payload),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Unable to update the auto post."
        );
      }

      setPost(data);

      setSuccess(
        "Auto post updated successfully."
      );

      setTimeout(() => {
        setSuccess("");
      }, 4000);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to update the auto post."
      );
    } finally {
      setSaving(false);
    }
  }

  // ------------------------------------------------------------
  // ACTIONS
  // ------------------------------------------------------------

  async function performAction(
    action:
      | "queue"
      | "cancel"
      | "retry"
  ) {
    if (!post) {
      return;
    }

    setError("");
    setSuccess("");
    setActionLoading(true);

    try {
      const response = await fetch(
        `${API_URL}/api/telegram/auto-posts/${post.id}/${action}`,
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

      setPost(data);

      setSuccess(
        action === "queue"
          ? "Post queued successfully."
          : action === "retry"
          ? "Post queued for retry."
          : "Post cancelled successfully."
      );

      await loadPost();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : `Unable to ${action} this post.`
      );
    } finally {
      setActionLoading(false);
    }
  }

  // ------------------------------------------------------------
  // DELETE
  // ------------------------------------------------------------

  async function handleDelete() {
    if (!post || !canDelete) {
      return;
    }

    const confirmed =
      window.confirm(
        `Delete "${post.title}"?\n\nThis action cannot be undone.`
      );

    if (!confirmed) {
      return;
    }

    setDeleting(true);
    setError("");

    try {
      const response = await fetch(
        `${API_URL}/api/telegram/auto-posts/${post.id}`,
        {
          method: "DELETE",
          credentials: "include",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Unable to delete the auto post."
        );
      }

      router.push(
        "/telegram/auto-publisher"
      );
      router.refresh();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to delete the auto post."
      );
    } finally {
      setDeleting(false);
    }
  }

  // ------------------------------------------------------------
  // LOADING
  // ------------------------------------------------------------

  if (loading) {
    return (
      <AdminShell>
        <div className="space-y-6">
          <div>
            <div className="h-4 w-40 animate-pulse rounded bg-gray-100" />

            <div className="mt-3 h-8 w-64 animate-pulse rounded bg-gray-100" />

            <div className="mt-2 h-4 w-96 max-w-full animate-pulse rounded bg-gray-100" />
          </div>

          <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
            <div className="h-96 animate-pulse rounded-xl border border-gray-200 bg-white xl:col-span-2" />

            <div className="h-96 animate-pulse rounded-xl border border-gray-200 bg-white" />
          </div>
        </div>
      </AdminShell>
    );
  }

  // ------------------------------------------------------------
  // ERROR / NOT FOUND
  // ------------------------------------------------------------

  if (!post) {
    return (
      <AdminShell>
        <div className="space-y-6">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">
              Auto Post
            </h1>

            <p className="mt-1 text-sm text-gray-500">
              Unable to load this Auto Publisher post.
            </p>
          </div>

          <div className="rounded-xl border border-red-200 bg-red-50 p-6">
            <p className="text-sm text-red-700">
              {error ||
                "The requested post could not be found."}
            </p>

            <Link
              href="/telegram/auto-publisher"
              className="mt-5 inline-flex rounded-lg bg-gray-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-gray-800"
            >
              Back to Auto Publisher
            </Link>
          </div>
        </div>
      </AdminShell>
    );
  }

  // ------------------------------------------------------------
  // PAGE
  // ------------------------------------------------------------

  return (
    <AdminShell>
      <div className="space-y-6">
        {/* ---------------------------------------------------- */}
        {/* HEADER */}
        {/* ---------------------------------------------------- */}

        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2 text-sm text-gray-500">
              <Link
                href="/telegram/auto-publisher"
                className="hover:text-gray-900"
              >
                Auto Publisher
              </Link>

              <span>/</span>

              <span className="text-gray-900">
                {post.title}
              </span>
            </div>

            <div className="mt-2 flex flex-wrap items-center gap-3">
              <h1 className="text-2xl font-semibold text-gray-900">
                {post.title}
              </h1>

              <span
                className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-medium ${statusClasses(
                  post.status
                )}`}
              >
                {post.status}
              </span>
            </div>

            <p className="mt-1 text-sm text-gray-500">
              Manage the content, scheduling and publishing
              status of this Auto Publisher post.
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <Link
              href="/telegram/auto-publisher/queue"
              className="rounded-lg border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Queue
            </Link>

            <Link
              href="/telegram/auto-publisher/history"
              className="rounded-lg border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              History
            </Link>

            <Link
              href="/telegram/auto-publisher"
              className="rounded-lg border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Back
            </Link>
          </div>
        </div>

        {/* ---------------------------------------------------- */}
        {/* ALERTS */}
        {/* ---------------------------------------------------- */}

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {success && (
          <div className="rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
            {success}
          </div>
        )}

        {/* ---------------------------------------------------- */}
        {/* PUBLISHED NOTICE */}
        {/* ---------------------------------------------------- */}

        {isPublished && (
          <div className="rounded-xl border border-blue-200 bg-blue-50 px-4 py-4">
            <div className="flex gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-100 text-sm text-blue-700">
                i
              </div>

              <div>
                <p className="text-sm font-semibold text-blue-900">
                  This post has already been published
                </p>

                <p className="mt-1 text-sm leading-5 text-blue-700">
                  Published posts are read-only. Telegram
                  delivery information is shown below for
                  reference.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* ---------------------------------------------------- */}
        {/* MAIN CONTENT */}
        {/* ---------------------------------------------------- */}

        <form
          onSubmit={handleSave}
          className="grid grid-cols-1 gap-6 xl:grid-cols-3"
        >
          {/* ================================================== */}
          {/* LEFT */}
          {/* ================================================== */}

          <div className="space-y-6 xl:col-span-2">
            {/* Content */}
            <div className="rounded-xl border border-gray-200 bg-white">
              <div className="border-b border-gray-100 px-6 py-5">
                <h2 className="text-base font-semibold text-gray-900">
                  Post Content
                </h2>

                <p className="mt-1 text-sm text-gray-500">
                  Review or edit the content configured for
                  this post.
                </p>
              </div>

              <div className="space-y-5 p-6">
                {/* Title */}
                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    Post Title
                  </label>

                  <input
                    type="text"
                    value={title}
                    disabled={!canEdit}
                    onChange={(event) =>
                      setTitle(
                        event.target.value
                      )
                    }
                    className="w-full rounded-lg border border-gray-200 bg-white px-3.5 py-2.5 text-sm text-gray-900 outline-none transition placeholder:text-gray-400 focus:border-gray-400 focus:ring-2 focus:ring-gray-100 disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-500"
                  />
                </div>

                {/* Content type */}
                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    Content Type
                  </label>

                  <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                    {[
                      {
                        value: "MESSAGE",
                        label: "Message",
                        icon: "💬",
                      },
                      {
                        value: "LINK",
                        label: "Link",
                        icon: "🔗",
                      },
                      {
                        value: "VIDEO",
                        label: "Video",
                        icon: "▶",
                      },
                      {
                        value: "IMAGE",
                        label: "Image",
                        icon: "▧",
                      },
                    ].map((item) => {
                      const selected =
                        contentType ===
                        item.value;

                      return (
                        <button
                          key={item.value}
                          type="button"
                          disabled={!canEdit}
                          onClick={() =>
                            setContentType(
                              item.value as ContentType
                            )
                          }
                          className={`rounded-lg border px-3 py-3 text-left transition disabled:cursor-not-allowed ${
                            selected
                              ? "border-gray-900 bg-gray-50"
                              : "border-gray-200 bg-white hover:bg-gray-50 disabled:hover:bg-white"
                          }`}
                        >
                          <div className="text-lg">
                            {item.icon}
                          </div>

                          <div
                            className={`mt-1 text-sm font-medium ${
                              selected
                                ? "text-gray-900"
                                : "text-gray-600"
                            }`}
                          >
                            {item.label}
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Message */}
                {contentType === "MESSAGE" && (
                  <div>
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      Message
                    </label>

                    <textarea
                      value={message}
                      disabled={!canEdit}
                      onChange={(event) =>
                        setMessage(
                          event.target.value
                        )
                      }
                      rows={10}
                      className="w-full resize-y rounded-lg border border-gray-200 bg-white px-3.5 py-3 text-sm leading-6 text-gray-900 outline-none transition focus:border-gray-400 focus:ring-2 focus:ring-gray-100 disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-500"
                    />
                  </div>
                )}

                {/* Link */}
                {contentType === "LINK" && (
                  <div>
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      Link URL
                    </label>

                    <input
                      type="url"
                      value={linkUrl}
                      disabled={!canEdit}
                      onChange={(event) =>
                        setLinkUrl(
                          event.target.value
                        )
                      }
                      className="w-full rounded-lg border border-gray-200 bg-white px-3.5 py-2.5 text-sm text-gray-900 outline-none transition focus:border-gray-400 focus:ring-2 focus:ring-gray-100 disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-500"
                    />
                  </div>
                )}

                {/* Media */}
                {(contentType === "VIDEO" ||
                  contentType === "IMAGE") && (
                  <>
                    <div>
                      <label className="mb-2 block text-sm font-medium text-gray-700">
                        {contentType ===
                        "VIDEO"
                          ? "Video URL"
                          : "Image URL"}
                      </label>

                      <input
                        type="url"
                        value={mediaUrl}
                        disabled={!canEdit}
                        onChange={(event) =>
                          setMediaUrl(
                            event.target.value
                          )
                        }
                        className="w-full rounded-lg border border-gray-200 bg-white px-3.5 py-2.5 text-sm text-gray-900 outline-none transition focus:border-gray-400 focus:ring-2 focus:ring-gray-100 disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-500"
                      />
                    </div>

                    <div>
                      <label className="mb-2 block text-sm font-medium text-gray-700">
                        Caption
                      </label>

                      <textarea
                        value={caption}
                        disabled={!canEdit}
                        onChange={(event) =>
                          setCaption(
                            event.target.value
                          )
                        }
                        rows={6}
                        className="w-full resize-y rounded-lg border border-gray-200 bg-white px-3.5 py-3 text-sm leading-6 text-gray-900 outline-none transition focus:border-gray-400 focus:ring-2 focus:ring-gray-100 disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-500"
                      />
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Scheduling */}
            <div className="rounded-xl border border-gray-200 bg-white">
              <div className="border-b border-gray-100 px-6 py-5">
                <h2 className="text-base font-semibold text-gray-900">
                  Scheduling
                </h2>

                <p className="mt-1 text-sm text-gray-500">
                  Control when this post becomes eligible for
                  automatic publishing.
                </p>
              </div>

              <div className="p-6">
                <label className="flex cursor-pointer items-start gap-3">
                  <input
                    type="checkbox"
                    checked={scheduleEnabled}
                    disabled={!canEdit}
                    onChange={(event) =>
                      setScheduleEnabled(
                        event.target.checked
                      )
                    }
                    className="mt-1 h-4 w-4 rounded border-gray-300 disabled:cursor-not-allowed"
                  />

                  <span>
                    <span className="block text-sm font-medium text-gray-800">
                      Schedule this post
                    </span>

                    <span className="mt-1 block text-xs leading-5 text-gray-500">
                      Set a specific date and time for the
                      post to become eligible for publishing.
                    </span>
                  </span>
                </label>

                {scheduleEnabled && (
                  <div className="mt-5">
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      Scheduled Date & Time
                    </label>

                    <input
                      type="datetime-local"
                      value={scheduledAt}
                      disabled={!canEdit}
                      onChange={(event) =>
                        setScheduledAt(
                          event.target.value
                        )
                      }
                      className="w-full max-w-md rounded-lg border border-gray-200 bg-white px-3.5 py-2.5 text-sm text-gray-900 outline-none focus:border-gray-400 focus:ring-2 focus:ring-gray-100 disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-500"
                    />
                  </div>
                )}

                {!scheduleEnabled && (
                  <div className="mt-5 rounded-lg bg-gray-50 px-4 py-3">
                    <p className="text-xs leading-5 text-gray-500">
                      No specific schedule is configured.
                      Queueing the post will make it eligible
                      for the next available publishing cycle.
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Save actions */}
            {canEdit && (
              <div className="flex flex-col-reverse gap-3 border-t border-gray-200 pt-5 sm:flex-row sm:justify-end">
                <Link
                  href="/telegram/auto-publisher"
                  className="inline-flex items-center justify-center rounded-lg border border-gray-200 bg-white px-5 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </Link>

                <button
                  type="submit"
                  disabled={saving}
                  className="inline-flex items-center justify-center rounded-lg bg-gray-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {saving
                    ? "Saving..."
                    : "Save Changes"}
                </button>
              </div>
            )}
          </div>

          {/* ================================================== */}
          {/* RIGHT */}
          {/* ================================================== */}

          <div className="space-y-6">
            {/* Publishing Settings */}
            <div className="rounded-xl border border-gray-200 bg-white">
              <div className="border-b border-gray-100 px-6 py-5">
                <h2 className="text-base font-semibold text-gray-900">
                  Publishing Settings
                </h2>
              </div>

              <div className="space-y-5 p-6">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-medium text-gray-800">
                      Active Post
                    </p>

                    <p className="mt-1 text-xs leading-5 text-gray-500">
                      Active posts can be queued and processed
                      by the Auto Publisher.
                    </p>
                  </div>

                  <button
                    type="button"
                    disabled={!canEdit}
                    onClick={() =>
                      setIsActive(
                        !isActive
                      )
                    }
                    className={`relative mt-0.5 h-6 w-11 shrink-0 rounded-full transition disabled:cursor-not-allowed disabled:opacity-60 ${
                      isActive
                        ? "bg-gray-900"
                        : "bg-gray-200"
                    }`}
                  >
                    <span
                      className={`absolute top-1 h-4 w-4 rounded-full bg-white transition ${
                        isActive
                          ? "left-6"
                          : "left-1"
                      }`}
                    />
                  </button>
                </div>

                <div className="border-t border-gray-100 pt-5">
                  <p className="text-xs font-medium uppercase tracking-wide text-gray-400">
                    Current Status
                  </p>

                  <div className="mt-2">
                    <span
                      className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-medium ${statusClasses(
                        post.status
                      )}`}
                    >
                      {post.status}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="rounded-xl border border-gray-200 bg-white">
              <div className="border-b border-gray-100 px-6 py-5">
                <h2 className="text-base font-semibold text-gray-900">
                  Publishing Actions
                </h2>

                <p className="mt-1 text-sm text-gray-500">
                  Manage the post lifecycle.
                </p>
              </div>

              <div className="space-y-3 p-6">
                {post.status === "DRAFT" && (
                  <button
                    type="button"
                    disabled={
                      actionLoading ||
                      !post.is_active
                    }
                    onClick={() =>
                      performAction("queue")
                    }
                    className="w-full rounded-lg bg-gray-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {actionLoading
                      ? "Processing..."
                      : "Queue for Publishing"}
                  </button>
                )}

                {post.status === "FAILED" && (
                  <button
                    type="button"
                    disabled={
                      actionLoading ||
                      !post.is_active
                    }
                    onClick={() =>
                      performAction("retry")
                    }
                    className="w-full rounded-lg bg-gray-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {actionLoading
                      ? "Processing..."
                      : "Retry Publishing"}
                  </button>
                )}

                {(post.status === "QUEUED" ||
                  post.status === "FAILED" ||
                  post.status === "DRAFT") && (
                  <button
                    type="button"
                    disabled={actionLoading}
                    onClick={() =>
                      performAction("cancel")
                    }
                    className="w-full rounded-lg border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Cancel Post
                  </button>
                )}

                {post.status ===
                  "PUBLISHING" && (
                  <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3">
                    <p className="text-sm font-medium text-amber-800">
                      Publishing in progress
                    </p>

                    <p className="mt-1 text-xs leading-5 text-amber-700">
                      The worker is currently processing this
                      post. Actions are temporarily limited.
                    </p>
                  </div>
                )}

                {post.status ===
                  "PUBLISHED" && (
                  <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-3">
                    <p className="text-sm font-medium text-green-800">
                      Successfully published
                    </p>

                    <p className="mt-1 text-xs leading-5 text-green-700">
                      This post was successfully delivered to
                      Telegram.
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Delivery Information */}
            <div className="rounded-xl border border-gray-200 bg-white">
              <div className="border-b border-gray-100 px-6 py-5">
                <h2 className="text-base font-semibold text-gray-900">
                  Telegram Delivery
                </h2>

                <p className="mt-1 text-sm text-gray-500">
                  Delivery information recorded by the worker.
                </p>
              </div>

              <div className="divide-y divide-gray-100">
                <div className="flex items-center justify-between gap-4 px-6 py-4">
                  <span className="text-sm text-gray-500">
                    Channel
                  </span>

                  <span className="max-w-[180px] truncate text-right text-sm font-medium text-gray-800">
                    {post.channel_username ||
                      post.channel_id ||
                      "—"}
                  </span>
                </div>

                <div className="flex items-center justify-between gap-4 px-6 py-4">
                  <span className="text-sm text-gray-500">
                    Telegram Message ID
                  </span>

                  <span className="text-sm font-medium text-gray-800">
                    {post.telegram_message_id ??
                      "—"}
                  </span>
                </div>

                <div className="flex items-center justify-between gap-4 px-6 py-4">
                  <span className="text-sm text-gray-500">
                    Published At
                  </span>

                  <span className="text-right text-sm font-medium text-gray-800">
                    {formatDate(
                      post.published_at
                    )}
                  </span>
                </div>
              </div>
            </div>

            {/* Attempts */}
            <div className="rounded-xl border border-gray-200 bg-white">
              <div className="border-b border-gray-100 px-6 py-5">
                <h2 className="text-base font-semibold text-gray-900">
                  Processing Details
                </h2>
              </div>

              <div className="divide-y divide-gray-100">
                <div className="flex items-center justify-between px-6 py-4">
                  <span className="text-sm text-gray-500">
                    Attempts
                  </span>

                  <span className="text-sm font-semibold text-gray-900">
                    {post.attempts}
                  </span>
                </div>

                <div className="flex items-center justify-between px-6 py-4">
                  <span className="text-sm text-gray-500">
                    Created
                  </span>

                  <span className="text-right text-sm text-gray-700">
                    {formatDate(
                      post.created_at
                    )}
                  </span>
                </div>

                <div className="flex items-center justify-between px-6 py-4">
                  <span className="text-sm text-gray-500">
                    Updated
                  </span>

                  <span className="text-right text-sm text-gray-700">
                    {formatDate(
                      post.updated_at
                    )}
                  </span>
                </div>
              </div>
            </div>

            {/* Error */}
            {post.error_message && (
              <div className="rounded-xl border border-red-200 bg-red-50">
                <div className="border-b border-red-100 px-6 py-5">
                  <h2 className="text-base font-semibold text-red-900">
                    Last Publishing Error
                  </h2>
                </div>

                <div className="p-6">
                  <p className="whitespace-pre-wrap break-words text-sm leading-6 text-red-700">
                    {post.error_message}
                  </p>
                </div>
              </div>
            )}

            {/* Danger Zone */}
            {canDelete && (
              <div className="rounded-xl border border-red-200 bg-white">
                <div className="border-b border-red-100 px-6 py-5">
                  <h2 className="text-base font-semibold text-red-900">
                    Danger Zone
                  </h2>

                  <p className="mt-1 text-sm text-gray-500">
                    Permanently remove this Auto Publisher post.
                  </p>
                </div>

                <div className="p-6">
                  <button
                    type="button"
                    disabled={
                      deleting ||
                      isPublishing
                    }
                    onClick={handleDelete}
                    className="w-full rounded-lg border border-red-200 bg-white px-4 py-2.5 text-sm font-medium text-red-600 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {deleting
                      ? "Deleting..."
                      : "Delete Auto Post"}
                  </button>
                </div>
              </div>
            )}
          </div>
        </form>
      </div>
    </AdminShell>
  );
} 
