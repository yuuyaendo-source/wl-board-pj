"use client";

import { useEffect, useState, useCallback } from "react";
import { flushSync } from "react-dom";
import { api } from "@/lib/api";
import type { PlacementWithNote } from "@/lib/types";
import type { Team } from "@/lib/types";
import { usePersonalMembers } from "@/lib/personalMembers";
import ApiErrorBanner from "../components/ApiErrorBanner";
import NoteCard from "../components/NoteCard";

const POSTIT_BOARD_URL =
  process.env.NEXT_PUBLIC_LEGACY_BOARD_URL || "http://localhost:3000";
const POSTIT_BOARD_ID = "wl";

/** mutation 直後の refetch で古いレスポンスが返るのを防ぐ */
const REFETCH_DELAY_MS = 120;
const delay = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

const AUTO_IMPORT_STORAGE_KEY = "board-system:taskboard:autoImport";

function getStoredAutoImport(): boolean {
  if (typeof window === "undefined") return true;
  const stored = window.localStorage.getItem(AUTO_IMPORT_STORAGE_KEY);
  if (stored === null) return true; // 未設定時はON（バックグラウンドで実行）
  return stored === "true";
}

const COLUMNS = [
  { id: "unassigned", title: "応援要請・未振り分け", targetQ: null, droppable: false },
  { id: "ideas", title: "アイデア", targetQ: 1, droppable: true },
  { id: "tasks", title: "タスク", targetQ: 2, droppable: true },
  { id: "done", title: "完了", targetQ: 5, droppable: true },
] as const;

type PostitNote = { id: string; text: string; author?: string; createdAt?: number; gray?: boolean };

