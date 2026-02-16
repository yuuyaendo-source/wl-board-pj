"use client";

import { motion } from "framer-motion";
import type { PlacementWithNote, TakenByUser } from "@/lib/types";

interface NoteCardProps {
  placement: PlacementWithNote;
  showAiBadge?: boolean;
  draggable?: boolean;
  /** ドラッグ時に dataTransfer に追加でセットする値（Personal のゴミ箱/タスクリリース制限用） */
  dragData?: Record<string, string>;
  /** Task/Personal の付箋色（未指定時は placement.task_color または黄） */
  cardColor?: "yellow" | "green" | "grey" | "blue" | "red";
  /** Task 用: 引き取り者（短縮名アイコン表示） */
  takenBy?: TakenByUser[];
  onDragStart?: (e: React.DragEvent) => void;
  onDragEnd?: (e: React.DragEvent) => void;
}

const BG_COLOR = {
  yellow: "bg-[#fff9c4]",
  green: "bg-green-100 border-green-300",
  grey: "bg-zinc-200 border-zinc-400",
  blue: "bg-blue-100 border-blue-300",
  red: "bg-red-100 border-red-400",
} as const;

export default function NoteCard({
  placement,
  showAiBadge = false,
  draggable = false,
  dragData,
  cardColor,
  takenBy = [],
  onDragStart,
  onDragEnd,
}: NoteCardProps) {
  const color = cardColor ?? placement.task_color ?? "yellow";
  const bg = BG_COLOR[color];

  const content = (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-start justify-between gap-2">
        <p className="min-h-[1.5em] flex-1 whitespace-pre-wrap text-sm font-medium text-zinc-900">
          {placement.note_content || "（空）"}
        </p>
        {showAiBadge && (
          <span className="shrink-0 text-amber-600 dark:text-amber-400" title="AI が配置">
            ✨
          </span>
        )}
      </div>
      {takenBy.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {takenBy.map((u) => (
            <span
              key={u.id}
              className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-white/80 text-xs font-medium text-zinc-600 shadow-sm"
              title={u.name}
            >
              {u.name_short}
            </span>
          ))}
        </div>
      )}
    </div>
  );

  const className = `rounded-xl border border-[var(--border)] p-3 shadow-sm ${bg} ${
    draggable ? "cursor-grab active:cursor-grabbing" : ""
  }`;

  if (draggable) {
    return (
      <motion.div layout initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} whileHover={{ scale: 1.02 }}>
        <div
          className={className}
          draggable
          onDragStart={(e) => {
            const noteIdStr = String(placement.note_id);
            e.dataTransfer.setData("placementId", String(placement.id));
            e.dataTransfer.setData("noteId", noteIdStr);
            e.dataTransfer.setData("text/plain", noteIdStr);
            if (dragData) {
              Object.entries(dragData).forEach(([k, v]) => e.dataTransfer.setData(k, v));
              // dragover では getData が空になるブラウザがあるため、Task リリース用に型だけ付与（drop ゾーンで types を参照）
              // isFromTask: タスク由来の付箋をリリース（配置削除）。canReleaseToTask: パーソナル投稿もタスクへ追加可能
              if (dragData.isFromTask === "true" || dragData.canReleaseToTask === "true") {
                e.dataTransfer.setData("application/x-board-task-release", "1");
              }
            }
            e.dataTransfer.effectAllowed = "copyMove";
            onDragStart?.(e);
          }}
          onDragEnd={onDragEnd}
        >
          {content}
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      className={className}
    >
      {content}
    </motion.div>
  );
}
