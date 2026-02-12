"use client";

import { motion } from "framer-motion";
import type { PlacementWithNote } from "@/lib/types";

interface NoteCardProps {
  placement: PlacementWithNote;
  showAiBadge?: boolean;
  draggable?: boolean;
  /** ドラッグ時に dataTransfer に追加でセットする値（Personal のゴミ箱/タスクリリース制限用） */
  dragData?: Record<string, string>;
  onDragStart?: (e: React.DragEvent) => void;
  onDragEnd?: (e: React.DragEvent) => void;
}

export default function NoteCard({
  placement,
  showAiBadge = false,
  draggable = false,
  dragData,
  onDragStart,
  onDragEnd,
}: NoteCardProps) {
  const content = (
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
  );

  const className = `rounded-xl border border-[var(--border)] bg-[#fff9c4] p-3 shadow-sm ${
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
