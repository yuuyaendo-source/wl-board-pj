"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import type { PersonalMember } from "@/lib/personalMembers";
import type { Team, User } from "@/lib/types";
import { requireAdminAuth } from "./AdminAuthModal";

interface AddUserMenuProps {
  members: PersonalMember[];
  onSuccess: () => void;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

type Tab = "members" | "teams";

// チームごとのバッジカラー設定
const TEAM_BADGE_STYLES = [
  "bg-indigo-100 text-indigo-700 border-indigo-200",
  "bg-emerald-100 text-emerald-700 border-emerald-200",
  "bg-amber-100 text-amber-700 border-amber-200",
  "bg-rose-100 text-rose-700 border-rose-200",
  "bg-purple-100 text-purple-700 border-purple-200",
  "bg-sky-100 text-sky-700 border-sky-200",
];

function getTeamBadgeStyle(teamId: number): string {
  const index = Math.abs(Number(teamId)) % TEAM_BADGE_STYLES.length;
  return TEAM_BADGE_STYLES[index];
}

export default function AddUserMenu({ members, onSuccess, open: controlledOpen, onOpenChange }: AddUserMenuProps) {
  const [internalOpen, setInternalOpen] = useState(false);
  const controlled = controlledOpen !== undefined && onOpenChange !== undefined;
  const open = controlled ? controlledOpen : internalOpen;
  const setOpen = (next: boolean) => {
    if (controlled) onOpenChange(next);
    else setInternalOpen(next);
  };

  const [tab, setTab] = useState<Tab>("members");

  // APIから直接取得した最新ユーザーリスト
  const [fullUsers, setFullUsers] = useState<User[]>([]);

  // --- メンバー追加・編集フォームステート ---
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [callName, setCallName] = useState("");
  const [teamIds, setTeamIds] = useState<number[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [editEmail, setEditEmail] = useState("");
  const [editCallName, setEditCallName] = useState("");
  const [editTeamIds, setEditTeamIds] = useState<number[]>([]);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // --- チーム管理ステート ---
  const [teams, setTeams] = useState<Team[]>([]);
  const [teamsLoading, setTeamsLoading] = useState(false);
  const [newTeamName, setNewTeamName] = useState("");
  const [teamSubmitting, setTeamSubmitting] = useState(false);
  const [editingTeamId, setEditingTeamId] = useState<number | null>(null);
  const [editTeamName, setEditTeamName] = useState("");
  const [deletingTeamId, setDeletingTeamId] = useState<number | null>(null);
  const [teamError, setTeamError] = useState<string | null>(null);

  // ユーザー全件取得
  const fetchUsersData = useCallback(async () => {
    try {
      const data = await api.users.list();
      setFullUsers(data);
    } catch {
      // silent
    }
  }, []);

  // チーム一覧取得
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
      setTeamIds([]);
      setEditingId(null);
      setError(null);
      setNewTeamName("");
      setTeamError(null);
      setEditingTeamId(null);
      void fetchUsersData();
      void fetchTeams();
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  }, [open, fetchUsersData, fetchTeams]);

  // ------- メンバー操作 -------

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedName = name.trim();
    if (!trimmedName) return;

