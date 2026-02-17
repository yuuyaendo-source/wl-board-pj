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
      // 楽観的更新: すぐ一覧に表示してからサーバーと同期
      const tempId = -note.id;
      setByLane((prev) => ({
        ...prev,
        INBOX: [
          {
            id: tempId,
            note_id: note.id,
            board_type: "PERSONAL",
            owner_id: ownerId,
            lane: "INBOX",
            position_x: null,
            position_y: null,
            matrix_quadrant: null,
            sort_order: 0,
            note_content: text,
            note_status: "ACTIVE",
            is_from_task: false,
          } as PlacementWithNote,
          ...prev.INBOX,
        ],
      }));
      await fetchPersonal();
    },
    [ownerId, fetchPersonal]
  );

  const handleDrop = useCallback(
    async (placementId: number, targetLane: LaneType) => {
      setError(null);
      // 楽観的更新: 1回の操作で即反映
      setByLane((prev) => {
        let placement: PlacementWithNote | null = null;
        const next = { ...prev };
        for (const key of Object.keys(next) as LaneType[]) {
          const idx = next[key].findIndex((p) => p.id === placementId);
          if (idx >= 0) {
            placement = { ...next[key][idx], lane: targetLane };
            next[key] = next[key].filter((_, i) => i !== idx);
            break;
          }
        }
        if (placement) next[targetLane] = [...next[targetLane], placement];
        return next;
      });
      await api.boardPlacements.patch(placementId, { lane: targetLane });
      await fetchPersonal();
    },
    [fetchPersonal]
  );

  const handleTrashDrop = useCallback(
    async (noteId: number) => {
      setError(null);
      try {
        await api.stickyNotes.delete(noteId);
        await fetchPersonal();
      } catch (e) {
        setError(e instanceof Error ? e.message : "削除に失敗しました");
      }
    },
    [fetchPersonal]
  );

  /** 付箋をタスクボードへ。Task 由来・パーソナル投稿どちらも releaseToTask(noteId) で統一（404 回避） */
  const handleReleaseToTask = useCallback(
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

  if (loading) return <div className="p-6">Loading...</div>;
  if (error)
    return (
      <div className="p-6">
        <ApiErrorBanner error={error} onRetry={fetchPersonal} />
      </div>
    );

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      {/* スクロール時も入力・投稿・ゴミ箱・タスクボードへが追従する */}
      <div className="sticky top-[52px] z-10 -mx-6 bg-white px-6 pb-4 pt-2 shadow-[0_1px_0_0_var(--border)]">
        <h1 className="mb-4 text-xl font-bold">パーソナルボード — {displayName}</h1>
        <OneLineInput placeholder="タスクやメモを入力..." onSubmit={handlePost} />

        <div className="mt-6 flex flex-row flex-nowrap items-center gap-3 rounded-xl border border-[var(--border)] bg-white p-4 shadow-sm">
          <PersonalTrashDropZone onDrop={handleTrashDrop} />
          <PersonalTaskReleaseDropZone onDropToTask={handleReleaseToTask} />
        </div>
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

function PersonalTaskReleaseDropZone({ onDropToTask }: { onDropToTask: (noteId: number) => void | Promise<void> }) {
  const [over, setOver] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
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
    await Promise.resolve(onDropToTask(Number(noteIdStr)));
  };

  return (
    <div
      className={`flex items-center gap-2 rounded-xl border-2 border-dashed px-4 py-2 text-sm transition-colors ${
        over ? "border-[var(--primary)] bg-green-50" : "border-zinc-300 bg-zinc-100"
      }`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <span>📤</span>
      <span>タスクボードへ</span>
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
            showPersonalBadge={p.is_from_task === false && lane !== "HELP_REQUEST"}
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
