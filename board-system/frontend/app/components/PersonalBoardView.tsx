"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import type { PlacementWithNote } from "@/lib/types";
import type { LaneType } from "@/lib/types";
import ApiErrorBanner from "./ApiErrorBanner";
import NoteCard from "./NoteCard";
import OneLineInput from "./OneLineInput";

const LANES: { key: LaneType; label: string }[] = [
  { key: "TODAY", label: "Today" },
  { key: "INBOX", label: "タスク" },
  { key: "DONE", label: "Done" },
  { key: "HELP_REQUEST", label: "応援要請" },
];

export default function PersonalBoardView({
  ownerId,
  displayName,
}: {
  ownerId: number;
  displayName: string;
}) {
  const [byLane, setByLane] = useState<Record<LaneType, PlacementWithNote[]>>({
    INBOX: [],
    TODAY: [],
    DONE: [],
    HELP_REQUEST: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPersonal = useCallback(async () => {
    try {
      setError(null);
      const list = await api.boards.personal(ownerId);
      const next: Record<LaneType, PlacementWithNote[]> = { INBOX: [], TODAY: [], DONE: [], HELP_REQUEST: [] };
      for (const p of list) {
        const lane = (p.lane ?? "INBOX") as LaneType;
        if (lane in next) next[lane].push(p);
      }
      setByLane(next);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [ownerId]);

  useEffect(() => {
    fetchPersonal();
  }, [fetchPersonal]);

  const handlePost = useCallback(
    async (text: string) => {
      // personal_only: true で Task に載せず Personal のみ（青付箋）
      const note = (await api.stickyNotes.create({ content: text, personal_only: true })) as { id: number };
      await api.stickyNotes.moveToPersonal(note.id, { owner_id: ownerId, lane: "INBOX" });
      await fetchPersonal();
    },
    [ownerId, fetchPersonal]
  );

  const handleDrop = useCallback(
    async (placementId: number, targetLane: LaneType) => {
      setError(null);
      await api.boardPlacements.patch(placementId, { lane: targetLane });
      await fetchPersonal();
    },
    [fetchPersonal]
  );

  const handleTrashDrop = useCallback(
    async (noteId: number) => {
      await api.stickyNotes.delete(noteId);
      await fetchPersonal();
    },
    [fetchPersonal]
  );

  const handleTaskReleaseDrop = useCallback(
    async (placementId: number) => {
      setError(null);
      try {
        await api.boardPlacements.delete(placementId);
        await fetchPersonal();
      } catch (e) {
        setError(e instanceof Error ? e.message : "タスクリリースに失敗しました");
      }
    },
    [fetchPersonal]
  );

  /** パーソナル投稿（青）をタスクボードへ追加。Task に載っていない付箋用。 */
  const handleNoteAddToTask = useCallback(
    async (noteId: number) => {
      setError(null);
      try {
        await api.stickyNotes.releaseToTask(noteId);
        await fetchPersonal();
      } catch (e) {
        setError(e instanceof Error ? e.message : "タスクボードへの追加に失敗しました");
      }
    },
    [fetchPersonal]
  );

  // タスクリリースで placementId が取れないブラウザ用: noteId から配置IDを解決
  const fromTaskPlacements = [...byLane.INBOX, ...byLane.TODAY, ...byLane.DONE, ...byLane.HELP_REQUEST].filter(
    (p) => p.is_from_task
  );
  const getReleasePlacementId = useCallback(
    (noteId: number) => fromTaskPlacements.find((p) => p.note_id === noteId)?.id ?? null,
    [fromTaskPlacements]
  );

  if (loading) return <div className="p-6">Loading...</div>;
  if (error)
    return (
      <div className="p-6">
        <ApiErrorBanner error={error} onRetry={fetchPersonal} />
      </div>
    );

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <h1 className="mb-4 text-xl font-bold">パーソナルボード — {displayName}</h1>
      <OneLineInput placeholder="タスクやメモを入力..." onSubmit={handlePost} />

      <div className="mt-6 flex flex-row flex-nowrap items-center gap-3 rounded-xl border border-[var(--border)] bg-white p-4 shadow-sm">
        <PersonalTrashDropZone onDrop={handleTrashDrop} />
        <PersonalTaskReleaseDropZone
          onDrop={handleTaskReleaseDrop}
          onDropNoteToTask={handleNoteAddToTask}
          getReleasePlacementId={getReleasePlacementId}
        />
      </div>

      <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-3">
        {LANES.map(({ key, label }) => (
          <LaneColumn
            key={key}
            lane={key}
            label={label}
            placements={byLane[key]}
            onDrop={(placementId) => handleDrop(placementId, key)}
            onRefresh={fetchPersonal}
          />
        ))}
      </div>
    </div>
  );
}

function PersonalTrashDropZone({ onDrop }: { onDrop: (noteId: number) => void }) {
  const [over, setOver] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    const isFromTask = e.dataTransfer.getData("isFromTask");
    if (isFromTask === "true") {
      e.dataTransfer.dropEffect = "none";
      return;
    }
    e.dataTransfer.dropEffect = "move";
    setOver(true);
  };
  const handleDragLeave = () => setOver(false);
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setOver(false);
    if (e.dataTransfer.getData("isFromTask") === "true") return;
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
      <span>🗑️</span>
      <span>ゴミ箱（Personalで作った付箋のみ）</span>
    </div>
  );
}

function PersonalTaskReleaseDropZone({
  onDrop,
  onDropNoteToTask,
  getReleasePlacementId,
}: {
  onDrop: (placementId: number) => void;
  /** パーソナル投稿（Task に載っていない付箋）をタスクボードへ追加するとき */
  onDropNoteToTask?: (noteId: number) => void;
  getReleasePlacementId?: (noteId: number) => number | null;
}) {
  const [over, setOver] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    // dragover では getData() が空になるブラウザがあるため、型の有無で判定（Task 由来 or パーソナル投稿）
    const canRelease = e.dataTransfer.types.includes("application/x-board-task-release");
    if (!canRelease) {
      e.dataTransfer.dropEffect = "none";
      return;
    }
    e.dataTransfer.dropEffect = "move";
    setOver(true);
  };
  const handleDragLeave = () => setOver(false);
  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setOver(false);
    const noteIdStr = e.dataTransfer.getData("noteId") || e.dataTransfer.getData("text/plain");
    if (!noteIdStr) return;
    const noteId = Number(noteIdStr);
    // Task 由来の付箋は配置削除でリリース。パーソナル投稿（青）は releaseToTask で Task に追加
    const placementId = getReleasePlacementId?.(noteId) ?? null;
    if (placementId != null) {
      await Promise.resolve(onDrop(placementId));
    } else if (onDropNoteToTask) {
      await Promise.resolve(onDropNoteToTask(noteId));
    }
  };

  return (
    <div
      className={`flex items-center gap-2 rounded-xl border-2 border-dashed px-4 py-2 text-sm transition-colors ${
        over ? "border-[var(--primary)] bg-green-50" : "border-zinc-300 bg-zinc-100"
      }`}
      style={over ? {} : undefined}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <span>📤</span>
      <span>タスクボードへ（Task由来はリリース、投稿付箋は追加）</span>
    </div>
  );
}

