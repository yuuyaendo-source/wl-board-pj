"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import LinkifiedText from "./LinkifiedText";
import type { PlacementWithNote, TakenByUser } from "@/lib/types";

interface NoteCardProps {
  placement: PlacementWithNote;
  showAiBadge?: boolean;
  /** パーソナル投稿（自分で作成）の印。タスクへ移動したら表示しない */
  showPersonalBadge?: boolean;
  draggable?: boolean;
  /** ドラッグ時に dataTransfer に追加でセットする値（Personal のゴミ箱/タスクリリース制限用） */
  dragData?: Record<string, string>;
  /** Task/Personal の付箋色（未指定時は placement.task_color または黄） */
  cardColor?: "yellow" | "green" | "grey" | "blue" | "red" | "purple";
  /** カレンダー由来の付箋印 */
  showCalendarBadge?: boolean;
  /** Task 用: 引き取り者（短縮名アイコン表示） */
  takenBy?: TakenByUser[];
  /** 追記コールバック（指定時は追記入力欄を表示。付箋は追記のみ） */
  onAppendContent?: (noteId: number, currentContent: string | null, appendedText: string) => void;
  /** 期限変更コールバック。YYYY-MM-DD 文字列（クリア時は ""） */
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

/** JSTを基準として、due_date（YYYY-MM-DD）の期限に応じた背景色・文字色を返す */
function getDueDateColor(dueDateStr: string | null | undefined): string {
  if (!dueDateStr) return "text-zinc-600 bg-zinc-200";

  const now = new Date();
  const jstFormatter = new Intl.DateTimeFormat('ja-JP', { timeZone: 'Asia/Tokyo', year: 'numeric', month: '2-digit', day: '2-digit' });
  const parts = jstFormatter.formatToParts(now);
  const jstDateStr = `${parts.find(p => p.type === 'year')?.value}-${parts.find(p => p.type === 'month')?.value}-${parts.find(p => p.type === 'day')?.value}`;

  if (dueDateStr < jstDateStr) {
    return "bg-red-500 text-white"; // 期限切れ (強く強調)
  } else if (dueDateStr === jstDateStr) {
    return "bg-orange-500 text-white"; // 今日 (強調)
  } else {
    return "bg-zinc-200 text-zinc-700"; // 未来 (控えめ)
  }
}

/** 期限バッジのスタイル（残り日数に応じて色を動的に変える） */
function DueDateBadge({
  dueDate,
  onClick,
}: {
  dueDate: string | null | undefined;
  onClick?: () => void;
}) {
  if (!dueDate) return null;

  const badgeCls = getDueDateColor(dueDate);
  return (
    <span
      onClick={(e) => { e.stopPropagation(); onClick?.(); }}
      className={`inline-flex cursor-pointer items-center gap-1 rounded px-2 py-0.5 text-[11px] font-bold leading-tight transition-opacity hover:opacity-80 shadow-sm ${badgeCls}`}
      title={`期限: ${dueDate}`}
    >
      📅 {dueDate}
    </span>
  );
}

/** カレンダー日付入力UI（インライン） */
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

  const handleSave = () => {
    onSave(noteId, value); // value は "" (クリア) or "YYYY-MM-DD"
    onClose();
  };

  const handleClear = () => {
    onSave(noteId, "");
    onClose();
  };

  return (
    <div
      className="mt-1 flex items-center gap-1 rounded-lg border border-zinc-200 bg-white p-1.5 shadow-md"
      onClick={(e) => e.stopPropagation()}
    >
      <input
        type="date"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        className="rounded border border-zinc-300 px-1.5 py-0.5 text-xs"
      />
      <button
        type="button"
        onClick={handleSave}
        className="rounded bg-blue-500 px-2 py-0.5 text-[10px] font-medium text-white hover:bg-blue-600"
      >
        保存
      </button>
      {currentDueDate && (
        <button
          type="button"
          onClick={handleClear}
          className="rounded bg-zinc-200 px-2 py-0.5 text-[10px] font-medium text-zinc-600 hover:bg-zinc-300"
        >
          クリア
        </button>
      )}
      <button
        type="button"
        onClick={onClose}
        className="text-[10px] text-zinc-400 hover:text-zinc-600"
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
              title="パーソナル投稿（自分で作成）"
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
        <div>
          <DueDateBadge
            dueDate={placement.due_date}
            onClick={() => onDueDateChange && setShowDatePicker((v) => !v)}
          />
        </div>
      )}

      {/* 期限未設定の場合：設定ボタン */}
      {!placement.due_date && onDueDateChange && (
        <button
          type="button"
          onClick={(e) => { e.stopPropagation(); setShowDatePicker((v) => !v); }}
          className="w-fit text-[10px] text-zinc-400 hover:text-zinc-600"
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
            className="min-w-0 flex-1 resize-none rounded border border-zinc-300 px-2 py-1 text-xs"
          />
          <button
            type="button"
            onClick={handleSubmitAppend}
            className="shrink-0 self-end rounded px-2 py-1 text-xs font-medium text-gray-300 hover:bg-amber-300"
          >
            追記
          </button>
        </div>
      )}
    </div>
  );

  const className = `rounded-xl border border-[var(--border)] p-3 shadow-sm ${bg} ${draggable ? "cursor-grab active:cursor-grabbing" : ""
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