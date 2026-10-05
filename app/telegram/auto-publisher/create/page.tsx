"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import AdminShell from "@/components/layout/AdminShell";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type ContentType = "MESSAGE" | "LINK" | "VIDEO" | "IMAGE";

export default function CreateAutoPostPage() {
  const router = useRouter();

  const [title, setTitle] = useState("");
  const [contentType, setContentType] =
    useState<ContentType>("MESSAGE");

  const [message, setMessage] = useState("");
  const [linkUrl, setLinkUrl] = useState("");
  const [mediaUrl, setMediaUrl] = useState("");
  const [caption, setCaption] = useState("");

  const [isActive, setIsActive] = useState(true);
  const [scheduleEnabled, setScheduleEnabled] =
    useState(false);
  const [scheduledAt, setScheduledAt] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    setError("");

    if (!title.trim()) {
      setError("Please enter a post title.");
      return;
    }

    if (contentType === "MESSAGE" && !message.trim()) {
      setError("Please enter the message content.");
      return;
    }

    if (contentType === "LINK" && !linkUrl.trim()) {
      setError("Please enter the link URL.");
      return;
    }

    if (
      (contentType === "VIDEO" || contentType === "IMAGE") &&
      !mediaUrl.trim()
    ) {
      setError("Please enter the media URL.");
      return;
    }

    setIsSubmitting(true);

    try {
      const payload: Record<string, unknown> = {
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
          scheduleEnabled && scheduledAt
            ? new Date(scheduledAt).toISOString()
            : null,
      };

      const response = await fetch(
        `${API_URL}/api/telegram/auto-posts`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Unable to create the auto post."
        );
      }

      router.push("/telegram/auto-publisher");
      router.refresh();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to create the auto post."
      );
    } finally {
      setIsSubmitting(false);
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
                Create Post
              </span>
            </div>

            <h1 className="mt-2 text-2xl font-semibold text-gray-900">
              Create Auto Post
            </h1>

            <p className="mt-1 text-sm text-gray-500">
              Create content that can be queued and published
              automatically to Telegram.
            </p>
          </div>

          <Link
            href="/telegram/auto-publisher"
            className="inline-flex items-center justify-center rounded-lg border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 transition hover:bg-gray-50"
          >
            ← Back to Auto Publisher
          </Link>
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <form
          onSubmit={handleSubmit}
          className="grid grid-cols-1 gap-6 xl:grid-cols-3"
        >
          {/* Main form */}
          <div className="space-y-6 xl:col-span-2">
            <div className="rounded-xl border border-gray-200 bg-white">
              <div className="border-b border-gray-100 px-6 py-5">
                <h2 className="text-base font-semibold text-gray-900">
                  Post Content
                </h2>

                <p className="mt-1 text-sm text-gray-500">
                  Configure the content that will be published.
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
                    onChange={(e) =>
                      setTitle(e.target.value)
                    }
                    placeholder="Enter an internal post title"
                    className="w-full rounded-lg border border-gray-200 bg-white px-3.5 py-2.5 text-sm text-gray-900 outline-none transition placeholder:text-gray-400 focus:border-gray-400 focus:ring-2 focus:ring-gray-100"
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
                        contentType === item.value;

                      return (
                        <button
                          key={item.value}
                          type="button"
                          onClick={() =>
                            setContentType(
                              item.value as ContentType
                            )
                          }
                          className={`rounded-lg border px-3 py-3 text-left transition ${
                            selected
                              ? "border-gray-900 bg-gray-50"
                              : "border-gray-200 bg-white hover:bg-gray-50"
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
                      onChange={(e) =>
                        setMessage(e.target.value)
                      }
                      rows={9}
                      placeholder="Write the Telegram message..."
                      className="w-full resize-y rounded-lg border border-gray-200 bg-white px-3.5 py-3 text-sm text-gray-900 outline-none transition placeholder:text-gray-400 focus:border-gray-400 focus:ring-2 focus:ring-gray-100"
                    />

                    <p className="mt-2 text-xs text-gray-400">
                      This content will be sent directly as a
                      Telegram message.
                    </p>
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
                      onChange={(e) =>
                        setLinkUrl(e.target.value)
                      }
                      placeholder="https://example.com/article"
                      className="w-full rounded-lg border border-gray-200 bg-white px-3.5 py-2.5 text-sm text-gray-900 outline-none transition placeholder:text-gray-400 focus:border-gray-400 focus:ring-2 focus:ring-gray-100"
                    />
                  </div>
                )}

                {/* Media */}
                {(contentType === "VIDEO" ||
                  contentType === "IMAGE") && (
                  <>
                    <div>
                      <label className="mb-2 block text-sm font-medium text-gray-700">
                        {contentType === "VIDEO"
                          ? "Video URL"
                          : "Image URL"}
                      </label>

                      <input
                        type="url"
                        value={mediaUrl}
                        onChange={(e) =>
                          setMediaUrl(e.target.value)
                        }
                        placeholder="https://example.com/media"
                        className="w-full rounded-lg border border-gray-200 bg-white px-3.5 py-2.5 text-sm text-gray-900 outline-none transition placeholder:text-gray-400 focus:border-gray-400 focus:ring-2 focus:ring-gray-100"
                      />
                    </div>

                    <div>
                      <label className="mb-2 block text-sm font-medium text-gray-700">
                        Caption
                      </label>

                      <textarea
                        value={caption}
                        onChange={(e) =>
                          setCaption(e.target.value)
                        }
                        rows={5}
                        placeholder="Optional caption..."
                        className="w-full resize-y rounded-lg border border-gray-200 bg-white px-3.5 py-3 text-sm text-gray-900 outline-none transition placeholder:text-gray-400 focus:border-gray-400 focus:ring-2 focus:ring-gray-100"
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
                  Publish immediately through the queue or
                  schedule this post for a specific time.
                </p>
              </div>

              <div className="p-6">
                <label className="flex cursor-pointer items-start gap-3">
                  <input
                    type="checkbox"
                    checked={scheduleEnabled}
                    onChange={(e) =>
                      setScheduleEnabled(
                        e.target.checked
                      )
                    }
                    className="mt-1 h-4 w-4 rounded border-gray-300"
                  />

                  <span>
                    <span className="block text-sm font-medium text-gray-800">
                      Schedule this post
                    </span>

                    <span className="mt-1 block text-xs text-gray-500">
                      If disabled, the post can be queued
                      for the next available publishing cycle.
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
                      onChange={(e) =>
                        setScheduledAt(e.target.value)
                      }
                      className="w-full rounded-lg border border-gray-200 bg-white px-3.5 py-2.5 text-sm text-gray-900 outline-none focus:border-gray-400 focus:ring-2 focus:ring-gray-100 sm:max-w-md"
                    />
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right column */}
          <div className="space-y-6">
            <div className="rounded-xl border border-gray-200 bg-white">
              <div className="border-b border-gray-100 px-6 py-5">
                <h2 className="text-base font-semibold text-gray-900">
                  Publishing Settings
                </h2>
              </div>

              <div className="space-y-5 p-6">
                <label className="flex cursor-pointer items-start justify-between gap-4">
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
                    onClick={() =>
                      setIsActive(!isActive)
                    }
                    className={`relative mt-0.5 h-6 w-11 rounded-full transition ${
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
                </label>
              </div>
            </div>

            <div className="rounded-xl border border-gray-200 bg-white">
              <div className="border-b border-gray-100 px-6 py-5">
                <h2 className="text-base font-semibold text-gray-900">
                  Publishing Flow
                </h2>
              </div>

              <div className="space-y-4 p-6">
                {[
                  ["1", "Create", "Post starts as a draft."],
                  ["2", "Queue", "Post becomes eligible for publishing."],
                  ["3", "Publish", "Worker sends content to Telegram."],
                ].map(([number, label, text]) => (
                  <div
                    key={number}
                    className="flex gap-3"
                  >
                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gray-100 text-xs font-semibold text-gray-700">
                      {number}
                    </div>

                    <div>
                      <p className="text-sm font-medium text-gray-800">
                        {label}
                      </p>

                      <p className="mt-0.5 text-xs text-gray-500">
                        {text}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-xl border border-gray-200 bg-gray-50 p-5">
              <p className="text-xs leading-5 text-gray-500">
                The Auto Publisher worker checks the queue
                every 20 minutes. Only active queued posts
                are eligible for automatic publishing.
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex flex-col-reverse gap-3 border-t border-gray-200 pt-5 sm:flex-row sm:justify-end xl:col-span-3">
            <Link
              href="/telegram/auto-publisher"
              className="inline-flex items-center justify-center rounded-lg border border-gray-200 bg-white px-5 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </Link>

            <button
              type="submit"
              disabled={isSubmitting}
              className="inline-flex items-center justify-center rounded-lg bg-gray-900 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isSubmitting
                ? "Creating..."
                : "Create Auto Post"}
            </button>
          </div>
        </form>
      </div>
    </AdminShell>
  );
}
 