function LaneColumn({
  lane,
  label,
  placements,
  onDrop,
  onRefresh,
}: {
  lane: LaneType;
  label: string;
  placements: PlacementWithNote[];
  onDrop: (placementId: number) => void | Promise<void>;
  onRefresh: () => void;
}) {
  const [over, setOver] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    setOver(true);
  };
  const handleDragLeave = () => setOver(false);
  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setOver(false);
    const id = e.dataTransfer.getData("placementId");
    if (id) await Promise.resolve(onDrop(Number(id)));
  };

  return (
    <div
      className={`rounded-xl border-2 border-dashed border-[var(--border)] p-4 transition-colors ${
        over ? "border-[var(--primary)] bg-green-50/50" : "bg-white"
      }`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <h2 className="mb-3 font-semibold text-zinc-700">{label}</h2>
      <div className="flex flex-col gap-2">
        {placements.map((p) => (
          <NoteCard
            key={p.id}
            placement={p}
            draggable
            cardColor={
              lane === "HELP_REQUEST"
                ? "red"
                : lane === "DONE"
                  ? "grey"
                  : p.is_from_task
                    ? "green"
                    : "blue"
            }
            dragData={{ isFromTask: String(!!p.is_from_task), canReleaseToTask: "true" }}
            onDragEnd={onRefresh}
          />
        ))}
      </div>
    </div>
  );
}