    requireAdminAuth(async () => {
      setSubmitting(true);
      setError(null);
      try {
        const newUser = await api.users.create({
          name: trimmedName,
          email: email.trim(),
          call_name: callName.trim(),
          team_ids: teamIds,
        });
        // 取得レスポンスを直接ステートに追加して同期ズレを防止
        setFullUsers((prev) => [...prev, newUser]);
        onSuccess();
        setOpen(false);
      } catch (e) {
        setError(e instanceof Error ? e.message : "追加に失敗しました");
      } finally {
        setSubmitting(false);
      }
    });
  };

  const handleDelete = async (ownerId: number, displayName: string) => {
    requireAdminAuth(async () => {
      if (!confirm(`「${displayName}」を削除しますか？\nその人が持っていた付箋はすべてタスクボードにリリースされ、誰でも引き取れる状態になります。`)) return;
      setDeletingId(ownerId);
      setError(null);
      try {
        await api.users.delete(ownerId);
        setFullUsers((prev) => prev.filter((u) => Number(u.id) !== Number(ownerId)));
        onSuccess();
      } catch (e) {
        setError(e instanceof Error ? e.message : "削除に失敗しました");
      } finally {
        setDeletingId(null);
      }
    });
  };

  const startEdit = (m: any) => {
    const targetId = Number(m.ownerId ?? m.id);
    // fullUsersの最新データから参照
    const targetUser = fullUsers.find((u) => Number(u.id) === targetId) ?? m;

    setEditingId(targetId);
    setEditName(targetUser.name ?? "");
    setEditEmail(targetUser.email ?? "");
    setEditCallName(targetUser.call_name ?? "");

    // チームIDリストを確実に数値配列化
    let extractedTeamIds: number[] = [];
    if (Array.isArray(targetUser.team_ids)) {
      extractedTeamIds = targetUser.team_ids.map(Number);
    } else if (Array.isArray(targetUser.teams)) {
      extractedTeamIds = targetUser.teams.map((t: any) => Number(t.id));
    } else if (targetUser.teamId) {
      extractedTeamIds = [Number(targetUser.teamId)];
    }

    setEditTeamIds(extractedTeamIds);
    setError(null);
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (editingId == null) return;
    const trimmedName = editName.trim();
    if (!trimmedName) return;

    requireAdminAuth(async () => {
      setSubmitting(true);
      setError(null);
      try {
        const updatedUser = await api.users.update(editingId, {
          name: trimmedName,
          email: editEmail.trim(),
          call_name: editCallName.trim(),
          team_ids: editTeamIds,
        });

        // サーバーから返ってきた最新データを直接ステートに反映（同期ズレ解消）
        setFullUsers((prev) =>
          prev.map((u) => (Number(u.id) === Number(editingId) ? updatedUser : u))
        );

        onSuccess();
        setEditingId(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "更新に失敗しました");
      } finally {
        setSubmitting(false);
      }
    });
  };

  // ------- チーム操作 -------

  const handleCreateTeam = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = newTeamName.trim();
    if (!trimmed) return;

    requireAdminAuth(async () => {
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
    });
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

    requireAdminAuth(async () => {
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
    });
  };

  const handleDeleteTeam = async (teamId: number, teamName: string) => {
    requireAdminAuth(async () => {
      if (!confirm(`「${teamName}」を削除しますか？\n所属メンバーのチーム割り当ては解除されます。`)) return;
      setDeletingTeamId(teamId);
      setTeamError(null);
      try {
        await api.teams.delete(teamId);
        await fetchTeams();
        await fetchUsersData();
      } catch (e) {
        setTeamError(e instanceof Error ? e.message : "チーム削除に失敗しました");
      } finally {
        setDeletingTeamId(null);
      }
    });
  };

  const panelBoxClass = controlled
    ? "fixed right-4 top-14 z-50 w-[min(26rem,calc(100vw-2rem))] max-h-[85vh] overflow-y-auto rounded-xl border border-[var(--border)] bg-white p-4 shadow-lg"
    : "absolute right-0 top-full z-50 mt-1 w-[26rem] max-h-[85vh] overflow-y-auto rounded-xl border border-[var(--border)] bg-white p-4 shadow-lg";

  const renderTeamCheckboxes = (selectedIds: number[], onChange: (ids: number[]) => void) => (
    <div className="flex flex-col gap-1.5 rounded-lg border border-[var(--border)] p-2 bg-zinc-50">
      <span className="text-xs text-zinc-500 font-medium">所属チーム（複数選択可）</span>
      {teams.length === 0 ? (
        <span className="text-xs text-zinc-400">チームが登録されていません</span>
      ) : (
        <div className="flex flex-wrap gap-2">
          {teams.map((t) => {
            const checked = selectedIds.map(Number).includes(Number(t.id));
            return (
              <label key={t.id} className="flex items-center gap-1.5 cursor-pointer bg-white px-2.5 py-1 rounded border border-zinc-200 text-xs hover:bg-zinc-100">
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={(e) => {
                    const targetId = Number(t.id);
                    if (e.target.checked) onChange([...selectedIds.map(Number), targetId]);
                    else onChange(selectedIds.map(Number).filter((id) => id !== targetId));
                  }}
                  disabled={submitting}
                />
                <span className="text-zinc-700">{t.name}</span>
              </label>
            );
          })}
        </div>
      )}
    </div>
  );

  // 一覧表示データは fullUsers を最優先
  const displayList = fullUsers.length > 0 ? fullUsers : members;

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
                className={`px-4 py-2 text-sm font-medium transition-colors ${tab === "members"
                  ? "border-b-2 border-[var(--primary)] text-[var(--primary)]"
                  : "text-zinc-500 hover:text-zinc-700"
                  }`}
              >
                メンバー管理
              </button>
              <button
                type="button"
                onClick={() => { setTab("teams"); void fetchTeams(); }}
                className={`px-4 py-2 text-sm font-medium transition-colors ${tab === "teams"
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
                  {renderTeamCheckboxes(teamIds, setTeamIds)}
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
                    {displayList.map((m: any) => {
                      const memberId = Number(m.ownerId ?? m.id);
                      const targetUser = fullUsers.find((u) => Number(u.id) === memberId) ?? m;

                      // 所属チームの判定
                      let assignedTeamIds: number[] = [];
                      if (Array.isArray(targetUser.team_ids)) {
                        assignedTeamIds = targetUser.team_ids.map(Number);
                      } else if (Array.isArray(targetUser.teams)) {
                        assignedTeamIds = targetUser.teams.map((t: any) => Number(t.id));
                      } else if (targetUser.teamId) {
                        assignedTeamIds = [Number(targetUser.teamId)];
                      }

                      const userTeams = teams.filter((t) => assignedTeamIds.includes(Number(t.id)));

                      return (
                        <li
                          key={memberId}
                          className="flex flex-col gap-1 rounded-lg border border-[var(--border)] px-3 py-2 text-sm"
                        >
                          {editingId === memberId ? (
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
                              {renderTeamCheckboxes(editTeamIds, setEditTeamIds)}
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
                                <div className="flex flex-wrap items-center gap-1.5">
                                  <span className="text-zinc-800 font-medium">{targetUser.name}</span>
                                  {userTeams.map((t) => (
                                    <span
                                      key={t.id}
                                      className={`rounded-full px-2 py-0.5 text-xs font-medium border ${getTeamBadgeStyle(t.id)}`}
                                    >
                                      {t.name}
                                    </span>
                                  ))}
                                  {userTeams.length === 0 && (
                                    <span className="text-xs text-zinc-400">(未所属)</span>
                                  )}
                                </div>
                                <div className="flex shrink-0 gap-1">
                                  <button
                                    type="button"
                                    onClick={() => startEdit(targetUser)}
                                    className="rounded px-2 py-1 text-xs text-zinc-600 hover:bg-zinc-100"
                                  >
                                    編集
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => handleDelete(memberId, targetUser.name)}
                                    disabled={deletingId === memberId}
                                    className="rounded px-2 py-1 text-xs text-red-600 hover:bg-red-50 disabled:opacity-50"
                                  >
                                    {deletingId === memberId ? "削除中…" : "削除"}
                                  </button>
                                </div>
                              </div>
                              {(targetUser.email || targetUser.call_name) && (
                                <div className="flex flex-wrap gap-x-3 gap-y-0 text-xs text-zinc-500">
                                  {targetUser.email && <span>{targetUser.email}</span>}
                                  {targetUser.call_name && <span>呼び名: {targetUser.call_name}</span>}
                                </div>
                              )}
                            </>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                  {displayList.length === 0 && (
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
                              {displayList
                                .filter((m: any) => {
                                  const memberId = Number(m.ownerId ?? m.id);
                                  const targetUser = fullUsers.find((u) => Number(u.id) === memberId) ?? m;

                                  let ids: number[] = [];
                                  if (Array.isArray(targetUser.team_ids)) {
                                    ids = targetUser.team_ids.map(Number);
                                  } else if (Array.isArray(targetUser.teams)) {
                                    ids = targetUser.teams.map((t: any) => Number(t.id));
                                  } else if (targetUser.teamId) {
                                    ids = [Number(targetUser.teamId)];
                                  }

                                  return ids.includes(Number(team.id));
                                })
                                .map((m: any) => (
                                  <span key={m.ownerId ?? m.id} className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-600">
                                    {m.name}
                                  </span>
                                ))}
                              {displayList.filter((m: any) => {
                                const memberId = Number(m.ownerId ?? m.id);
                                const targetUser = fullUsers.find((u) => Number(u.id) === memberId) ?? m;

                                let ids: number[] = [];
                                if (Array.isArray(targetUser.team_ids)) {
                                  ids = targetUser.team_ids.map(Number);
                                } else if (Array.isArray(targetUser.teams)) {
                                  ids = targetUser.teams.map((t: any) => Number(t.id));
                                } else if (targetUser.teamId) {
                                  ids = [Number(targetUser.teamId)];
                                }

                                return ids.includes(Number(team.id));
                              }).length === 0 && (
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