"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import type { User } from "@/lib/types";
import type { PlacementWithNote } from "@/lib/types";
import ApiErrorBanner from "../components/ApiErrorBanner";
import DueDateBadge, { getDueDateBorderClass } from "../components/DueDateBadge";

export default function MeetingBoardPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [morningPlacements, setMorningPlacements] = useState<PlacementWithNote[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);

  const fetchMorning = useCallback(async () => {
    try {
      setError(null);
      const [userList, morningList] = await Promise.all([
        api.users.list(),
        api.boards.morning(),
      ]);
      setUsers(userList);
      setMorningPlacements(morningList);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMorning();
  }, [fetchMorning]);

  const handleSyncToMorning = useCallback(async () => {
    setSyncing(true);
    try {
      await api.dailyReset.syncToMorning();
      await fetchMorning();
    } catch (e) {
      setError(e instanceof Error ? e.message : "同期に失敗しました");
    } finally {
      setSyncing(false);
    }
  }, [fetchMorning]);

  const handleResetMeeting = useCallback(async () => {
    setSyncing(true);
    try {
      await api.dailyReset.resetMeeting();
      await fetchMorning();
    } catch (e) {
      setError(e instanceof Error ? e.message : "リセットに失敗しました");
    } finally {
      setSyncing(false);
    }
  }, [fetchMorning]);

  const handleFetchNews = useCallback(async () => {
    setSyncing(true);
    try {
      await api.news.fetch();
      await fetchMorning();
    } catch (e) {
      setError(e instanceof Error ? e.message : "ニュースの取得に失敗しました");
    } finally {
      setSyncing(false);
    }
  }, [fetchMorning]);

  const handleClearNews = useCallback(async () => {
    setSyncing(true);
    try {
      await api.news.clear();
      await fetchMorning();
    } catch (e) {
      setError(e instanceof Error ? e.message : "ニュースのクリアに失敗しました");
    } finally {
      setSyncing(false);
    }
  }, [fetchMorning]);

  const newsPlacements = morningPlacements.filter((p) => p.placement_source === "news");
  const byOwner = users.reduce(
    (acc, u) => {
      acc[u.id] = morningPlacements.filter((p) => p.owner_id === u.id);
      return acc;
    },
    {} as Record<number, PlacementWithNote[]>
  );

  if (loading) return <div className="p-6">Loading...</div>;
  if (error) return <div className="p-6"><ApiErrorBanner error={error} onRetry={fetchMorning} /></div>;

  return (
    <div className="mx-auto max-w-4xl px-6 py-8">
      <h1 className="mb-2 text-xl font-bold">Meeting</h1>
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={handleSyncToMorning}
          disabled={syncing}
          className="rounded-lg border border-[var(--border)] bg-white px-3 py-1.5 text-sm text-zinc-600 hover:bg-zinc-50 disabled:opacity-50"
        >
          {syncing ? "反映中…" : "Todayを反映（ミーティング前に実施してください）"}
        </button>
        <button
          type="button"
          onClick={handleResetMeeting}
          disabled={syncing}
          className="rounded-lg border border-[var(--border)] bg-white px-3 py-1.5 text-sm text-zinc-600 hover:bg-zinc-50 disabled:opacity-50"
        >
          リセット
        </button>
        <span className="text-zinc-400">|</span>
        <button
          type="button"
          onClick={handleFetchNews}
          disabled={syncing}
          className="rounded-lg border border-[var(--border)] bg-amber-50 px-3 py-1.5 text-sm text-amber-800 hover:bg-amber-100 disabled:opacity-50"
        >
          {syncing ? "取得中…" : "ニュースを取得"}
        </button>
        <button
          type="button"
          onClick={handleClearNews}
          disabled={syncing || newsPlacements.length === 0}
          className="rounded-lg border border-[var(--border)] bg-white px-3 py-1.5 text-sm text-zinc-600 hover:bg-zinc-50 disabled:opacity-50"
        >
          ニュースをクリア
        </button>
      </div>

      {newsPlacements.length > 0 && (
        <section className="mb-6 rounded-xl border border-amber-200 bg-amber-50/50 p-4 shadow-sm">
          <h2 className="mb-3 font-semibold text-amber-900">リン子ピックアップ</h2>
          <ul className="flex flex-col gap-3">
            {newsPlacements.map((p) => (
              <li
                key={p.id}
                className="rounded-lg border border-amber-100 bg-white px-3 py-2 text-sm text-zinc-800"
              >
                <span
                  className="whitespace-pre-wrap [&>br]:block"
                  dangerouslySetInnerHTML={{
                    __html: p.note_content
                      ? p.note_content
                        .replace(
                          /\[([^\]]*)\]\((https?:\/\/[^\s)]+)\)/g,
                          (_, label, url) =>
                            `<a href="${encodeURI(url)}" target="_blank" rel="noopener noreferrer" class="text-blue-600 underline">${(label || url).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")}</a>`
                        )
                        .replace(/\n/g, "<br />")
                      : "",
                  }}
                />
              </li>
            ))}
          </ul>
        </section>
      )}

      <div className="flex flex-col gap-6">
        {users.map((u) => (
          <section key={u.id} className="rounded-xl border border-[var(--border)] bg-white p-4 shadow-sm">
            <h2 className="mb-3 font-semibold text-zinc-800">{u.name}</h2>
            <ul className="flex flex-col gap-2">
              {(byOwner[u.id] ?? []).map((p) => {
                const borderClass = getDueDateBorderClass(p.due_date);
                return (
                  <li
                    key={p.id}
                    className={`flex flex-wrap items-center justify-between gap-2 rounded-xl border bg-[#fff9c4] px-3 py-2 text-sm font-medium text-zinc-900 ${borderClass || "border-[var(--border)]"
                      }`}
                  >
                    <span className="flex-1 whitespace-pre-wrap break-words">{p.note_content || "（空）"}</span>
                    {p.due_date && <DueDateBadge dueDate={p.due_date} />}
                  </li>
                );
              })}
            </ul>
            {(byOwner[u.id] ?? []).length === 0 && (
              <p className="text-sm text-zinc-500">今日のタスクなし</p>
            )}
          </section>
        ))}
      </div>
    </div>
  );
}