const BASE = typeof window !== "undefined" ? (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") : "";

function normalizeErrorMessage(status: number, body: string): string {
  const trimmed = body.trim();
  // HTML が返った場合（404 ページ・エラーページ等）は短いメッセージに置き換え
  if (trimmed.startsWith("<") || trimmed.startsWith("<!")) {
    if (status === 404) {
      return "API の URL が誤っているか、指定したパスが存在しません。NEXT_PUBLIC_API_URL を確認してください。";
    }
    return `サーバーエラー（${status}）。API の接続先を確認してください。`;
  }
  // JSON の detail など短いメッセージはそのまま返す（長すぎる場合は切り詰め）
  if (trimmed.length > 300) return trimmed.slice(0, 300) + "...";
  return trimmed || `HTTP ${status}`;
}

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(normalizeErrorMessage(res.status, text));
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

import type { PlacementWithNote, User } from "./types";

export const api = {
  health: () => fetchApi<{ status: string }>("/health"),

  users: {
    list: () => fetchApi<User[]>("/users"),
    create: (body: { name: string; role?: string }) =>
      fetchApi<User>("/users", { method: "POST", body: JSON.stringify(body) }),
  },

  stickyNotes: {
    list: () => fetchApi<unknown[]>("/sticky_notes"),
    create: (body: {
      content: string;
      author_id?: number;
      postit_board_id?: string;
      postit_note_id?: string;
    }) => fetchApi<{ id: number }>("/sticky_notes", { method: "POST", body: JSON.stringify(body) }),
    /** 付箋ボードから一括取り込み（重複はスキップ） */
    importFromPostit: (body: { board_id: string; notes: { id: string; text: string }[] }) =>
      fetchApi<{ created: number; skipped: number }>("/sticky_notes/import_from_postit", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    delete: (noteId: number) =>
      fetchApi<undefined>(`/sticky_notes/${noteId}`, { method: "DELETE" }),
    moveToPersonal: (noteId: number, body: { owner_id: number; lane?: "INBOX" | "TODAY" | "DONE" }) =>
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
        lane?: "INBOX" | "TODAY" | "DONE";
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

  dailyReset: {
    messages: (ownerId: number) =>
      fetchApi<{ owner_id: number; messages: string[] }>(`/daily_reset/messages?owner_id=${ownerId}`),
  },
};
