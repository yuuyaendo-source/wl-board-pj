"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import type { PersonalMember } from "@/lib/personalMembers";
import type { Team } from "@/lib/types";

interface AddUserMenuProps {
  members: PersonalMember[];
  onSuccess: () => void;
  /** 指定時は親（管理メニュー等）が開閉を制御し、トリガーボタンは表示しない */
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

type Tab = "members" | "teams";

export default function AddUserMenu({ members, onSuccess, open: controlledOpen, onOpenChange }: AddUserMenuProps) {
  const [internalOpen, setInternalOpen] = useState(false);
  const controlled = controlledOpen !== undefined && onOpenChange !== undefined;
  const open = controlled ? controlledOpen : internalOpen;
  const setOpen = (next: boolean) => {
    if (controlled) onOpenChange(next);
    else setInternalOpen(next);
  };

  const [tab, setTab] = useState<Tab>("members");

  // --- メンバー追加フォーム ---
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [callName, setCallName] = useState("");
  const [teamId, setTeamId] = useState<number | "">("");
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [editEmail, setEditEmail] = useState("");
  const [editCallName, setEditCallName] = useState("");
  const [editTeamId, setEditTeamId] = useState<number | "">("");
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // --- チーム管理 ---
  const [teams, setTeams] = useState<Team[]>([]);
  const [teamsLoading, setTeamsLoading] = useState(false);
  const [newTeamName, setNewTeamName] = useState("");
  const [teamSubmitting, setTeamSubmitting] = useState(false);
  const [editingTeamId, setEditingTeamId] = useState<number | null>(null);
  const [editTeamName, setEditTeamName] = useState("");
  const [deletingTeamId, setDeletingTeamId] = useState<number | null>(null);
  const [teamError, setTeamError] = useState<string | null>(null);

  const fetchTeams = useCallback(async () => {
    setTeamsLoading(true);
    try {
      const data = await api.teams.list();
      setTeams(data);
    } catch {
      // silent
    } finally {
      setTeamsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) {
      setName("");
      setEmail("");
      setCallName("");
      setTeamId("");
      setEditingId(null);
      setError(null);
      setNewTeamName("");
      setTeamError(null);
      setEditingTeamId(null);
      fetchTeams();
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  }, [open, fetchTeams]);

  // ------- メンバー操作 -------

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
        team_id: teamId !== "" ? Number(teamId) : null,
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
    setEditTeamId(m.teamId ?? "");
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
        team_id: editTeamId !== "" ? Number(editTeamId) : null,
      });
      onSuccess();
      setEditingId(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "更新に失敗しました");
    } finally {
      setSubmitting(false);
    }
  };

  // ------- チーム操作 -------

  const handleCreateTeam = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = newTeamName.trim();
    if (!trimmed) return;
    setTeamSubmitting(true);
    setTeamError(null);
    try {
      await api.teams.create({ name: trimmed });
      setNewTeamName("");
      await fetchTeams();
    } catch (e) {
      setTeamError(e instanceof Error ? e.message : "チーム作成に失敗しました");
    } finally {
      setTeamSubmitting(false);
    }
  };

  const startEditTeam = (team: Team) => {
    setEditingTeamId(team.id);
    setEditTeamName(team.name);
    setTeamError(null);
  };

  const handleUpdateTeam = async (e: React.FormEvent) => {
    e.preventDefault();
    if (editingTeamId == null) return;
    const trimmed = editTeamName.trim();
    if (!trimmed) return;
    setTeamSubmitting(true);
    setTeamError(null);
    try {
      await api.teams.update(editingTeamId, { name: trimmed });
      setEditingTeamId(null);
      await fetchTeams();
    } catch (e) {
      setTeamError(e instanceof Error ? e.message : "チーム更新に失敗しました");
    } finally {
      setTeamSubmitting(false);
    }
  };

  const handleDeleteTeam = async (teamId: number, teamName: string) => {
    if (!confirm(`「${teamName}」を削除しますか？\n所属メンバーのチーム割り当ては解除されます。`)) return;
    setDeletingTeamId(teamId);
    setTeamError(null);
    try {
      await api.teams.delete(teamId);
      await fetchTeams();
    } catch (e) {
      setTeamError(e instanceof Error ? e.message : "チーム削除に失敗しました");
    } finally {
      setDeletingTeamId(null);
    }
  };

  const panelBoxClass = controlled
    ? "fixed right-4 top-14 z-50 w-[min(26rem,calc(100vw-2rem))] max-h-[85vh] overflow-y-auto rounded-xl border border-[var(--border)] bg-white p-4 shadow-lg"
    : "absolute right-0 top-full z-50 mt-1 w-[26rem] max-h-[85vh] overflow-y-auto rounded-xl border border-[var(--border)] bg-white p-4 shadow-lg";

  const teamSelectEl = (
    <select
      value={teamId}
      onChange={(e) => setTeamId(e.target.value === "" ? "" : Number(e.target.value))}
      className="rounded-lg border border-[var(--border)] px-3 py-2 text-sm bg-white"
      disabled={submitting}
    >
      <option value="">チームなし</option>
      {teams.map((t) => (
        <option key={t.id} value={t.id}>{t.name}</option>
      ))}
    </select>
  );

  const editTeamSelectEl = (
    <select
      value={editTeamId}
      onChange={(e) => setEditTeamId(e.target.value === "" ? "" : Number(e.target.value))}
      className="rounded border border-[var(--border)] px-2 py-1 text-sm bg-white"
      disabled={submitting}
    >
      <option value="">チームなし</option>
      {teams.map((t) => (
        <option key={t.id} value={t.id}>{t.name}</option>
      ))}
    </select>
  );

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
            {/* タブ */}
            <div className="mb-3 flex border-b border-[var(--border)]">
              <button
                type="button"
                onClick={() => setTab("members")}
                className={`px-4 py-2 text-sm font-medium transition-colors ${
                  tab === "members"
                    ? "border-b-2 border-[var(--primary)] text-[var(--primary)]"
                    : "text-zinc-500 hover:text-zinc-700"
                }`}
              >
                メンバー管理
              </button>
              <button
                type="button"
                onClick={() => { setTab("teams"); fetchTeams(); }}
                className={`px-4 py-2 text-sm font-medium transition-colors ${
                  tab === "teams"
                    ? "border-b-2 border-[var(--primary)] text-[var(--primary)]"
                    : "text-zinc-500 hover:text-zinc-700"
                }`}
              >
                チーム管理
              </button>
            </div>

            {/* ===== メンバー管理タブ ===== */}
            {tab === "members" && (
              <>
                <p className="mb-3 text-xs text-zinc-500">
                  ここで登録したユーザーはパーソナルボード・デスクトップアプリのメールログインで共通利用されます。
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
                    placeholder="メールアドレス（任意）"
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
                  {teamSelectEl}
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
                            {editTeamSelectEl}
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
                              <div>
                                <span className="text-zinc-800 font-medium">{m.name}</span>
                                {m.teamId && (
                                  <span className="ml-2 rounded-full bg-indigo-100 px-2 py-0.5 text-xs text-indigo-700">
                                    {teams.find(t => t.id === m.teamId)?.name ?? "チーム"}
                                  </span>
                                )}
                              </div>
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
              </>
            )}

            {/* ===== チーム管理タブ ===== */}
            {tab === "teams" && (
              <>
                <p className="mb-3 text-xs text-zinc-500">
                  チームを管理します。タスクボードでチームに付箋をドロップすると、所属メンバー全員にコピーされます。
                </p>
                <form onSubmit={handleCreateTeam} className="mb-4 flex gap-2">
                  <input
                    type="text"
                    value={newTeamName}
                    onChange={(e) => setNewTeamName(e.target.value)}
                    placeholder="新しいチーム名"
                    className="flex-1 rounded-lg border border-[var(--border)] px-3 py-2 text-sm"
                    disabled={teamSubmitting}
                    maxLength={100}
                  />
                  <button
                    type="submit"
                    disabled={teamSubmitting || !newTeamName.trim()}
                    className="rounded-lg bg-[var(--primary)] px-3 py-1.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
                  >
                    {teamSubmitting ? "追加中…" : "追加"}
                  </button>
                </form>
                {teamError && (
                  <p className="mb-2 text-sm text-red-600">{teamError}</p>
                )}
                <div className="border-t border-[var(--border)] pt-3">
                  {teamsLoading ? (
                    <p className="py-2 text-sm text-zinc-400">読み込み中…</p>
                  ) : (
                    <ul className="flex flex-col gap-2">
                      {teams.map((team) => (
                        <li
                          key={team.id}
                          className="flex flex-col gap-2 rounded-lg border border-[var(--border)] px-3 py-2"
                        >
                          {editingTeamId === team.id ? (
                            <form onSubmit={handleUpdateTeam} className="flex gap-2">
                              <input
                                type="text"
                                value={editTeamName}
                                onChange={(e) => setEditTeamName(e.target.value)}
                                className="flex-1 rounded border border-[var(--border)] px-2 py-1 text-sm"
                                disabled={teamSubmitting}
                                maxLength={100}
                              />
                              <button
                                type="submit"
                                disabled={teamSubmitting || !editTeamName.trim()}
                                className="rounded bg-[var(--primary)] px-2 py-1 text-xs font-medium text-white hover:opacity-90 disabled:opacity-50"
                              >
                                {teamSubmitting ? "保存中…" : "保存"}
                              </button>
                              <button
                                type="button"
                                onClick={() => setEditingTeamId(null)}
                                className="rounded border border-[var(--border)] px-2 py-1 text-xs text-zinc-600 hover:bg-zinc-50"
                              >
                                キャンセル
                              </button>
                            </form>
                          ) : (
                            <div className="flex items-center justify-between gap-2">
                              <div>
                                <span className="font-medium text-zinc-800">👥 {team.name}</span>
                                <span className="ml-2 text-xs text-zinc-400">{team.member_count}名</span>
                              </div>
                              <div className="flex shrink-0 gap-1">
                                <button
                                  type="button"
                                  onClick={() => startEditTeam(team)}
                                  className="rounded px-2 py-1 text-xs text-zinc-600 hover:bg-zinc-100"
                                >
                                  編集
                                </button>
                                <button
                                  type="button"
                                  onClick={() => handleDeleteTeam(team.id, team.name)}
                                  disabled={deletingTeamId === team.id}
                                  className="rounded px-2 py-1 text-xs text-red-600 hover:bg-red-50 disabled:opacity-50"
                                >
                                  {deletingTeamId === team.id ? "削除中…" : "削除"}
                                </button>
                              </div>
                            </div>
                          )}
                          {/* 所属メンバー一覧 */}
                          {editingTeamId !== team.id && (
                            <div className="flex flex-wrap gap-1">
                              {members
                                .filter(m => m.teamId === team.id)
                                .map(m => (
                                  <span key={m.ownerId} className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-600">
                                    {m.name}
                                  </span>
                                ))}
                              {members.filter(m => m.teamId === team.id).length === 0 && (
                                <span className="text-xs text-zinc-400">メンバーなし</span>
                              )}
                            </div>
                          )}
                        </li>
                      ))}
                      {teams.length === 0 && (
                        <p className="py-2 text-sm text-zinc-500">チームがありません</p>
                      )}
                    </ul>
                  )}
                </div>
              </>
            )}

            <button
              type="button"
              onClick={() => setOpen(false)}
              className="mt-4 w-full rounded-lg border border-[var(--border)] py-1.5 text-sm text-zinc-600 hover:bg-zinc-50"
            >
              閉じる
            </button>
          </div>
        </>
      )}
    </div>
  );
}
