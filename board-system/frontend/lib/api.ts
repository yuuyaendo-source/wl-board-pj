const BASE = typeof window !== "undefined" ? (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") : "";
export const API_BASE = BASE;

function normalizeErrorMessage(status: number, body: string): string {
  const trimmed = body.trim();
  // HTML が返った場合（404 ページ・エラーページ等）は短いメッセージに置き換え
  if (trimmed.startsWith("<") || trimmed.startsWith("<!")) {
    if (status === 404) {
      return "API の URL が誤っているか、指定したパスが存在しません。NEXT_PUBLIC_API_URL を確認してください。";
    }
    return `サーバーエラー（${status}）。API の接続先を確認してください。`;
  }
  // JSON の detail を優先（FastAPI の HTTPException 等）
  if (trimmed.startsWith("{")) {
    try {
      const o = JSON.parse(trimmed) as { detail?: string };
      if (typeof o.detail === "string" && o.detail) return o.detail;
    } catch {
      // ignore
    }
  }
  if (trimmed.length > 300) return trimmed.slice(0, 300) + "...";
  return trimmed || `HTTP ${status}`;
}

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    cache: "no-store",
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(normalizeErrorMessage(res.status, text));
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

import type { LaneType, PlacementWithNote, User } from "./types";

export const api = {
  health: () => fetchApi<{ status: string }>("/health"),

  users: {
    list: () => fetchApi<User[]>("/users"),
    create: (body: { name: string; email?: string; call_name?: string; role?: string }) =>
      fetchApi<User>("/users", { method: "POST", body: JSON.stringify(body) }),
    update: (userId: number, body: { name?: string; email?: string; call_name?: string; role?: string }) =>
      fetchApi<User>(`/users/${userId}`, { method: "PATCH", body: JSON.stringify(body) }),
    delete: (userId: number) =>
      fetchApi<undefined>(`/users/${userId}`, { method: "DELETE" }),
  },

  stickyNotes: {
    list: () => fetchApi<unknown[]>("/sticky_notes"),
    create: (body: {
      content: string;
      author_id?: number;
      postit_board_id?: string;
      postit_note_id?: string;
      personal_only?: boolean;
    }) => fetchApi<{ id: number }>("/sticky_notes", { method: "POST", body: JSON.stringify(body) }),
    /** パーソナルボードに直接投稿（1リクエストで create + Personal 配置。move_to_personal の 404 を防ぐ） */
    createPersonal: (body: { content: string; owner_id: number; lane?: LaneType }) =>
      fetchApi<{ id: number; note_id: number }>("/sticky_notes/create_personal", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    /** 付箋ボードから一括取り込み（重複はスキップ） */
    importFromPostit: (body: { board_id: string; notes: { id: string; text: string }[] }) =>
      fetchApi<{ created: number; skipped: number }>("/sticky_notes/import_from_postit", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    delete: (noteId: number) =>
      fetchApi<undefined>(`/sticky_notes/${noteId}`, { method: "DELETE" }),
    /** 付箋の content を更新（追記反映。付箋ボード連携付箋の場合は付箋ボード側にも同期される） */
    update: (noteId: number, body: { content?: string; status?: string }) =>
      fetchApi<unknown>(`/sticky_notes/${noteId}`, { method: "PATCH", body: JSON.stringify(body) }),
    moveToPersonal: (noteId: number, body: { owner_id: number; lane?: LaneType }) =>
      fetchApi<unknown>(`/sticky_notes/${noteId}/move_to_personal`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    releaseToTask: (noteId: number) =>
      fetchApi<unknown>(`/sticky_notes/${noteId}/release_to_task_board`, { method: "POST" }),
  },

  boardPlacements: {
    list: (params?: { board_type?: string; owner_id?: number }) => {
      const q = new URLSearchParams();
      if (params?.board_type) q.set("board_type", params.board_type);
      if (params?.owner_id != null) q.set("owner_id", String(params.owner_id));
      const query = q.toString();
      return fetchApi<{ id: number; note_id: number; board_type: string }[]>(
        `/board_placements${query ? `?${query}` : ""}`
      );
    },
    patch: (
      id: number,
      body: {
        lane?: LaneType;
        position_x?: number;
        position_y?: number;
        matrix_quadrant?: number;
        sort_order?: number;
      }
    ) => fetchApi<unknown>(`/board_placements/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    delete: (placementId: number) =>
      fetchApi<undefined>(`/board_placements/${placementId}`, { method: "DELETE" }),
  },

  boards: {
    main: () => fetchApi<PlacementWithNote[]>("/boards/main"),
    task: () => fetchApi<PlacementWithNote[]>("/boards/task"),
    personal: (ownerId: number) => fetchApi<PlacementWithNote[]>(`/boards/personal?owner_id=${ownerId}`),
    morning: () => fetchApi<PlacementWithNote[]>("/boards/morning"),
  },

  /** パーソナルサマリ（今日の予定 + Today）。owner_id を person_id として GET。カレンダー連携表示用 */
  personalSummary: (ownerId: number) =>
    fetchApi<{ events: { summary?: string; start?: string; end?: string }[]; today: { label?: string; summary?: string; start?: string; end?: string }[] }>(
      `/api/personal/${ownerId}/summary`
    ),
  /** Google カレンダーから今日の予定を取得してキャッシュに保存。その後 personalSummary を再取得すると反映される。 */
  personalCalendarRefresh: (ownerId: number) =>
    fetchApi<{ ok: boolean; events_count: number }>(`/api/personal/${ownerId}/calendar/refresh`, { method: "POST" }),

  dailyReset: {
    messages: (ownerId: number) =>
      fetchApi<{ owner_id: number; messages: string[] }>(`/daily_reset/messages?owner_id=${ownerId}`),
    /** 全ユーザーの Personal Today を MORNING にコピー（毎朝 10:15 の cron 用・テスト用） */
    syncToMorning: () =>
      fetchApi<{ ok: boolean; created: number }>("/daily_reset/sync_to_morning", { method: "POST" }),
  },
};
