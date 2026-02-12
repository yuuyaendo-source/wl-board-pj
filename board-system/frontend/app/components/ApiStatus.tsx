"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function ApiStatus() {
  const [ok, setOk] = useState<boolean | null>(null);

  useEffect(() => {
    api
      .health()
      .then(() => setOk(true))
      .catch(() => setOk(false));
  }, []);

  if (ok === null) return <span className="text-sm text-zinc-500">API 確認中...</span>;
  if (ok)
    return <span className="text-sm text-green-600 dark:text-green-400">API 接続済み</span>;
  return (
    <div className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-200">
      <p className="font-medium">API に接続できません</p>
      <p className="mt-1 text-xs">バックエンドを起動してから各ボードを開いてください。</p>
      <code className="mt-1 block text-xs">
        cd board-system/backend → .venv\Scripts\Activate.ps1 → uvicorn app.main:app --port 8000
      </code>
    </div>
  );
}
