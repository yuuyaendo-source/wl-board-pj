"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { flushSync } from "react-dom";
import { api, API_BASE } from "@/lib/api";
import type { PlacementWithNote } from "@/lib/types";
import type { LaneType } from "@/lib/types";
import ApiErrorBanner from "./ApiErrorBanner";
import NoteCard from "./NoteCard";
import OneLineInput from "./OneLineInput";

/** パーソナルサマリ（今日の予定・Today）の型 */
interface SummaryEvent {
  summary?: string;
  start?: string;
  end?: string;
}
interface SummaryTodayItem {
  label?: string;
  summary?: string;
  start?: string;
  end?: string;
}

/** mutation 直後の refetch で古いレスポンスが返るのを防ぐため、少し待ってから再取得する */
const REFETCH_DELAY_MS = 120;
const delay = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

function isCalendarPlacement(src?: string | null): boolean {
  return src === "calendar" || src === "calendar_timed";
}

function personalCardColor(
  lane: LaneType,
  placement: PlacementWithNote
): "yellow" | "green" | "grey" | "blue" | "red" | "purple" {
  if (lane === "HELP_REQUEST") return "red";
  if (lane === "DONE") return "grey";
  if (isCalendarPlacement(placement.placement_source)) return "purple";
  if (placement.is_from_task) return "green";
  return "blue";
}

/** 表示順: 応援要請 → Today → タスク → Done */
const LANES: { key: LaneType; label: string }[] = [
  { key: "HELP_REQUEST", label: "応援要請" },
  { key: "TODAY", label: "Today" },
  { key: "INBOX", label: "タスク" },
  { key: "DONE", label: "Done" },
];

