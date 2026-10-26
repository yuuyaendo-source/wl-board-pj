"use client";

import React, { useEffect, useState, useCallback } from "react";
import { flushSync } from "react-dom";
import { api } from "@/lib/api";
import {
  fetchLegacyPostitNotes,
  LEGACY_POSTIT_BOARD_ID,
} from "@/lib/legacyPostit";
import type { PlacementWithNote, Team } from "@/lib/types";
import { usePersonalMembers } from "@/lib/personalMembers";
import ApiErrorBanner from "../components/ApiErrorBanner";
import NoteCard from "../components/NoteCard";
import { OperationPanel } from "../components/OperationPanel";

/** mutation 直後の refetch で古いレスポンスが返るのを防ぐ */
const REFETCH_DELAY_MS = 120;
const delay = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

const AUTO_IMPORT_STORAGE_KEY = "board-system:taskboard:autoImport";

function getStoredAutoImport(): boolean {
  if (typeof window === "undefined") return true;
  const stored = window.localStorage.getItem(AUTO_IMPORT_STORAGE_KEY);
  if (stored === null) return true; // 未設定時はON
  return stored === "true";
}

const COLUMNS = [
  { id: "unassigned", title: "応援要請・未振り分け", targetQ: null, droppable: false },
  { id: "ideas", title: "アイデア", targetQ: 1, droppable: true },
  { id: "tasks", title: "タスク", targetQ: 2, droppable: true },
  { id: "done", title: "完了", targetQ: 5, droppable: true },
] as const;

