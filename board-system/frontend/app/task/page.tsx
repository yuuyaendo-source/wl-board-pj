"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import type { PlacementWithNote } from "@/lib/types";
import { PERSONAL_MEMBERS } from "@/lib/personalMembers";
import ApiErrorBanner from "../components/ApiErrorBanner";
import NoteCard from "../components/NoteCard";

// 付箋ボード（02_1）のベースURL。取り込み時に /api/boards/wl/notes を取得
const POSTIT_BOARD_URL =
  process.env.NEXT_PUBLIC_LEGACY_BOARD_URL || "http://localhost:3000";
const POSTIT_BOARD_ID = "wl";

const QUADRANTS = [
  { q: 1, title: "緊急・重要", cx: 75, cy: 75 },
  { q: 2, title: "重要", cx: 25, cy: 75 },
  { q: 3, title: "緊急", cx: 75, cy: 25 },
  { q: 4, title: "その他", cx: 25, cy: 25 },
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

  const byQuadrant = placements.reduce(
    (acc, p) => {
      const q = p.matrix_quadrant ?? 4;
      if (!acc[q]) acc[q] = [];
      acc[q].push(p);
      return acc;
    },
    {} as Record<number, PlacementWithNote[]>
  );

  const handleDrop = useCallback(
    async (placementId: number, quadrant: number) => {
      const { cx, cy } = QUADRANTS.find((x) => x.q === quadrant) ?? QUADRANTS[3];
      await api.boardPlacements.patch(placementId, {
        position_x: cx,
        position_y: cy,
        matrix_quadrant: quadrant,
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
    <div className="mx-auto max-w-5xl px-6 py-8">
      <h1 className="mb-2 text-xl font-bold">Task Board（4事象）</h1>
      <p className="mb-4 text-sm text-zinc-500">
        付箋をドラッグして象限で振り分け。メンバー名にドロップでパーソナルボードへコピー。
      </p>

      <div className="mb-6 flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={handleImportFromPostit}
          disabled={importing}
          className="rounded-xl px-4 py-2 text-sm font-medium text-white transition-colors disabled:opacity-50"
          style={{ background: "var(--primary)" }}
        >
          {importing ? "取り込み中…" : "付箋ボードから取り込む"}
        </button>
        {importMessage && (
          <span className="text-sm text-zinc-500">{importMessage}</span>
        )}
      </div>

      <div className="mb-6 rounded-xl border border-[var(--border)] bg-white p-4 shadow-sm">
        <h2 className="mb-2 text-sm font-semibold text-zinc-600">
          パーソナルボードへコピー（付箋をメンバーにドロップ）
        </h2>
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

      <div className="mb-6 flex items-center gap-4">
        <span className="text-sm text-zinc-500">ゴミ箱（付箋をドロップで削除・付箋ボードからも削除）</span>
        <TrashDropZone onDrop={handleTrashDrop} />
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {QUADRANTS.map(({ q, title }) => (
          <QuadrantDropZone
            key={q}
            quadrant={q}
            title={title}
            placements={byQuadrant[q] ?? []}
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
      className={`flex items-center gap-2 rounded-xl border-2 border-dashed px-4 py-3 text-sm transition-colors ${
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
  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setOver(false);
  };
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setOver(false);
    const noteId = e.dataTransfer.getData("noteId") || e.dataTransfer.getData("text/plain");
    if (noteId) onDrop(Number(noteId));
  };

  return (
    <div
      className={`min-w-[120px] rounded-xl border-2 border-dashed px-4 py-2 text-sm transition-colors ${
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

function QuadrantDropZone({
  quadrant,
  title,
  placements,
  onDrop,
  onRefresh,
}: {
  quadrant: number;
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
      className={`min-h-[200px] rounded-xl border-2 border-dashed border-[var(--border)] bg-white p-4 transition-colors ${
        over ? "border-[var(--primary)] bg-green-50/50" : ""
      }`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <h2 className="mb-3 font-semibold text-zinc-700">{title}</h2>
      <div className="flex flex-col gap-2">
        {placements.map((p) => (
          <NoteCard key={p.id} placement={p} draggable onDragEnd={onRefresh} />
        ))}
      </div>
    </div>
  );
}
