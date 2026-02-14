"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import type { PlacementWithNote } from "@/lib/types";
import { PERSONAL_MEMBERS } from "@/lib/personalMembers";
import ApiErrorBanner from "../components/ApiErrorBanner";
import NoteCard from "../components/NoteCard";

const POSTIT_BOARD_URL =
  process.env.NEXT_PUBLIC_LEGACY_BOARD_URL || "http://localhost:3000";
const POSTIT_BOARD_ID = "wl";

/** 5列: アイデア(1), 短期タスク(2), 長期タスク(3), 重要(4), 完了(5) */
const COLUMNS = [
  { q: 1, title: "アイデア" },
  { q: 2, title: "短期タスク" },
  { q: 3, title: "長期タスク" },
  { q: 4, title: "重要" },
  { q: 5, title: "完了" },
] as const;

type PostitNote = { id: string; text: string; author?: string; createdAt?: number };

export default function TaskBoardPage() {
  const [placements, setPlacements] = useState<PlacementWithNote[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [importing, setImporting] = useState(false);
  const [importMessage, setImportMessage] = useState<string | null>(null);

  const fetchTask = useCallback(async () => {
    try {
      setError(null);
      const list = await api.boards.task();
      setPlacements(list);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTask();
  }, [fetchTask]);

  const handleImportFromPostit = useCallback(async () => {
    setImporting(true);
    setImportMessage(null);
    try {
      const res = await fetch(`${POSTIT_BOARD_URL}/api/boards/${POSTIT_BOARD_ID}/notes`);
      if (!res.ok) throw new Error("付箋ボードの取得に失敗しました");
      const data = (await res.json()) as { notes: PostitNote[] };
      const notes = (data.notes || []).map((n) => ({
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

  const handleCopyToPersonal = useCallback(
    async (noteId: number, ownerId: number) => {
      try {
        await api.stickyNotes.moveToPersonal(noteId, {
          owner_id: ownerId,
          lane: "INBOX",
        });
        await fetchTask();
        setImportMessage("パーソナルボードにコピーしました");
        setTimeout(() => setImportMessage(null), 2000);
      } catch (err) {
        setImportMessage(err instanceof Error ? err.message : "コピーに失敗しました");
      }
    },
    [fetchTask]
  );

  const handleTrashDrop = useCallback(
    async (noteId: number) => {
      await api.stickyNotes.delete(noteId);
      await fetchTask();
    },
    [fetchTask]
  );

  const byColumn = placements.reduce(
    (acc, p) => {
      const q = p.matrix_quadrant ?? 1;
      if (!acc[q]) acc[q] = [];
      acc[q].push(p);
      return acc;
    },
    {} as Record<number, PlacementWithNote[]>
  );

  const handleDrop = useCallback(
    async (placementId: number, column: number) => {
      await api.boardPlacements.patch(placementId, {
        matrix_quadrant: column,
      });
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
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <span className="text-sm text-zinc-500">ゴミ箱</span>
          <TrashDropZone onDrop={handleTrashDrop} />
        </div>
        <div className="flex flex-col gap-2">
          <span className="text-sm text-zinc-500">パーソナルボードへコピー（付箋をメンバーにドロップ）</span>
          <div className="flex flex-wrap gap-2">
            {PERSONAL_MEMBERS.map(({ ownerId, name }) => (
              <MemberDropZone
                key={ownerId}
                name={name}
                onDrop={(noteId) => handleCopyToPersonal(noteId, ownerId)}
              />
            ))}
          </div>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
        {COLUMNS.map(({ q, title }) => (
          <ColumnDropZone
            key={q}
            column={q}
            title={title}
            placements={byColumn[q] ?? []}
            onDrop={(placementId) => handleDrop(placementId, q)}
            onRefresh={fetchTask}
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
      className={`flex items-center gap-2 rounded-xl border-2 border-dashed px-4 py-2 text-sm transition-colors ${
        over ? "border-red-400 bg-red-50" : "border-zinc-300 bg-zinc-100"
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
      className={`min-w-[80px] rounded-xl border-2 border-dashed px-3 py-1.5 text-sm transition-colors ${
        over ? "border-[var(--primary)] bg-green-50" : "border-[var(--border)] bg-white"
      }`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {name}
    </div>
  );
}

function ColumnDropZone({
  column,
  title,
  placements,
  onDrop,
  onRefresh,
}: {
  column: number;
  title: string;
  placements: PlacementWithNote[];
  onDrop: (placementId: number) => void;
  onRefresh: () => void;
}) {
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
    const id = e.dataTransfer.getData("placementId");
    if (id) onDrop(Number(id));
  };

  return (
    <div
      className={`min-h-[200px] rounded-xl border-2 border-dashed border-[var(--border)] bg-white p-3 transition-colors ${
        over ? "border-[var(--primary)] bg-green-50/50" : ""
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
            onDragEnd={onRefresh}
          />
        ))}
      </div>
    </div>
  );
}
