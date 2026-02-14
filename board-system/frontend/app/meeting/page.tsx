"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import type { User } from "@/lib/types";
import type { PlacementWithNote } from "@/lib/types";
import ApiErrorBanner from "../components/ApiErrorBanner";

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
        <p className="text-sm text-zinc-500">（毎朝 10:15 に反映）</p>
        <button
          type="button"
          onClick={handleSyncToMorning}
          disabled={syncing}
          className="rounded-lg border border-[var(--border)] bg-white px-3 py-1.5 text-sm text-zinc-600 hover:bg-zinc-50 disabled:opacity-50"
        >
          {syncing ? "反映中…" : "今の Today を反映（テスト用）"}
        </button>
      </div>
      <div className="flex flex-col gap-6">
        {users.map((u) => (
          <section key={u.id} className="rounded-xl border border-[var(--border)] bg-white p-4 shadow-sm">
            <h2 className="mb-3 font-semibold text-zinc-800">{u.name}</h2>
            <ul className="flex flex-col gap-2">
              {(byOwner[u.id] ?? []).map((p) => (
                <li
                  key={p.id}
                  className="rounded-xl border border-[var(--border)] bg-[#fff9c4] px-3 py-2 text-sm font-medium text-zinc-900"
                >
                  {p.note_content || "（空）"}
                </li>
              ))}
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
