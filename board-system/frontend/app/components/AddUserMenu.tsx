"use client";

import { useState, useRef, useEffect } from "react";
import { api } from "@/lib/api";
import type { PersonalMember } from "@/lib/personalMembers";

interface AddUserMenuProps {
  members: PersonalMember[];
  onSuccess: () => void;
}

export default function AddUserMenu({ members, onSuccess }: AddUserMenuProps) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      setName("");
      setError(null);
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  }, [open]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.users.create({ name: trimmed });
      onSuccess();
      setOpen(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "追加に失敗しました");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (ownerId: number, displayName: string) => {
    if (!confirm(`「${displayName}」を削除しますか？\nその人が持っていた付箋はすべてタスクボードにリリースされ、誰でも引き取れる状態になります。`)) return;
    setDeletingId(ownerId);
    setError(null);
    try {
      await api.users.delete(ownerId);
      onSuccess();
    } catch (e) {
      setError(e instanceof Error ? e.message : "削除に失敗しました");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="rounded-xl px-3 py-1.5 text-sm font-medium text-zinc-600 hover:bg-zinc-100"
      >
        ユーザー管理
      </button>

      {open && (
        <>
          <div
            className="fixed inset-0 z-40"
            aria-hidden
            onClick={() => setOpen(false)}
          />
          <div className="absolute right-0 top-full z-50 mt-1 w-80 max-h-[80vh] overflow-y-auto rounded-xl border border-[var(--border)] bg-white p-4 shadow-lg">
            <p className="mb-3 text-sm font-medium text-zinc-700">メンバー管理</p>
            <form onSubmit={handleSubmit} className="mb-4 flex flex-col gap-3">
              <input
                ref={inputRef}
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="名前"
                className="rounded-lg border border-[var(--border)] px-3 py-2 text-sm"
                disabled={submitting}
                maxLength={100}
              />
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={submitting || !name.trim()}
                  className="rounded-lg bg-[var(--primary)] px-3 py-1.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
                >
                  {submitting ? "追加中…" : "追加"}
                </button>
              </div>
            </form>
            {error && (
              <p className="mb-2 text-sm text-red-600">{error}</p>
            )}
            <div className="border-t border-[var(--border)] pt-3">
              <p className="mb-2 text-xs text-zinc-500">削除（付箋はタスクボードにリリースされます）</p>
              <ul className="flex flex-col gap-1">
                {members.map(({ ownerId, name: displayName }) => (
                  <li
                    key={ownerId}
                    className="flex items-center justify-between gap-2 rounded-lg border border-[var(--border)] px-3 py-2 text-sm"
                  >
                    <span className="text-zinc-800">{displayName}</span>
                    <button
                      type="button"
                      onClick={() => handleDelete(ownerId, displayName)}
                      disabled={deletingId === ownerId}
                      className="shrink-0 rounded px-2 py-1 text-xs text-red-600 hover:bg-red-50 disabled:opacity-50"
                    >
                      {deletingId === ownerId ? "削除中…" : "削除"}
                    </button>
                  </li>
                ))}
              </ul>
              {members.length === 0 && (
                <p className="py-2 text-sm text-zinc-500">メンバーがいません</p>
              )}
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="mt-3 w-full rounded-lg border border-[var(--border)] py-1.5 text-sm text-zinc-600 hover:bg-zinc-50"
            >
              閉じる
            </button>
          </div>
        </>
      )}
    </div>
  );
}
