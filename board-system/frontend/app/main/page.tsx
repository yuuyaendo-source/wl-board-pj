"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { flushSync } from "react-dom";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import type { PlacementWithNote } from "@/lib/types";
import ApiErrorBanner from "../components/ApiErrorBanner";
import OneLineInput from "../components/OneLineInput";

/** mutation 直後の refetch で古いレスポンスが返るのを防ぐ */
const REFETCH_DELAY_MS = 120;
const delay = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

/** キャンバス上の座標（ピクセル） */
type Position = { x: number; y: number };

export default function MainBoardPage() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerSize, setContainerSize] = useState({ w: 1200, h: 800 });
  const [placements, setPlacements] = useState<PlacementWithNote[]>([]);
  const [positions, setPositions] = useState<Record<number, Position>>({});
  const [aiMovedNoteIds, setAiMovedNoteIds] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMain = useCallback(async () => {
    try {
      setError(null);
      const [mainList, allPlacements] = await Promise.all([
        api.boards.main(),
        api.boardPlacements.list(),
      ]);
      const moved = new Set<number>();
      for (const p of allPlacements) {
        if (p.board_type === "TASK" || p.board_type === "PERSONAL") moved.add(p.note_id);
      }
      flushSync(() => {
        setPlacements(mainList);
        setAiMovedNoteIds(moved);
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMain();
  }, [fetchMain]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => {
      const { width, height } = el.getBoundingClientRect();
      if (width > 0 && height > 0) setContainerSize({ w: width, h: height });
    });
    ro.observe(el);
    const { width, height } = el.getBoundingClientRect();
    if (width > 0 && height > 0) setContainerSize({ w: width, h: height });
    return () => ro.disconnect();
  }, [placements.length]);

  useEffect(() => {
    const { w, h } = containerSize;
    setPositions((prev) => {
      const next = { ...prev };
      placements.forEach((p, i) => {
        const px = p.position_x != null ? (p.position_x / 100) * w : 20 + i * 90;
        const py = p.position_y != null ? (p.position_y / 100) * h : 20 + i * 70;
        next[p.id] = { x: px, y: py };
      });
      return next;
    });
  }, [placements, containerSize]);

  const handlePost = useCallback(
    async (text: string) => {
      await api.stickyNotes.create({ content: text });
      await delay(REFETCH_DELAY_MS);
      await fetchMain();
    },
    [fetchMain]
  );

  const handleDragEnd = useCallback(
    async (placementId: number, ev: MouseEvent | TouchEvent | PointerEvent) => {
      const container = containerRef.current;
      if (!container) return;
      const target = ev.target as HTMLElement;
      const box = target.getBoundingClientRect();
      const containerRect = container.getBoundingClientRect();
      const x = box.left - containerRect.left;
      const y = box.top - containerRect.top;
      const { w, h } = containerSize;
      const position_x = Math.max(0, Math.min(100, (x / w) * 100));
      const position_y = Math.max(0, Math.min(100, (y / h) * 100));
      await api.boardPlacements.patch(placementId, { position_x, position_y });
      await delay(REFETCH_DELAY_MS);
      await fetchMain();
    },
    [containerSize, fetchMain]
  );

  const syncPositionFromElement = useCallback(
    (placementId: number, ev: MouseEvent | TouchEvent | PointerEvent) => {
      const container = containerRef.current;
      if (!container) return;
      const target = ev.target as HTMLElement;
      const box = target.getBoundingClientRect();
      const containerRect = container.getBoundingClientRect();
      setPositions((prev) => ({
        ...prev,
        [placementId]: {
          x: box.left - containerRect.left,
          y: box.top - containerRect.top,
        },
      }));
    },
    []
  );

  if (loading) return <div className="p-6">Loading...</div>;
  if (error)
    return (
      <div className="p-6">
        <ApiErrorBanner error={error} onRetry={fetchMain} />
      </div>
    );

  return (
    <div className="flex h-[calc(100vh-52px)] flex-col">
      <div className="shrink-0 border-b border-zinc-200 bg-zinc-50 px-4 py-3 dark:border-zinc-800 dark:bg-zinc-900">
        <h1 className="mb-1 text-lg font-bold">Main Board（広場）</h1>
        <p className="mb-3 text-xs text-zinc-500">
          ホワイトボード形式。付箋をドラッグして配置。AI が Task / Personal へ仕分けした付箋は ✨。
        </p>
        <OneLineInput placeholder="投稿内容を入力..." onSubmit={handlePost} />
      </div>
      <div
        ref={containerRef}
        className="relative flex-1 overflow-hidden bg-[#f5f5dc] dark:bg-zinc-900"
        style={{ minHeight: 320 }}
      >
        {placements.map((p) => (
          <motion.div
            key={p.id}
            className="absolute left-0 top-0 cursor-grab active:cursor-grabbing"
            style={{
              x: positions[p.id]?.x ?? 0,
              y: positions[p.id]?.y ?? 0,
              touchAction: "none",
            }}
            drag
            dragMomentum={false}
            dragElastic={0}
            dragConstraints={containerRef}
            onDragEnd={(ev) => {
              void handleDragEnd(p.id, ev);
            }}
            onDrag={(ev) => syncPositionFromElement(p.id, ev)}
          >
            <MainBoardNoteCard
              content={p.note_content}
              showAiBadge={aiMovedNoteIds.has(p.note_id)}
            />
          </motion.div>
        ))}
      </div>
    </div>
  );
}

function MainBoardNoteCard({
  content,
  showAiBadge,
}: {
  content: string;
  showAiBadge: boolean;
}) {
  return (
    <div className="flex max-w-[220px] items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 shadow-md dark:border-amber-800 dark:bg-amber-950/40">
      <p className="min-h-[1.5em] flex-1 whitespace-pre-wrap text-sm font-medium text-zinc-900">
        {content || "（空）"}
      </p>
      {showAiBadge && (
        <span className="shrink-0 text-amber-600 dark:text-amber-400" title="AI が配置">
          ✨
        </span>
      )}
    </div>
  );
}
