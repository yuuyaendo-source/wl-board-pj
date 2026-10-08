"use client";

import { useState, useCallback, useRef } from "react";
import { formatWithDay } from "@shared/utils/dueDate";

interface OneLineInputProps {
  placeholder?: string;
  onSubmit: (text: string, dueDate?: string | null) => void | Promise<void>;
  disabled?: boolean;
}

export default function OneLineInput({ placeholder = "入力して Enter", onSubmit, disabled }: OneLineInputProps) {
  const [value, setValue] = useState("");
  const [dueDate, setDueDate] = useState<string>("");
  const dateInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      const t = value.trim();
      if (!t || disabled) return;
      setValue("");
      setDueDate("");
      await onSubmit(t, dueDate || null);
    },
    [value, dueDate, disabled, onSubmit]
  );

  const handleOpenPicker = () => {
    if (disabled) return;
    if (dateInputRef.current) {
      if (typeof dateInputRef.current.showPicker === "function") {
        try {
          dateInputRef.current.showPicker();
        } catch {
          dateInputRef.current.focus();
        }
      } else {
        dateInputRef.current.click();
      }
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2" autoComplete="off">
      <input
        type="text"
        name="board_memo_line"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        autoComplete="off"
        {...{ "data-1p-ignore": true }}
        {...{ "data-lpignore": true }}
        className="flex-1 rounded-lg border border-zinc-300 bg-white px-3 py-2 text-zinc-900 placeholder-zinc-400 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 dark:border-zinc-600 dark:bg-zinc-900 dark:text-zinc-100"
      />

      <div className="relative flex items-center">
        <button
          type="button"
          onClick={handleOpenPicker}
          disabled={disabled}
          className="flex items-center gap-1.5 rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-50 disabled:opacity-50 dark:border-zinc-600 dark:bg-zinc-900 dark:text-zinc-200 cursor-pointer"
          title="期限を設定"
        >
          <span>{dueDate ? formatWithDay(dueDate) : "期限を設定"}</span>
          <span>📅</span>
        </button>

        {dueDate && (
          <button
            type="button"
            onClick={() => setDueDate("")}
            className="ml-1 text-xs text-zinc-400 hover:text-zinc-600 p-1 cursor-pointer"
            title="期限をクリア"
          >
            ✕
          </button>
        )}

        <input
          ref={dateInputRef}
          type="date"
          value={dueDate}
          onChange={(e) => setDueDate(e.target.value)}
          disabled={disabled}
          className="sr-only"
          tabIndex={-1}
        />
      </div>

      <button
        type="submit"
        disabled={disabled || !value.trim()}
        className="rounded-lg bg-amber-500 px-4 py-2 font-medium text-white hover:bg-amber-600 disabled:opacity-50 cursor-pointer"
      >
        投稿
      </button>
    </form>
  );
}