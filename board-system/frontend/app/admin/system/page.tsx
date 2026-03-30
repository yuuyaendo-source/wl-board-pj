"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";

type LlmStatus = Awaited<ReturnType<typeof api.admin.llm.get>>;

export default function AdminSystemPage() {
  const [status, setStatus] = useState<LlmStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState<number | "env">(1);

  const load = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      const s = await api.admin.llm.get();
      setStatus(s);
      if (s.db_llm_target != null) {
        setDraft(s.db_llm_target);
      } else {
        setDraft("env");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "読み込みに失敗しました");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const saveSlot = async (slot: number) => {
    setSaving(true);
    setError(null);
    try {
      const s = await api.admin.llm.put({ llm_target: slot });
      setStatus(s);
      setDraft(slot);
    } catch (e) {
      setError(e instanceof Error ? e.message : "保存に失敗しました");
    } finally {
      setSaving(false);
    }
  };

  const clearDbOverride = async () => {
    setSaving(true);
    setError(null);
    try {
      const s = await api.admin.llm.put({ llm_target: null });
      setStatus(s);
      setDraft("env");
    } catch (e) {
      setError(e instanceof Error ? e.message : "保存に失敗しました");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mx-auto max-w-lg px-4 py-8">
      <p className="mb-4 text-sm text-zinc-500">
        <Link href="/taskboard" className="text-[var(--primary)] hover:underline">
          ← Task ボードへ
        </Link>
      </p>
      <h1 className="mb-2 text-xl font-semibold text-zinc-800">システム管理</h1>
      <p className="mb-6 text-sm text-zinc-600">
        運用向けの設定をまとめます。項目は今後追加できます。
      </p>

      {loading && <p className="text-sm text-zinc-500">読込中…</p>}
      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

      {!loading && status && (
        <section
          id="llm"
          className="space-y-4 scroll-mt-20 rounded-xl border border-[var(--border)] bg-white p-4 shadow-sm"
          aria-labelledby="llm-heading"
        >
          <h2 id="llm-heading" className="text-sm font-medium text-zinc-800">
            LLM切替
          </h2>
          <p className="text-xs text-zinc-500">
            Ollama エンドポイント 1〜3 の切替。URL は環境変数の OLLAMA_URL_n / OLLAMA_URL で定義します。
          </p>
          <div className="text-xs text-zinc-500 space-y-1">
            <p>環境変数 LLM_TARGET: {status.env_llm_target ?? "（未設定）"}</p>
            <p>DB 上書き: {status.db_llm_target ?? "（なし・env に従う）"}</p>
            <p className="font-medium text-zinc-700">実効スロット: {status.effective_llm_target ?? "（なし・OLLAMA_URL のみ）"}</p>
            <p className="break-all">解決 URL: {status.resolved_url ?? "—"}</p>
            <p>
              モデル: {status.model_mode === "fixed" ? `固定 (${status.model_override})` : "自動解決"}
            </p>
          </div>

          <div className="flex flex-col gap-2 border-t border-[var(--border)] pt-3">
            <p className="text-xs text-zinc-500">接続先スロット</p>
            {([1, 2, 3] as const).map((n) => (
              <label key={n} className="flex cursor-pointer items-center gap-2 text-sm text-zinc-700">
                <input
                  type="radio"
                  name="llm_slot"
                  checked={draft === n}
                  onChange={() => setDraft(n)}
                  disabled={saving}
                />
                <span>スロット {n}（OLLAMA_URL_{n}）</span>
              </label>
            ))}
            <label className="flex cursor-pointer items-center gap-2 text-sm text-zinc-700">
              <input
                type="radio"
                name="llm_slot"
                checked={draft === "env"}
                onChange={() => setDraft("env")}
                disabled={saving}
              />
              <span>DB 上書きをやめて環境変数 LLM_TARGET に従う</span>
            </label>
          </div>

          <div className="flex flex-wrap gap-2">
            {draft !== "env" && typeof draft === "number" && (
              <button
                type="button"
                disabled={saving}
                onClick={() => void saveSlot(draft)}
                className="rounded-lg bg-[var(--primary)] px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
              >
                {saving ? "保存中…" : "選択したスロットを保存"}
              </button>
            )}
            {draft === "env" && (
              <button
                type="button"
                disabled={saving}
                onClick={() => void clearDbOverride()}
                className="rounded-lg border border-[var(--border)] px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 disabled:opacity-50"
              >
                {saving ? "保存中…" : "環境変数に従う（DB 上書き解除）"}
              </button>
            )}
          </div>
        </section>
      )}
    </div>
  );
}
