"use client";

const API_URL = typeof window !== "undefined" ? (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") : "http://localhost:8000";

function isNetworkError(message: string): boolean {
  const m = message.toLowerCase();
  return (
    m.includes("failed to fetch") ||
    m.includes("load failed") ||
    m.includes("networkerror") ||
    m.includes("network error") ||
    m.includes("connection refused") ||
    m.includes("err_connection_refused")
  );
}

interface ApiErrorBannerProps {
  error: string;
  onRetry?: () => void;
}

export default function ApiErrorBanner({ error, onRetry }: ApiErrorBannerProps) {
  const showBackendHint = isNetworkError(error);
  return (
    <div className="mx-auto max-w-xl rounded-lg border border-amber-200 bg-amber-50 p-6 dark:border-amber-800 dark:bg-amber-950/30">
      <p className="mb-2 font-medium text-amber-900 dark:text-amber-200">エラー: {error}</p>
      {showBackendHint && (
        <div className="mb-4 text-sm text-amber-800 dark:text-amber-300">
          <p className="mb-1">API に接続できていません。バックエンドを起動してください。</p>
          <code className="block rounded bg-amber-100 px-2 py-1 font-mono text-xs dark:bg-amber-900/50">
            cd board-system/backend
            <br />
            .venv\Scripts\Activate.ps1
            <br />
            uvicorn app.main:app --reload --port 8000
          </code>
          <p className="mt-2 text-zinc-600 dark:text-zinc-400">
            接続先: {API_URL}
          </p>
        </div>
      )}
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="rounded bg-amber-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-amber-700"
        >
          再試行
        </button>
      )}
    </div>
  );
}
