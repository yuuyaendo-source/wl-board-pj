"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import LinkifiedText from "./LinkifiedText";
import type { PlacementWithNote, TakenByUser } from "@/lib/types";

interface NoteCardProps {
  placement: PlacementWithNote;
  showAiBadge?: boolean;
  showPersonalBadge?: boolean;
  draggable?: boolean;
  dragData?: Record<string, string>;
  cardColor?: "yellow" | "green" | "grey" | "blue" | "red" | "purple";
  showCalendarBadge?: boolean;
  takenBy?: TakenByUser[];
  onAppendContent?: (noteId: number, currentContent: string | null, appendedText: string) => void;
  onDueDateChange?: (noteId: number, dueDateStr: string) => void;
  onDragStart?: (e: React.DragEvent) => void;
  onDragEnd?: (e: React.DragEvent) => void;
}

const BG_COLOR = {
  yellow: "bg-[#fff9c4]",
  green: "bg-green-100 border-green-300",
  grey: "bg-zinc-300 border-zinc-300",
  blue: "bg-blue-100 border-blue-300",
  red: "bg-red-100 border-red-400",
  purple: "bg-violet-100 border-violet-300",
} as const;

/** 残り日数を計算（due_date: YYYY-MM-DD 文字列 → 整数） */
function calcDaysLeft(dueDateStr: string | null | undefined): number | null {
  if (!dueDateStr) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const [y, m, d] = dueDateStr.split("-").map(Number);
  if (!y || !m || !d) return null;
  const due = new Date(y, m - 1, d);
  due.setHours(0, 0, 0, 0);
  return Math.round((due.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
}

/** 期限に応じたカード外枠の強調スタイル */
function getDueDateBorderClass(dueDateStr: string | null | undefined): string {
  const days = calcDaysLeft(dueDateStr);
  if (days === null) return "";
  if (days < 0) return "ring-2 ring-red-500 border-red-500"; // 期限切れ: 鮮やかな赤枠
  if (days === 0) return "ring-2 ring-amber-500 border-amber-500"; // 今日: 鮮やかなオレンジ枠
  if (days <= 3) return "border-orange-400 border-2"; // 間近: オレンジ太枠
  return "";
}

/** 視認性を大幅に拡大した期限バッジ Component */
function DueDateBadge({
  dueDate,
  onClick,
}: {
  dueDate: string | null | undefined;
  onClick?: () => void;
}) {
  const days = calcDaysLeft(dueDate);
  if (days === null) return null;

  let label = "";
  let badgeCls = "";

  if (days < 0) {
    label = `⚠️ 期限切れ（${Math.abs(days)}日経過）`;
    badgeCls = "bg-red-600 text-white font-extrabold text-sm py-1 px-3 shadow-md animate-pulse";
  } else if (days === 0) {
    label = "🔥 本期日が期限！";
    badgeCls = "bg-amber-500 text-white font-extrabold text-sm py-1 px-3 shadow-md";
  } else if (days <= 3) {
    label = `⏰ 期限まであと${days}日`;
    badgeCls = "bg-orange-500 text-white font-bold text-xs py-1 px-2.5 shadow-sm";
  } else if (days <= 10) {
    label = `📅 期限まであと${days}日`;
    badgeCls = "bg-yellow-400 text-zinc-900 font-bold text-xs py-1 px-2.5 shadow-sm";
  } else {
    label = `📅 期限: ${dueDate}`;
    badgeCls = "bg-blue-100 text-blue-800 font-semibold text-xs py-1 px-2.5";
  }

  return (
    <span
      onClick={(e) => {
        e.stopPropagation();
        onClick?.();
      }}
      className={`inline-flex cursor-pointer items-center gap-1.5 rounded-lg border leading-none transition-all hover:opacity-80 hover:scale-105 ${badgeCls}`}
      title={`クリックして期限を変更 (期限: ${dueDate})`}
    >
      {label}
    </span>
  );
}

/** インライン日付入力ピッカー */
function DueDatePicker({
  noteId,
  currentDueDate,
  onSave,
  onClose,
}: {
  noteId: number;
  currentDueDate: string | null | undefined;
  onSave: (noteId: number, dateStr: string) => void;
  onClose: () => void;
}) {
  const [value, setValue] = useState(currentDueDate ?? "");

  const handleSave = (e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    onSave(noteId, value);
    onClose();
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    onSave(noteId, "");
    onClose();
  };

  return (
    <div
      className="mt-1 flex items-center gap-1.5 rounded-lg border border-zinc-200 bg-white p-2 shadow-lg z-10"
      onClick={(e) => e.stopPropagation()}
      onMouseDown={(e) => e.stopPropagation()}
    >
      <input
        type="date"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        className="rounded border border-zinc-300 px-2 py-1 text-xs text-zinc-800"
      />
      <button
        type="button"
        onClick={handleSave}
        className="rounded bg-blue-600 px-2.5 py-1 text-xs font-bold text-white hover:bg-blue-700"
      >
        保存
      </button>
      {currentDueDate && (
        <button
          type="button"
          onClick={handleClear}
          className="rounded bg-zinc-200 px-2 py-1 text-xs font-medium text-zinc-700 hover:bg-zinc-300"
        >
          クリア
        </button>
      )}
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          onClose();
        }}
        className="text-xs text-zinc-400 hover:text-zinc-600 px-1"
      >
        ✕
      </button>
    </div>
  );
}

