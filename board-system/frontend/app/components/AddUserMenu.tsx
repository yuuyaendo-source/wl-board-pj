"use client";

import { useState, useRef, useEffect } from "react";
import { api } from "@/lib/api";
import type { PersonalMember } from "@/lib/personalMembers";

interface AddUserMenuProps {
  members: PersonalMember[];
  onSuccess: () => void;
  /** 指定時は親（管理メニュー等）が開閉を制御し、トリガーボタンは表示しない */
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export default function AddUserMenu({ members, onSuccess, open: controlledOpen, onOpenChange }: AddUserMenuProps) {
  const [internalOpen, setInternalOpen] = useState(false);
  const controlled = controlledOpen !== undefined && onOpenChange !== undefined;
  const open = controlled ? controlledOpen : internalOpen;
  const setOpen = (next: boolean) => {
    if (controlled) onOpenChange(next);
    else setInternalOpen(next);
  };
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [callName, setCallName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [editEmail, setEditEmail] = useState("");
  const [editCallName, setEditCallName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      setName("");
      setEmail("");
      setCallName("");
      setEditingId(null);
      setError(null);
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  }, [open]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedName = name.trim();
    if (!trimmedName) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.users.create({
        name: trimmedName,
        email: email.trim() || undefined,
        call_name: callName.trim() || undefined,
      });
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

  const startEdit = (m: PersonalMember) => {
    setEditingId(m.ownerId);
    setEditName(m.name);
    setEditEmail(m.email ?? "");
    setEditCallName(m.call_name ?? "");
    setError(null);
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (editingId == null) return;
    const trimmedName = editName.trim();
    if (!trimmedName) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.users.update(editingId, {
        name: trimmedName,
        email: editEmail.trim() || undefined,
        call_name: editCallName.trim() || undefined,
      });
      onSuccess();
      setEditingId(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "更新に失敗しました");
    } finally {
      setSubmitting(false);
    }
  };

  const panelBoxClass = controlled
    ? "fixed right-4 top-14 z-50 w-[min(24rem,calc(100vw-2rem))] max-h-[85vh] overflow-y-auto rounded-xl border border-[var(--border)] bg-white p-4 shadow-lg"
    : "absolute right-0 top-full z-50 mt-1 w-96 max-h-[85vh] overflow-y-auto rounded-xl border border-[var(--border)] bg-white p-4 shadow-lg";

  return (
    <div className={controlled ? "contents" : "relative"}>
      {!controlled && (
        <button
          type="button"
          onClick={() => setOpen(!open)}
          className="rounded-xl px-3 py-1.5 text-sm font-medium text-zinc-600 hover:bg-zinc-100"
        >
          ユーザー管理
        </button>
      )}

      {open && (
        <>
          <div
            className="fixed inset-0 z-40"
            aria-hidden
            onClick={() => setOpen(false)}
          />
          <div className={panelBoxClass}>
            <p className="mb-3 text-sm font-medium text-zinc-700">メンバー管理（共通ユーザーDB）</p>
            <p className="mb-3 text-xs text-zinc-500">
              ここで登録したユーザーはパーソナルボード・デスクトップアプリのメールログインで共通利用されます。メールを登録するとデスクトップアプリで「ボード」からパーソナルを開けます。
            </p>
            <form onSubmit={handleSubmit} className="mb-4 flex flex-col gap-3">
              <input
                ref={inputRef}
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="名前（必須）"
                className="rounded-lg border border-[var(--border)] px-3 py-2 text-sm"
                disabled={submitting}
                maxLength={100}
              />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="メールアドレス（任意・デスクトップアプリ紐づけ用）"
                className="rounded-lg border border-[var(--border)] px-3 py-2 text-sm"
                disabled={submitting}
                maxLength={255}
              />
              <input
                type="text"
                value={callName}
                onChange={(e) => setCallName(e.target.value)}
                placeholder="呼び名（任意）"
                className="rounded-lg border border-[var(--border)] px-3 py-2 text-sm"
                disabled={submitting}
                maxLength={50}
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
              <p className="mb-2 text-xs text-zinc-500">編集・削除（付箋はタスクボードにリリースされます）</p>
              <ul className="flex flex-col gap-1">
                {members.map((m) => (
                  <li
                    key={m.ownerId}
                    className="flex flex-col gap-1 rounded-lg border border-[var(--border)] px-3 py-2 text-sm"
                  >
                    {editingId === m.ownerId ? (
                      <form onSubmit={handleUpdate} className="flex flex-col gap-2">
                        <input
                          type="text"
                          value={editName}
                          onChange={(e) => setEditName(e.target.value)}
                          placeholder="名前（必須）"
                          className="rounded border border-[var(--border)] px-2 py-1 text-sm"
                          disabled={submitting}
                          maxLength={100}
                        />
                        <input
                          type="email"
                          value={editEmail}
                          onChange={(e) => setEditEmail(e.target.value)}
                          placeholder="メールアドレス"
                          className="rounded border border-[var(--border)] px-2 py-1 text-sm"
                          disabled={submitting}
                          maxLength={255}
                        />
                        <input
                          type="text"
                          value={editCallName}
                          onChange={(e) => setEditCallName(e.target.value)}
                          placeholder="呼び名"
                          className="rounded border border-[var(--border)] px-2 py-1 text-sm"
                          disabled={submitting}
                          maxLength={50}
                        />
                        <div className="flex gap-2">
                          <button
                            type="submit"
                            disabled={submitting || !editName.trim()}
                            className="rounded bg-[var(--primary)] px-2 py-1 text-xs font-medium text-white hover:opacity-90 disabled:opacity-50"
                          >
                            {submitting ? "保存中…" : "保存"}
                          </button>
                          <button
                            type="button"
                            onClick={() => setEditingId(null)}
                            className="rounded border border-[var(--border)] px-2 py-1 text-xs text-zinc-600 hover:bg-zinc-50"
                          >
                            キャンセル
                          </button>
                        </div>
                      </form>
                    ) : (
                      <>
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-zinc-800 font-medium">{m.name}</span>
                          <div className="flex shrink-0 gap-1">
                            <button
                              type="button"
                              onClick={() => startEdit(m)}
                              className="rounded px-2 py-1 text-xs text-zinc-600 hover:bg-zinc-100"
                            >
                              編集
                            </button>
                            <button
                              type="button"
                              onClick={() => handleDelete(m.ownerId, m.name)}
                              disabled={deletingId === m.ownerId}
                              className="rounded px-2 py-1 text-xs text-red-600 hover:bg-red-50 disabled:opacity-50"
                            >
                              {deletingId === m.ownerId ? "削除中…" : "削除"}
                            </button>
                          </div>
                        </div>
                        {(m.email || m.call_name) && (
                          <div className="flex flex-wrap gap-x-3 gap-y-0 text-xs text-zinc-500">
                            {m.email && <span>{m.email}</span>}
                            {m.call_name && <span>呼び名: {m.call_name}</span>}
                          </div>
                        )}
                      </>
                    )}
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