export default function TaskBoardPage() {
  const [placements, setPlacements] = useState<PlacementWithNote[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [importing, setImporting] = useState(false);
  const [importMessage, setImportMessage] = useState<string | null>(null);
  const [autoImportEnabled, setAutoImportEnabledState] = useState(true);
  const { members: personalMembers } = usePersonalMembers();
  const [teams, setTeams] = useState<Team[]>([]);

  // 初回マウント時に localStorage から復元（デフォルトはON）
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
    try {
      const res = await fetch(`${POSTIT_BOARD_URL}/api/boards/${POSTIT_BOARD_ID}/notes`);
      if (!res.ok) throw new Error("付箋ボードの取得に失敗しました");
      const data = (await res.json()) as { notes: PostitNote[] };
      const notes = (data.notes || [])
        .filter((n) => !n.gray)
        .map((n) => ({
          id: String(n.id),
          text: n.text || "",
        }));
      const result = await api.stickyNotes.importFromPostit({
        board_id: POSTIT_BOARD_ID,
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
      setImportMessage(e instanceof Error ? e.message : "取り込みに失敗しました");
    } finally {
      setImporting(false);
    }
  }, [fetchTask]);

  useEffect(() => {
    const handler = () => handleImportFromPostit();
    window.addEventListener("task-import-request", handler);
    return () => window.removeEventListener("task-import-request", handler);
  }, [handleImportFromPostit]);

  // 自動取り込み（ON 時に1回実行し、以降5分ごと）
  useEffect(() => {
    if (!autoImportEnabled) return;
    const runImport = async () => {
      try {
        const res = await fetch(`${POSTIT_BOARD_URL}/api/boards/${POSTIT_BOARD_ID}/notes`);
        if (!res.ok) return;
        const data = (await res.json()) as { notes: PostitNote[] };
        const notes = (data.notes || [])
          .filter((n) => !n.gray)
          .map((n) => ({ id: String(n.id), text: n.text || "" }));
        if (notes.length === 0) return;
        await api.stickyNotes.importFromPostit({ board_id: POSTIT_BOARD_ID, notes });
        await delay(REFETCH_DELAY_MS);
        await fetchTask();
      } catch {
        // 自動取り込みは失敗しても静かにスキップ
      }
    };
    runImport(); // 有効化直後に1回
    const interval = setInterval(runImport, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [autoImportEnabled, fetchTask]);

  const handleCopyToPersonal = useCallback(
    async (noteId: number, ownerId: number) => {
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
        setImportMessage(err instanceof Error ? err.message : "コピーに失敗しました");
      }
    },
    [fetchTask]
  );

  const handleCopyToTeam = useCallback(
    async (noteId: number, teamId: number, teamName: string) => {
      try {
        const res = await api.stickyNotes.copyToTeam(noteId, { team_id: teamId, lane: "INBOX" });
        await delay(REFETCH_DELAY_MS);
        await fetchTask();
        setImportMessage(res.message);
        setTimeout(() => setImportMessage(null), 3000);
      } catch (err) {
        setImportMessage(err instanceof Error ? err.message : `${teamName} へのコピーに失敗しました`);
        setTimeout(() => setImportMessage(null), 5000);
      }
    },
    [fetchTask]
  );

  const handleAppendContent = useCallback(
    async (noteId: number, currentContent: string | null, appendedText: string) => {
      const newContent = (currentContent || "").trim()
        ? `${(currentContent || "").trim()}\n${appendedText}`
        : appendedText;
      await api.stickyNotes.update(noteId, { content: newContent });
      await delay(REFETCH_DELAY_MS);
      await fetchTask();
    },
    [fetchTask]
  );

  // 期限変更ハンドラー
  const handleDueDateChange = useCallback(
    async (noteId: number, dueDateStr: string) => {
      await api.stickyNotes.update(noteId, {
        due_date: dueDateStr === "" ? "" : dueDateStr,
      });
      await delay(REFETCH_DELAY_MS);
      await fetchTask();
    },
    [fetchTask]
  );

  const handleTrashDrop = useCallback(
    async (noteId: number) => {
      setImportMessage(null);
      try {
        await api.stickyNotes.delete(noteId);
        await delay(REFETCH_DELAY_MS);
        await fetchTask();
      } catch (e) {
        setImportMessage(e instanceof Error ? e.message : "削除に失敗しました");
        setTimeout(() => setImportMessage(null), 5000);
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
      await api.boardPlacements.patch(placementId, {
        matrix_quadrant: column,
      });
      await delay(REFETCH_DELAY_MS);
      await fetchTask();
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
      {/* メニューバー・ゴミ箱・パーソナルへコピーはスクロールについてくる */}
      <div className="sticky top-[52px] z-10 -mx-4 border-b border-[var(--border)] bg-white px-4 py-3 shadow-sm">
        {(importing || importMessage) && (
          <div className="mb-2 text-sm text-zinc-500">
            {importing ? "取り込み中…" : importMessage}
          </div>
        )}
        <div className="mb-2 items-center justify-between gap-3">
          <button
            type="button"
            onClick={() => handleImportFromPostit()}
            disabled={importing}
            className="shrink-0 rounded-xl px-3 py-1.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
            style={{ background: "var(--primary)" }}
          >
            付箋ボードから取り込む
          </button>

          <label className="flex cursor-pointer items-center gap-2 text-sm text-zinc-600">
            <input
              type="checkbox"
              checked={autoImportEnabled}
              onChange={(e) => setAutoImportEnabled(e.target.checked)}
              className="rounded border-[var(--border)]"
            />
            <span>自動で付箋ボードから取り込む（5分ごと・AIで振り分け）※オフにするときだけチェックを外してください</span>
          </label>

        </div>
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <span className="text-sm text-zinc-500">ゴミ箱</span>
          <TrashDropZone onDrop={handleTrashDrop} />
        </div>
        <div className="flex flex-col gap-2">
          <span className="text-sm text-zinc-500">パーソナルボードへコピー（付箋をメンバーにドロップ）</span>
          <div className="flex flex-wrap gap-2">
            {personalMembers.map(({ ownerId, name }) => (
              <MemberDropZone
                key={ownerId}
                name={name}
                onDrop={(noteId) => handleCopyToPersonal(noteId, ownerId)}
              />
            ))}
          </div>
          {teams.length > 0 && (
            <>
              <span className="text-sm text-zinc-500 mt-1">チームへ一括コピー（付箋をチームにドロップ）</span>
              <div className="flex flex-wrap gap-2">
                {teams.map((team) => (
                  <TeamDropZone
                    key={team.id}
                    team={team}
                    onDrop={(noteId) => handleCopyToTeam(noteId, team.id, team.name)}
                  />
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {COLUMNS.map(({ id, title, targetQ, droppable }) => (
          <ColumnDropZone
            key={id}
            title={title}
            placements={byColumn[id] ?? []}
            onDrop={droppable && targetQ !== null ? (placementId) => handleDrop(placementId, targetQ) : undefined}
            onRefresh={fetchTask}
            onAppendContent={handleAppendContent}
            onDueDateChange={handleDueDateChange}
            droppable={droppable}
          />
        ))}
      </div>
    </div>
  );
}

function TrashDropZone({ onDrop }: { onDrop: (noteId: number) => void }) {
  const [over, setOver] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    setOver(true);
  };
  const handleDragLeave = () => setOver(false);
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setOver(false);
    const noteId = e.dataTransfer.getData("noteId");
    if (noteId) onDrop(Number(noteId));
  };

  return (
    <div
      className={`flex items-center gap-2 rounded-xl border-2 border-dashed px-4 py-2 text-sm transition-colors ${over ? "border-red-400 bg-red-50" : "border-zinc-300 bg-zinc-100"
        }`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <span className="text-lg">🗑️</span>
      <span>ゴミ箱</span>
    </div>
  );
}

function MemberDropZone({
  name,
  onDrop,
}: {
  name: string;
  onDrop: (noteId: number) => void;
}) {
  const [over, setOver] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    e.dataTransfer.dropEffect = "move";
    setOver(true);
  };
  const handleDragLeave = () => setOver(false);
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setOver(false);
    const noteId = e.dataTransfer.getData("noteId") || e.dataTransfer.getData("text/plain");
    if (noteId) onDrop(Number(noteId));
  };

  return (
    <div
      className={`min-w-[80px] rounded-xl border-2 border-dashed px-3 py-1.5 text-sm transition-colors ${over ? "border-[var(--primary)] bg-green-50" : "border-[var(--border)] bg-white"
        }`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {name}
    </div>
  );
}

function TeamDropZone({
  team,
  onDrop,
}: {
  team: { id: number; name: string; member_count: number };
  onDrop: (noteId: number) => void;
}) {
  const [over, setOver] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    e.dataTransfer.dropEffect = "move";
    setOver(true);
  };
  const handleDragLeave = () => setOver(false);
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setOver(false);
    const noteId = e.dataTransfer.getData("noteId") || e.dataTransfer.getData("text/plain");
    if (noteId) onDrop(Number(noteId));
  };

  return (
    <div
      className={`min-w-[90px] rounded-xl border-2 border-dashed px-3 py-1.5 text-sm transition-colors flex items-center gap-1.5 ${over
          ? "border-indigo-400 bg-indigo-50 text-indigo-700"
          : "border-indigo-200 bg-indigo-50/50 text-indigo-600"
        }`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <span>👥</span>
      <span className="font-medium">{team.name}</span>
      <span className="text-xs opacity-60">({team.member_count}名)</span>
    </div>
  );
}

function ColumnDropZone({
  title,
  placements,
  onDrop,
  onRefresh,
  onAppendContent,
  onDueDateChange,
  droppable = true,
}: {
  title: string;
  placements: PlacementWithNote[];
  onDrop?: (placementId: number) => void;
  onRefresh: () => void;
  onAppendContent?: (noteId: number, currentContent: string | null, appendedText: string) => void;
  onDueDateChange?: (noteId: number, dueDateStr: string) => void;
  droppable?: boolean;
}) {
  const [over, setOver] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    if (!droppable || !onDrop) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    setOver(true);
  };
  const handleDragLeave = () => setOver(false);
  const handleDrop = async (e: React.DragEvent) => {
    if (!droppable || !onDrop) return;
    e.preventDefault();
    setOver(false);
    const id = e.dataTransfer.getData("placementId");
    if (id) await Promise.resolve(onDrop(Number(id)));
  };

  return (
    <div
      className={`min-h-[200px] rounded-xl border-2 border-dashed border-[var(--border)] bg-white p-3 transition-colors ${over ? "border-[var(--primary)] bg-green-50/50" : ""
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
            cardColor={p.task_color}
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