export default function NoteCard({
  placement,
  showAiBadge = false,
  showPersonalBadge = false,
  draggable = false,
  dragData,
  cardColor,
  showCalendarBadge = false,
  takenBy = [],
  onAppendContent,
  onDueDateChange,
  onDragStart,
  onDragEnd,
}: NoteCardProps) {
  const [appendText, setAppendText] = useState("");
  const [showDatePicker, setShowDatePicker] = useState(false);
  const color = cardColor ?? placement.task_color ?? "yellow";
  const bg = BG_COLOR[color];
  const borderHighlight = getDueDateBorderClass(placement.due_date);

  const handleSubmitAppend = () => {
    const trimmed = appendText.trim();
    if (!trimmed || !onAppendContent) return;
    onAppendContent(placement.note_id, placement.note_content ?? null, trimmed);
    setAppendText("");
  };

  const content = (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-start justify-between gap-2">
        <p className="min-h-[1.5em] flex-1 whitespace-pre-wrap text-sm font-medium text-zinc-900 break-words">
          {placement.note_content ? (
            <LinkifiedText text={placement.note_content} />
          ) : (
            "（空）"
          )}
        </p>
        <div className="flex shrink-0 items-center gap-1">
          {showCalendarBadge && (
            <span
              className="inline-flex h-5 w-5 items-center justify-center rounded bg-violet-500 text-[10px] font-bold text-white"
              title="カレンダー予定"
            >
              C
            </span>
          )}
          {showPersonalBadge && (
            <span
              className="inline-flex h-5 w-5 items-center justify-center rounded bg-blue-500 text-[10px] font-bold text-white"
              title="パーソナル投稿"
            >
              P
            </span>
          )}
          {showAiBadge && (
            <span className="text-amber-600 dark:text-amber-400" title="AI が配置">
              ✨
            </span>
          )}
          {placement.matrix_quadrant === 4 && (
            <span
              className="inline-flex h-5 w-5 items-center justify-center rounded bg-amber-500 text-[10px] font-bold text-white shadow-sm"
              title="重要"
            >
              ⭐
            </span>
          )}
        </div>
      </div>

      {/* 期限バッジ */}
      {placement.due_date && (
        <div className="mt-0.5">
          <DueDateBadge
            dueDate={placement.due_date}
            onClick={() => onDueDateChange && setShowDatePicker((v) => !v)}
          />
        </div>
      )}

      {/* 期限未設定時の設定ボタン */}
      {!placement.due_date && onDueDateChange && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            setShowDatePicker((v) => !v);
          }}
          className="w-fit text-xs text-zinc-400 hover:text-zinc-600 font-medium"
        >
          📅 期限を設定
        </button>
      )}

      {/* 日付ピッカー */}
      {showDatePicker && onDueDateChange && (
        <DueDatePicker
          noteId={placement.note_id}
          currentDueDate={placement.due_date}
          onSave={onDueDateChange}
          onClose={() => setShowDatePicker(false)}
        />
      )}

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
      {onAppendContent && (
        <div className="mt-1 flex gap-1" onClick={(e) => e.stopPropagation()}>
          <textarea
            value={appendText}
            onChange={(e) => setAppendText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSubmitAppend();
              }
            }}
            placeholder="追記... (Shift+Enter:改行)"
            rows={2}
            name="note_append_text"
            autoComplete="off"
            {...{ "data-1p-ignore": true }}
            {...{ "data-lpignore": true }}
            className="min-w-0 flex-1 resize-none rounded border border-zinc-300 px-2 py-1 text-xs text-zinc-900"
          />
          <button
            type="button"
            onClick={handleSubmitAppend}
            className="shrink-0 self-end rounded px-2 py-1 text-xs font-medium text-zinc-600 hover:bg-amber-300"
          >
            追記
          </button>
        </div>
      )}
    </div>
  );

  const className = `rounded-xl border p-3 shadow-sm ${bg} ${borderHighlight} ${draggable ? "cursor-grab active:cursor-grabbing" : ""
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