export default function PersonalBoardView({
  ownerId,
  displayName,
}: {
  ownerId: number;
  displayName: string;
}) {
  const [byLane, setByLane] = useState<Record<LaneType, PlacementWithNote[]>>({
    INBOX: [],
    TODAY: [],
    DONE: [],
    HELP_REQUEST: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [summary, setSummary] = useState<{ events: SummaryEvent[]; today: SummaryTodayItem[] } | null>(null);

  const fetchPersonal = useCallback(async () => {
    try {
      setError(null);
      const list = await api.boards.personal(ownerId);
      const next: Record<LaneType, PlacementWithNote[]> = { INBOX: [], TODAY: [], DONE: [], HELP_REQUEST: [] };
      for (const p of list) {
        const lane = (p.lane ?? "INBOX") as LaneType;
        if (lane in next) next[lane].push(p);
      }
      flushSync(() => setByLane(next));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [ownerId]);

  const fetchSummary = useCallback(async () => {
    try {
      const data = await api.personalSummary(ownerId);
      setSummary({ events: data.events ?? [], today: data.today ?? [] });
    } catch {
      setSummary({ events: [], today: [] });
    } finally {
      setSummaryLoading(false);
    }
  }, [ownerId]);

  useEffect(() => {
    fetchPersonal();
  }, [fetchPersonal]);
  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  const handleAppendContent = useCallback(
    async (noteId: number, currentContent: string | null, appendedText: string) => {
      const newContent = (currentContent || "").trim()
        ? `${(currentContent || "").trim()}\n${appendedText}`
        : appendedText;
      await api.stickyNotes.update(noteId, { content: newContent });
      await delay(REFETCH_DELAY_MS);
      await fetchPersonal();
    },
    [fetchPersonal]
  );

  const handlePost = useCallback(
    async (text: string) => {
      // 1リクエストで create + Personal 配置（move_to_personal の 404 を防ぐ）
      const placement = await api.stickyNotes.createPersonal({
        content: text,
        owner_id: ownerId,
        lane: "TODAY",
      });
      const noteId = placement.note_id;
      const placementId = placement.id;
      setByLane((prev) => ({
        ...prev,
        TODAY: [
          {
            id: placementId,
            note_id: noteId,
            board_type: "PERSONAL",
            owner_id: ownerId,
            lane: "TODAY",
            position_x: null,
            position_y: null,
            matrix_quadrant: null,
            sort_order: 0,
            note_content: text,
            note_status: "ACTIVE",
            is_from_task: false,
          } as PlacementWithNote,
          ...prev.TODAY,
        ],
      }));
      await delay(REFETCH_DELAY_MS);
      await fetchPersonal();
    },
    [ownerId, fetchPersonal]
  );

  const handleDrop = useCallback(
    async (placementId: number, targetLane: LaneType, targetIndex?: number) => {
      setError(null);
      const sourceLane = (Object.keys(byLane) as LaneType[]).find((k) =>
        byLane[k].some((p) => p.id === placementId)
      );
      const isSameLane = sourceLane === targetLane;

      if (isSameLane && targetIndex !== undefined) {
        const list = [...byLane[targetLane]];
        const fromIdx = list.findIndex((p) => p.id === placementId);
        if (fromIdx < 0) return;
        const [removed] = list.splice(fromIdx, 1);
        let insertIdx = targetIndex;
        if (insertIdx > fromIdx) insertIdx -= 1;
        list.splice(insertIdx, 0, removed);
        setByLane((prev) => ({ ...prev, [targetLane]: list }));
        await api.boardPlacements.reorderPersonalLane({
          owner_id: ownerId,
          lane: targetLane,
          placement_ids: list.map((p) => p.id),
        });
        await delay(REFETCH_DELAY_MS);
        await fetchPersonal();
        return;
      }

      setByLane((prev) => {
        let placement: PlacementWithNote | null = null;
        const next = { ...prev };
        for (const key of Object.keys(next) as LaneType[]) {
          const idx = next[key].findIndex((p) => p.id === placementId);
          if (idx >= 0) {
            placement = { ...next[key][idx], lane: targetLane };
            next[key] = next[key].filter((_, i) => i !== idx);
            break;
          }
        }
        if (placement) next[targetLane] = [...next[targetLane], placement];
        return next;
      });
      await api.boardPlacements.patch(placementId, { lane: targetLane });
      await delay(REFETCH_DELAY_MS);
      await fetchPersonal();
    },
    [ownerId, byLane, fetchPersonal]
  );

  const handleTrashDrop = useCallback(
    async (noteId: number) => {
      setError(null);
      try {
        await api.stickyNotes.delete(noteId);
        await delay(REFETCH_DELAY_MS);
        await fetchPersonal();
      } catch (e) {
        setError(e instanceof Error ? e.message : "削除に失敗しました");
      }
    },
    [fetchPersonal]
  );

  /** 付箋をタスクボードへ。Task 由来・パーソナル投稿どちらも releaseToTask(noteId) で統一（404 回避） */
  const handleReleaseToTask = useCallback(
    async (noteId: number) => {
      setError(null);
      try {
        await api.stickyNotes.releaseToTask(noteId);
        await delay(REFETCH_DELAY_MS);
        await fetchPersonal();
      } catch (e) {
        setError(e instanceof Error ? e.message : "タスクボードへの追加に失敗しました");
      }
    },
    [fetchPersonal]
  );

  if (loading) return <div className="p-6">Loading...</div>;
  if (error)
    return (
      <div className="p-6">
        <ApiErrorBanner error={error} onRetry={fetchPersonal} />
      </div>
    );

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      {/* スクロール時も入力・投稿・ゴミ箱・タスクボードへが追従する */}
      <div className="sticky top-[52px] z-10 -mx-6 bg-white px-6 pb-4 pt-2 shadow-[0_1px_0_0_var(--border)]">
        <h1 className="mb-4 text-xl font-bold">パーソナルボード — {displayName}</h1>
        <OneLineInput placeholder="タスクやメモを入力..." onSubmit={handlePost} />

        <div className="mt-6 flex flex-row flex-nowrap items-center gap-3 rounded-xl border border-[var(--border)] bg-white p-4 shadow-sm">
          <PersonalTrashDropZone onDrop={handleTrashDrop} />
          <PersonalTaskReleaseDropZone onDropToTask={handleReleaseToTask} />
        </div>
      </div>

      <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-5">
        {LANES.map(({ key, label }) => (
          <LaneColumn
            key={key}
            lane={key}
            label={label}
            placements={byLane[key]}
            onDrop={(placementId, targetIndex) => handleDrop(placementId, key, targetIndex)}
            onRefresh={fetchPersonal}
            onAppendContent={handleAppendContent}
          />
        ))}
        <PersonalCalendarPanel
          ownerId={ownerId}
          events={summary?.events ?? []}
          today={summary?.today ?? []}
          loading={summaryLoading}
          onRefresh={fetchSummary}
          onAfterCalendarRefresh={fetchPersonal}
        />
      </div>
    </div>
  );
}

function PersonalTrashDropZone({ onDrop }: { onDrop: (noteId: number) => void }) {
  const [over, setOver] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    const isFromTask = e.dataTransfer.getData("isFromTask");
    if (isFromTask === "true") {
      e.dataTransfer.dropEffect = "none";
      return;
    }
    e.dataTransfer.dropEffect = "move";
    setOver(true);
  };
  const handleDragLeave = () => setOver(false);
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setOver(false);
    if (e.dataTransfer.getData("isFromTask") === "true") return;
    // noteId を優先。一部ブラウザで drop 時に getData("noteId") が空になる場合があるため placementId をフォールバック（API が placement から note を解決）
    const noteId = e.dataTransfer.getData("noteId") || e.dataTransfer.getData("placementId");
    if (noteId) onDrop(Number(noteId));
  };

  return (
    <div
      className={`flex items-center gap-2 rounded-xl border-2 border-dashed px-4 py-2 text-sm transition-colors ${
        over ? "border-red-400 bg-red-50" : "border-zinc-300 bg-zinc-100"
      }`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <span>🗑️</span>
      <span>ゴミ箱（Personalで作った付箋のみ）</span>
    </div>
  );
}

function PersonalTaskReleaseDropZone({ onDropToTask }: { onDropToTask: (noteId: number) => void | Promise<void> }) {
  const [over, setOver] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const canRelease = e.dataTransfer.types.includes("application/x-board-task-release");
    if (!canRelease) {
      e.dataTransfer.dropEffect = "none";
      return;
    }
    e.dataTransfer.dropEffect = "move";
    setOver(true);
  };
  const handleDragLeave = () => setOver(false);
  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setOver(false);
    const noteIdStr = e.dataTransfer.getData("noteId") || e.dataTransfer.getData("text/plain");
    if (!noteIdStr) return;
    await Promise.resolve(onDropToTask(Number(noteIdStr)));
  };

  return (
    <div
      className={`flex items-center gap-2 rounded-xl border-2 border-dashed px-4 py-2 text-sm transition-colors ${
        over ? "border-[var(--primary)] bg-green-50" : "border-zinc-300 bg-zinc-100"
      }`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <span>📤</span>
      <span>タスクボードへ</span>
    </div>
  );
}

function formatSummaryTime(start?: string, end?: string): string {
  if (!start) return "";
  try {
    const s = new Date(start);
    const e = end ? new Date(end) : null;
    const time = (d: Date) =>
      isNaN(d.getTime()) ? "" : d.toLocaleTimeString("ja-JP", { hour: "2-digit", minute: "2-digit" });
    const startStr = time(s);
    if (e && !isNaN(e.getTime()) && startStr) {
      const endStr = time(e);
      if (endStr) return `${startStr}–${endStr}`;
    }
    return startStr || start;
  } catch {
    return start;
  }
}

const CALENDAR_LIVE_POLL_MS = 15 * 60 * 1000;

function PersonalCalendarPanel({
  ownerId,
  events,
  today,
  loading,
  onRefresh,
  onAfterCalendarRefresh,
}: {
  ownerId: number;
  events: SummaryEvent[];
  today: SummaryTodayItem[];
  loading: boolean;
  onRefresh: () => void;
  onAfterCalendarRefresh?: () => void;
}) {
  const [refreshing, setRefreshing] = useState(false);
  const [liveEvents, setLiveEvents] = useState<SummaryEvent[]>(events);
  const hasEvents = liveEvents.length > 0;

  useEffect(() => {
    setLiveEvents(events);
  }, [events]);

  useEffect(() => {
    let cancelled = false;
    const pollLive = async () => {
      if (typeof document !== "undefined" && document.visibilityState !== "visible") return;
      try {
        const data = await api.personalCalendarLive(ownerId);
        if (!cancelled && data.synced && Array.isArray(data.events)) {
          setLiveEvents(data.events);
          if (data.stickies_updated) {
            await onRefresh();
            if (onAfterCalendarRefresh) await onAfterCalendarRefresh();
          }
        }
      } catch {
        // 未連携・オフライン時はキャッシュ表示のまま
      }
    };
    const id = window.setInterval(pollLive, CALENDAR_LIVE_POLL_MS);
    const onVis = () => {
      if (document.visibilityState === "visible") pollLive();
    };
    document.addEventListener("visibilitychange", onVis);
    pollLive();
    return () => {
      cancelled = true;
      window.clearInterval(id);
      document.removeEventListener("visibilitychange", onVis);
    };
  }, [ownerId, onRefresh, onAfterCalendarRefresh]);

  const handleRefreshFromGoogle = useCallback(async () => {
    setRefreshing(true);
    try {
      await api.personalCalendarRefresh(ownerId);
      try {
        const data = await api.personalCalendarLive(ownerId);
        if (data.synced && Array.isArray(data.events)) {
          setLiveEvents(data.events);
        }
      } catch {
        // ignore
      }
      await onRefresh();
      if (onAfterCalendarRefresh) await onAfterCalendarRefresh();
    } catch {
      // ignore
    } finally {
      setRefreshing(false);
    }
  }, [ownerId, onRefresh, onAfterCalendarRefresh]);

  return (
    <div className="rounded-xl border-2 border-dashed border-[var(--border)] bg-white p-4">
      <h2 className="mb-3 font-semibold text-zinc-700">今日の予定（カレンダー連携）</h2>
      {loading ? (
        <p className="text-sm text-zinc-500">読み込み中...</p>
      ) : !hasEvents ? (
        <p className="text-sm text-zinc-500">
          カレンダー連携するとここに今日の予定が表示されます。
        </p>
      ) : (
        <ul className="flex flex-col gap-1 text-sm">
          {liveEvents.map((ev, i) => (
            <li key={i} className="flex flex-col gap-0.5">
              <span className="text-zinc-500">{formatSummaryTime(ev.start, ev.end)}</span>
              <span>{ev.summary || "(無題)"}</span>
            </li>
          ))}
        </ul>
      )}
      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
        <a
          href={
            typeof window !== "undefined"
              ? `${window.location.origin}/api/bs/auth/google?user_id=${ownerId}`
              : `${API_BASE}/auth/google?user_id=${ownerId}`
          }
          rel="noopener noreferrer"
          className="text-[var(--primary)] underline hover:opacity-80"
        >
          Google カレンダーと連携
        </a>
        <button
          type="button"
          onClick={handleRefreshFromGoogle}
          disabled={refreshing}
          className="text-zinc-500 underline hover:text-zinc-700 disabled:opacity-50"
        >
          {refreshing ? "更新中..." : "予定を更新"}
        </button>
      </div>
    </div>
  );
}

function LaneColumn({
  lane,
  label,
  placements,
  onDrop,
  onRefresh,
  onAppendContent,
}: {
  lane: LaneType;
  label: string;
  placements: PlacementWithNote[];
  onDrop: (placementId: number, targetIndex?: number) => void | Promise<void>;
  onRefresh: () => void;
  onAppendContent?: (noteId: number, currentContent: string | null, appendedText: string) => void;
}) {
  const [over, setOver] = useState(false);
  const columnRef = useRef<HTMLDivElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    setOver(true);
  };
  const handleDragLeave = () => setOver(false);
  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setOver(false);
    const id = e.dataTransfer.getData("placementId");
    if (!id) return;
    const placementId = Number(id);
    let targetIndex: number | undefined;
    if (columnRef.current) {
      const container = columnRef.current.querySelector("[data-lane-cards]");
      if (container) {
        const cards = Array.from(container.querySelectorAll("[data-placement-id]"));
        const y = e.clientY;
        for (let i = 0; i < cards.length; i++) {
          const r = (cards[i] as HTMLElement).getBoundingClientRect();
          if (y < r.top + r.height / 2) {
            targetIndex = i;
            break;
          }
          targetIndex = i + 1;
        }
      }
    }
    await Promise.resolve(onDrop(placementId, targetIndex));
  };

  return (
    <div
      ref={columnRef}
      className={`rounded-xl border-2 border-dashed border-[var(--border)] p-4 transition-colors ${
        over ? "border-[var(--primary)] bg-green-50/50" : "bg-white"
      }`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <h2 className="mb-3 font-semibold text-zinc-700">{label}</h2>
      <div className="flex flex-col gap-2" data-lane-cards>
        {placements.map((p) => (
          <div key={p.id} data-placement-id={p.id}>
            <NoteCard
            placement={p}
            draggable
            showPersonalBadge={
              p.is_from_task === false &&
              lane !== "HELP_REQUEST" &&
              !isCalendarPlacement(p.placement_source)
            }
            showCalendarBadge={isCalendarPlacement(p.placement_source)}
            cardColor={personalCardColor(lane, p)}
            dragData={{ isFromTask: String(!!p.is_from_task), canReleaseToTask: "true" }}
            onAppendContent={onAppendContent}
            onDragEnd={onRefresh}
          />
          </div>
        ))}
      </div>
    </div>
  );
}