export default function TaskBoardPage() {
  const [placements, setPlacements] = useState<PlacementWithNote[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [importing, setImporting] = useState(false);
  const [importMessage, setImportMessage] = useState<string | null>(null);
  const [autoImportEnabled, setAutoImportEnabledState] = useState(true);
  const { members: personalMembers } = usePersonalMembers();
  const [teams, setTeams] = useState<Team[]>([]);

  // 初回マウント時に localStorage から復元
  useEffect(() => {
    setAutoImportEnabledState(getStoredAutoImport());
  }, []);

  const setAutoImportEnabled = useCallback((value: boolean | ((prev: boolean) => boolean)) => {
    setAutoImportEnabledState((prev) => {
      const next = typeof value === "function" ? value(prev) : value;
      if (typeof window !== "undefined") {
        window.localStorage.setItem(AUTO_IMPORT_STORAGE_KEY, String(next));
      }
      return next;
    });
  }, []);

  const fetchTask = useCallback(async () => {
    try {
      setError(null);
      const list = await api.boards.task();
      flushSync(() => setPlacements(list));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchTeams = useCallback(async () => {
    try {
      const data = await api.teams.list();
      setTeams(data);
    } catch {
      // silent
    }
  }, []);

  useEffect(() => {
    fetchTask();
    fetchTeams();
  }, [fetchTask, fetchTeams]);

  const handleImportFromPostit = useCallback(async () => {
    setImporting(true);
    setImportMessage(null);
    setActionError(null);
    try {
      const notes = await fetchLegacyPostitNotes();
      const result = await api.stickyNotes.importFromPostit({
        board_id: LEGACY_POSTIT_BOARD_ID,
        notes,
      });
      const msg =
        result.created > 0
          ? `${result.created} 件を追加しました` + (result.skipped > 0 ? `（${result.skipped} 件は既存のためスキップ）` : "")
          : result.skipped > 0
            ? `すべて既に取り込み済みです（${result.skipped} 件）`
            : "取り込む付箋がありませんでした";
      setImportMessage(msg);
      await delay(REFETCH_DELAY_MS);
      await fetchTask();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "取り込みに失敗しました");
    } finally {
      setImporting(false);
    }
  }, [fetchTask]);

  useEffect(() => {
    const handler = () => handleImportFromPostit();
    window.addEventListener("task-import-request", handler);
    return () => window.removeEventListener("task-import-request", handler);
  }, [handleImportFromPostit]);

  // 自動取り込み（5分ごと）
  useEffect(() => {
    if (!autoImportEnabled) return;
    const runImport = async () => {
      try {
        const notes = await fetchLegacyPostitNotes();
        if (notes.length === 0) return;
        await api.stickyNotes.importFromPostit({ board_id: LEGACY_POSTIT_BOARD_ID, notes });
        await delay(REFETCH_DELAY_MS);
        await fetchTask();
      } catch {
        // silent
      }
    };
    runImport();
    const interval = setInterval(runImport, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [autoImportEnabled, fetchTask]);

  const handleCopyToPersonal = useCallback(
    async (noteId: number, ownerId: number) => {
      setActionError(null);
      try {
        await api.stickyNotes.moveToPersonal(noteId, {
          owner_id: ownerId,
          lane: "INBOX",
        });
        await delay(REFETCH_DELAY_MS);
        await fetchTask();
        setImportMessage("パーソナルボードにコピーしました");
        setTimeout(() => setImportMessage(null), 2000);
      } catch (err) {
        setActionError(err instanceof Error ? err.message : "コピーに失敗しました");
      }
    },
    [fetchTask]
  );

  const handleCopyToTeam = useCallback(
    async (noteId: number, teamId: number, teamName: string) => {
      setActionError(null);
      try {
        const res = await api.stickyNotes.copyToTeam(noteId, { team_id: teamId });
        await delay(REFETCH_DELAY_MS);
        await fetchTask();
        setImportMessage(res.message);
        setTimeout(() => setImportMessage(null), 3000);
      } catch (err) {
        setActionError(err instanceof Error ? err.message : `${teamName} へのコピーに失敗しました`);
      }
    },
    [fetchTask]
  );

  const handleAppendContent = useCallback(
    async (noteId: number, currentContent: string | null, appendedText: string) => {
      setActionError(null);
      const newContent = (currentContent || "").trim()
        ? `${(currentContent || "").trim()}\n${appendedText}`
        : appendedText;
      try {
        await api.stickyNotes.update(noteId, { content: newContent });
        await delay(REFETCH_DELAY_MS);
        await fetchTask();
      } catch (e) {
        setActionError(e instanceof Error ? e.message : "更新に失敗しました");
      }
    },
    [fetchTask]
  );

  const handleDueDateChange = useCallback(
    async (noteId: number, dueDateStr: string) => {
      setActionError(null);
      try {
        await api.stickyNotes.update(noteId, {
          due_date: dueDateStr === "" ? "" : dueDateStr,
        });
        await delay(REFETCH_DELAY_MS);
        await fetchTask();
      } catch (e) {
        setActionError(e instanceof Error ? e.message : "期限の更新に失敗しました");
      }
    },
    [fetchTask]
  );

  const handleTrashDrop = useCallback(
    async (noteId: number) => {
      setImportMessage(null);
      setActionError(null);
      try {
        await api.stickyNotes.delete(noteId);
        await delay(REFETCH_DELAY_MS);
        await fetchTask();
      } catch (e) {
        setActionError(e instanceof Error ? e.message : "削除に失敗しました");
        await fetchTask();
      }
    },
    [fetchTask]
  );

  const byColumnRaw: Record<string, PlacementWithNote[]> = {
    unassigned: [],
    ideas: [],
    tasks: [],
    done: [],
  };

  placements.forEach((p) => {
    const isUnassignedRed = p.task_color === "red" && !p.is_accepted_by_others;
    if (isUnassignedRed || p.task_color === "yellow") {
      byColumnRaw.unassigned.push(p);
    } else {
      const q = p.matrix_quadrant ?? 1;
      if (q === 1) {
        byColumnRaw.ideas.push(p);
      } else if (q === 2 || q === 3 || q === 4) {
        byColumnRaw.tasks.push(p);
      } else if (q === 5) {
        byColumnRaw.done.push(p);
      } else {
        byColumnRaw.ideas.push(p);
      }
    }
  });

  const byColumn: Record<string, PlacementWithNote[]> = {};
  for (const key of Object.keys(byColumnRaw)) {
    byColumn[key] = [...byColumnRaw[key]].sort((a, b) =>
      (a.task_color === "red" ? 0 : 1) - (b.task_color === "red" ? 0 : 1)
    );
  }

  const handleDrop = useCallback(
    async (placementId: number, column: number) => {
      setActionError(null);
      try {
        await api.boardPlacements.patch(placementId, {
          matrix_quadrant: column,
        });
        await delay(REFETCH_DELAY_MS);
        await fetchTask();
      } catch (e) {
        setActionError(e instanceof Error ? e.message : "移動に失敗しました");
        await fetchTask();
      }
    },
    [fetchTask]
  );

  if (loading) return <div className="p-6">Loading...</div>;
  if (error)
    return (
      <div className="p-6">
        <ApiErrorBanner error={error} onRetry={fetchTask} />
      </div>
    );

  return (
    <div className="mx-auto max-w-6xl px-4 py-4">
      {/* メニューバー・ゴミ箱・コピー先 */}
      <div className="sticky top-[52px] z-10 -mx-4 mb-4">
        {actionError && (
          <div className="mb-2 flex items-center justify-between gap-2 rounded-xl border border-amber-300 bg-amber-50 px-4 py-2 text-sm font-semibold text-amber-900 shadow-xs">
            <div className="flex items-center gap-2">
              <span>⚠️</span>
              <span>{actionError}</span>
            </div>
            <button
              type="button"
              onClick={() => setActionError(null)}
              className="text-xs text-amber-700 hover:underline font-bold"
            >
              ✕
            </button>
          </div>
        )}

        {(importing || importMessage) && (
          <div className="mb-2 flex items-center justify-between text-xs font-medium text-emerald-800 bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-200 shadow-xs">
            <span>{importing ? "取り込み中…" : importMessage}</span>
            <button
              type="button"
              onClick={() => setImportMessage(null)}
              className="text-xs text-emerald-600 hover:underline font-bold"
            >
              ✕
            </button>
          </div>
        )}

        <OperationPanel
          members={personalMembers}
          teams={teams}
          autoImport={autoImportEnabled}
          isImporting={importing}
          onAutoImportChange={setAutoImportEnabled}
          onImportClick={handleImportFromPostit}
          onTrashDrop={handleTrashDrop}
          onMemberDrop={handleCopyToPersonal}
          onTeamDrop={handleCopyToTeam}
        />
      </div>

      {/* タスクボード4列 */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
        {COLUMNS.map((col) => (
          <Column
            key={col.id}
            title={col.title}
            placements={byColumn[col.id] || []}
            droppable={col.droppable}
            targetQ={col.targetQ}
            onDrop={handleDrop}
            onRefresh={fetchTask}
            onAppendContent={handleAppendContent}
            onDueDateChange={handleDueDateChange}
          />
        ))}
      </div>
    </div>
  );
}

function Column({
  title,
  placements,
  droppable,
  targetQ,
  onDrop,
  onRefresh,
  onAppendContent,
  onDueDateChange,
}: {
  title: string;
  placements: PlacementWithNote[];
  droppable: boolean;
  targetQ: number | null;
  onDrop: (placementId: number, targetQ: number) => void;
  onRefresh: () => void;
  onAppendContent?: (noteId: number, currentContent: string | null, appendedText: string) => void;
  onDueDateChange?: (noteId: number, dueDateStr: string) => void;
}) {
  const [over, setOver] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    if (!droppable) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    setOver(true);
  };

  const handleDragLeave = () => setOver(false);

  const handleDrop = (e: React.DragEvent) => {
    if (!droppable || targetQ == null) return;
    e.preventDefault();
    try {
      const id = e.dataTransfer.getData("placementId");
      if (id && !isNaN(Number(id))) {
        onDrop(Number(id), targetQ);
      }
    } finally {
      setOver(false);
    }
  };

  return (
    <div
      role="region"
      aria-label={`${title} カラム`}
      className={`rounded-xl border-2 border-dashed p-4 transition-colors ${over ? "border-[var(--primary)] bg-green-50/50" : "border-[var(--border)] bg-white"
        }`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <h2 className="mb-3 font-semibold text-zinc-700">{title}</h2>
      <div className="flex flex-col gap-2">
        {placements.map((p) => (
          <NoteCard
            key={p.id}
            placement={p}
            draggable
            takenBy={p.taken_by}
            onAppendContent={onAppendContent}
            onDueDateChange={onDueDateChange}
            onDragEnd={onRefresh}
          />
        ))}
      </div>
    </div>
  );
}