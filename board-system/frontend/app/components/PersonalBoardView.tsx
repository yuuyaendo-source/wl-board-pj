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
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPersonal = useCallback(async () => {
    try {
      setError(null);
      const list = await api.boards.personal(ownerId);
      const next: Record<LaneType, PlacementWithNote[]> = { INBOX: [], TODAY: [], DONE: [] };
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
      const note = (await api.stickyNotes.create({ content: text })) as { id: number };
      await api.stickyNotes.moveToPersonal(note.id, { owner_id: ownerId, lane: "INBOX" });
      await fetchPersonal();
    },
    [ownerId, fetchPersonal]
  );

  const handleDrop = useCallback(
    async (placementId: number, targetLane: LaneType) => {
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
      try {
        await api.boardPlacements.delete(placementId);
        await fetchPersonal();
      } catch (e) {
        setError(e instanceof Error ? e.message : "タスクリリースに失敗しました");
      }
    },
    [fetchPersonal]
  );

  // タスクリリースで placementId が取れないブラウザ用: noteId から配置IDを解決
  const fromTaskPlacements = [...byLane.INBOX, ...byLane.TODAY, ...byLane.DONE].filter(
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
      <h1 className="mb-2 text-xl font-bold">パーソナルボード — {displayName}</h1>
      <p className="mb-4 text-sm text-zinc-500">
        1行入力でタスクに追加。D&D で Today / タスク / Done へ移動。
      </p>
      <OneLineInput placeholder="タスクやメモを入力..." onSubmit={handlePost} />

      <div className="mt-6 flex flex-wrap items-center gap-4 rounded-xl border border-[var(--border)] bg-white p-4 shadow-sm">
        <span className="text-sm text-zinc-500">ゴミ箱・タスクリリース：</span>
        <PersonalTrashDropZone onDrop={handleTrashDrop} />
        <PersonalTaskReleaseDropZone
          onDrop={handleTaskReleaseDrop}
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
  getReleasePlacementId,
}: {
  onDrop: (placementId: number) => void;
  getReleasePlacementId?: (noteId: number) => number | null;
}) {
  const [over, setOver] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    // dragover では getData() が空になるブラウザがあるため、型の有無で判定（NoteCard で Task 由来のときだけ付与）
    const canRelease = e.dataTransfer.types.includes("application/x-board-task-release");
    if (!canRelease) {
      e.dataTransfer.dropEffect = "none";
      return;
    }
    e.dataTransfer.dropEffect = "move";
    setOver(true);
  };
  const handleDragLeave = () => setOver(false);
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setOver(false);
    let placementIdStr = e.dataTransfer.getData("placementId");
    // Firefox 等で placementId が空になる場合のフォールバック
    if (!placementIdStr && getReleasePlacementId) {
      const noteId = e.dataTransfer.getData("noteId") || e.dataTransfer.getData("text/plain");
      if (noteId) {
        const resolved = getReleasePlacementId(Number(noteId));
        if (resolved != null) placementIdStr = String(resolved);
      }
    }
    if (placementIdStr) onDrop(Number(placementIdStr));
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
      <span>タスクリリース（Taskからコピーした付箋のみ）</span>
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
            dragData={{ isFromTask: String(!!p.is_from_task) }}
            onDragEnd={onRefresh}
          />
        ))}
      </div>
    </div>
  );
}
