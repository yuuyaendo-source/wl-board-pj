"use client";

import { useState, useCallback } from "react";

interface OneLineInputProps {
  placeholder?: string;
  onSubmit: (text: string) => void | Promise<void>;
  disabled?: boolean;
}

export default function OneLineInput({ placeholder = "入力して Enter", onSubmit, disabled }: OneLineInputProps) {
  const [value, setValue] = useState("");
  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      const t = value.trim();
      if (!t || disabled) return;
      setValue("");
      await onSubmit(t);
    },
    [value, disabled, onSubmit]
  );
  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        className="flex-1 rounded-lg border border-zinc-300 bg-white px-3 py-2 text-zinc-900 placeholder-zinc-400 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 dark:border-zinc-600 dark:bg-zinc-900 dark:text-zinc-100"
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        className="rounded-lg bg-amber-500 px-4 py-2 font-medium text-white hover:bg-amber-600 disabled:opacity-50"
      >
        投稿
      </button>
    </form>
  );
}
