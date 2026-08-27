const BASE = typeof window !== "undefined" ? (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") : "";
export const API_BASE = BASE;

const getAuthToken = (): string | null => {
  if (typeof window !== "undefined") {
    return sessionStorage.getItem("admin_token");
  }
  return null;
};

function normalizeErrorMessage(status: number, body: string): string {
  const trimmed = body.trim();
  if (trimmed.startsWith("<") || trimmed.startsWith("<!")) {
    if (status === 404) {
      return "API の URL が誤っているか、指定したパスが存在しません。NEXT_PUBLIC_API_URL を確認してください。";
    }
    return `サーバーエラー（${status}）。API の接続先を確認してください。`;
  }
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
  const token = getAuthToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE}${path}`, {
    ...options,
    cache: "no-store",
    headers,
  });

  if (res.status === 401) {
    if (typeof window !== "undefined") {
      sessionStorage.removeItem("admin_token");
      window.dispatchEvent(new Event("auth-unauthorized"));
    }
    const text = await res.text();
    throw new Error(normalizeErrorMessage(res.status, text));
  }

  if (!res.ok) {
    const text = await res.text();
    throw new Error(normalizeErrorMessage(res.status, text));
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

import type {
  LaneType,
  PersonalNoteCreatePayload,
  PlacementWithNote,
  StickyNoteCreatePayload,
  Team,
  User,
} from "./types";

export const api = {
  health: () => fetchApi<{ status: string }>("/health"),

  users: {
    list: () => fetchApi<User[]>("/users"),
    create: (body: { name: string; email?: string; call_name?: string; role?: string; team_ids?: number[] }) =>
      fetchApi<User>("/users", { method: "POST", body: JSON.stringify(body) }),
    update: (userId: number, body: { name?: string; email?: string; call_name?: string; role?: string; team_ids?: number[] }) =>
      fetchApi<User>(`/users/${userId}`, { method: "PATCH", body: JSON.stringify(body) }),
    delete: (userId: number) =>
      fetchApi<undefined>(`/users/${userId}`, { method: "DELETE" }),
  },

  teams: {
    list: () => fetchApi<Team[]>("/teams"),
    create: (body: { name: string }) =>
      fetchApi<Team>("/teams", { method: "POST", body: JSON.stringify(body) }),
    update: (teamId: number, body: { name?: string }) =>
      fetchApi<Team>(`/teams/${teamId}`, { method: "PATCH", body: JSON.stringify(body) }),
    delete: (teamId: number) =>
      fetchApi<undefined>(`/teams/${teamId}`, { method: "DELETE" }),
  },

  stickyNotes: {
    list: () => fetchApi<unknown[]>("/sticky_notes"),
    create: (body: StickyNoteCreatePayload) =>
      fetchApi<{ id: number }>("/sticky_notes", { method: "POST", body: JSON.stringify(body) }),
    createPersonal: (body: PersonalNoteCreatePayload) =>
      fetchApi<{ id: number; note_id: number }>("/sticky_notes/create_personal", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    importFromPostit: (body: { board_id: string; notes: { id: string; text: string; due_date?: string | null }[] }) =>
      fetchApi<{ created: number; skipped: number }>("/sticky_notes/import_from_postit", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    delete: (noteId: number) =>
      fetchApi<undefined>(`/sticky_notes/${noteId}`, { method: "DELETE" }),
    update: (noteId: number, body: { content?: string; status?: string; due_date?: string }) =>
      fetchApi<unknown>(`/sticky_notes/${noteId}`, { method: "PATCH", body: JSON.stringify(body) }),
    moveToPersonal: (noteId: number, body: { owner_id: number; lane?: LaneType }) =>
      fetchApi<unknown>(`/sticky_notes/${noteId}/move_to_personal`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    copyToTeam: (noteId: number, body: { team_id: number; lane?: string }) =>
      fetchApi<{ created: number; user_ids: number[]; message: string }>(
        `/sticky_notes/${noteId}/copy_to_team`,
        { method: "POST", body: JSON.stringify(body) }
      ),
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
    reorderPersonalLane: (body: { owner_id: number; lane: LaneType; placement_ids: number[] }) =>
      fetchApi<{ ok: boolean }>("/board_placements/reorder_personal_lane", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    delete: (placementId: number) =>
      fetchApi<undefined>(`/board_placements/${placementId}`, { method: "DELETE" }),
  },

  boards: {
    main: () => fetchApi<PlacementWithNote[]>("/boards/main"),
    task: () => fetchApi<PlacementWithNote[]>("/boards/task"),
    personal: (ownerId: number) => fetchApi<PlacementWithNote[]>(`/boards/personal?owner_id=${ownerId}`),
    morning: () => fetchApi<PlacementWithNote[]>("/boards/morning"),
  },

  personalSummary: (ownerId: number) =>
    fetchApi<{ events: { summary?: string; start?: string; end?: string }[]; today: { label?: string; summary?: string; start?: string; end?: string }[] }>(
      `/api/personal/${ownerId}/summary`
    ),
  personalCalendarRefresh: (ownerId: number) =>
    fetchApi<{ ok: boolean; events_count: number }>(`/api/personal/${ownerId}/calendar/refresh`, { method: "POST" }),
  personalCalendarLive: (ownerId: number) =>
    fetchApi<{
      events: { id?: string; summary?: string; start?: string; end?: string }[];
      synced: boolean;
      stickies_updated?: boolean;
    }>(`/api/personal/${ownerId}/calendar/events/live`),

  dailyReset: {
    messages: (ownerId: number) =>
      fetchApi<{ owner_id: number; messages: string[] }>(`/daily_reset/messages?owner_id=${ownerId}`),
    syncToMorning: () =>
      fetchApi<{ ok: boolean; created: number }>("/daily_reset/sync_to_morning", { method: "POST" }),
    resetMeeting: () =>
      fetchApi<{ ok: boolean }>("/daily_reset/reset_meeting", { method: "POST" }),
    run8am: () =>
      fetchApi<{ ok: boolean; refreshed: number[]; failed: number[] }>("/daily_reset/run_8am", { method: "POST" }),
  },

  admin: {
    login: (password: string) =>
      fetchApi<{ access_token: string; token_type: string }>("/admin/login", {
        method: "POST",
        body: JSON.stringify({ password }),
      }),
    llm: {
      get: () =>
        fetchApi<{
          db_llm_target: number | null;
          env_llm_target: number | null;
          effective_llm_target: number | null;
          resolved_url: string | null;
          model_override: string | null;
          model_mode: string;
        }>("/admin/llm"),
      put: (body: { llm_target: number | null }) =>
        fetchApi<{
          db_llm_target: number | null;
          env_llm_target: number | null;
          effective_llm_target: number | null;
          resolved_url: string | null;
          model_override: string | null;
          model_mode: string;
        }>("/admin/llm", { method: "PUT", body: JSON.stringify(body) }),
    },
  },

  news: {
    fetch: () =>
      fetchApi<{ ok: boolean; created?: number; skipped?: boolean; reason?: string; error?: string }>("/news/fetch", { method: "POST" }),
    clear: () =>
      fetchApi<{ ok: boolean; deleted: number }>("/news/clear", { method: "POST" }),
  },
};