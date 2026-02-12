"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import type { User } from "@/lib/types";
import type { PlacementWithNote } from "@/lib/types";
import ApiErrorBanner from "../components/ApiErrorBanner";

export default function MorningBoardPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [todayByUser, setTodayByUser] = useState<Record<number, PlacementWithNote[]>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMorning = useCallback(async () => {
    try {
      setError(null);
      const userList = await api.users.list();
      setUsers(userList);
      const next: Record<number, PlacementWithNote[]> = {};
      await Promise.all(
        userList.map(async (u) => {
          const list = await api.boards.personal(u.id);
          next[u.id] = list.filter((p) => p.lane === "TODAY");
        })
      );
      setTodayByUser(next);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMorning();
  }, [fetchMorning]);

  if (loading) return <div className="p-6">Loading...</div>;
  if (error) return <div className="p-6"><ApiErrorBanner error={error} onRetry={fetchMorning} /></div>;

  return (
    <div className="mx-auto max-w-4xl px-6 py-8">
      <h1 className="mb-2 text-xl font-bold">Meeting</h1>
      <p className="mb-6 text-sm text-zinc-500">参加者の Today レーンスナップショット</p>
      <div className="flex flex-col gap-6">
        {users.map((u) => (
          <section key={u.id} className="rounded-xl border border-[var(--border)] bg-white p-4 shadow-sm">
            <h2 className="mb-3 font-semibold text-zinc-800">{u.name}</h2>
            <ul className="flex flex-col gap-2">
              {(todayByUser[u.id] ?? []).map((p) => (
                <li
                  key={p.id}
                  className="rounded-xl border border-[var(--border)] bg-[#fff9c4] px-3 py-2 text-sm font-medium text-zinc-900"
                >
                  {p.note_content || "（空）"}
                </li>
              ))}
            </ul>
            {(todayByUser[u.id] ?? []).length === 0 && (
              <p className="text-sm text-zinc-500">今日のタスクなし</p>
            )}
          </section>
        ))}
      </div>
    </div>
  );
}
