"use client";

import React, { useState, useCallback } from "react";
import type { Team } from "@/lib/types";
import type { PersonalMember } from "@/lib/personalMembers";

interface OperationPanelProps {
    members: PersonalMember[];
    teams: Team[];
    autoImport: boolean;
    isImporting?: boolean;
    onAutoImportChange: (checked: boolean) => void;
    onImportClick: () => void;
    onTrashDrop: (noteId: number) => void;
    onMemberDrop: (noteId: number, ownerId: number) => void;
    onTeamDrop: (noteId: number, teamId: number, teamName: string) => void;
}

/** DragEvent から安全に noteId (number) を取り出すヘルパー */
function parseNoteId(e: React.DragEvent): number | null {
    const raw =
        e.dataTransfer.getData("noteId") ||
        e.dataTransfer.getData("placementId") ||
        e.dataTransfer.getData("text/plain");
    if (!raw) return null;
    const num = Number(raw);
    return isNaN(num) ? null : num;
}

export const OperationPanel: React.FC<OperationPanelProps> = ({
    members,
    teams,
    autoImport,
    isImporting = false,
    onAutoImportChange,
    onImportClick,
    onTrashDrop,
    onMemberDrop,
    onTeamDrop,
}) => {
    const [activeDragTarget, setActiveDragTarget] = useState<string | null>(null);

    const handleDragOver = useCallback((id: string, e: React.DragEvent) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = id === "trash" ? "move" : "copy";
        setActiveDragTarget((prev) => (prev !== id ? id : prev));
    }, []);

    const resetDragTarget = useCallback(() => {
        setActiveDragTarget(null);
    }, []);

    const handleDrop = useCallback(
        (id: string, callback: (noteId: number) => void, e: React.DragEvent) => {
            e.preventDefault();
            try {
                const noteId = parseNoteId(e);
                if (noteId !== null) {
                    callback(noteId);
                }
            } finally {
                resetDragTarget();
            }
        },
        [resetDragTarget]
    );

    return (
        <div
            onDragEnd={resetDragTarget}
            className="flex flex-col gap-3 p-3.5 bg-white/90 backdrop-blur-md rounded-2xl border border-zinc-200/80 shadow-sm"
        >
            {/* 1行目: 操作ボタン・自動インポート・ゴミ箱 */}
            <div className="flex flex-wrap items-center justify-between gap-3 pb-2 border-b border-zinc-100">
                <div className="flex flex-wrap items-center gap-3">
                    <button
                        type="button"
                        onClick={onImportClick}
                        disabled={isImporting}
                        className="flex items-center gap-1.5 px-4 py-2 bg-[var(--primary)] hover:bg-[var(--primary-hover)] disabled:opacity-50 text-white text-sm font-bold rounded-xl shadow-sm hover:shadow transition-all active:scale-95 cursor-pointer"
                    >
                        {isImporting ? (
                            <span className="flex items-center gap-1.5">
                                <span className="animate-spin text-xs">🌀</span>
                                <span>取り込み中…</span>
                            </span>
                        ) : (
                            <span>付箋ボードから取り込む</span>
                        )}
                    </button>

                    <label className="flex items-center gap-2 cursor-pointer text-sm font-medium text-zinc-700 hover:text-zinc-900 select-none">
                        <input
                            type="checkbox"
                            checked={autoImport}
                            onChange={(e) => onAutoImportChange(e.target.checked)}
                            className="w-4 h-4 rounded border-zinc-300 text-[var(--primary)] focus:ring-[var(--primary)] cursor-pointer"
                        />
                        <span>自動で取り込む（5分ごと・AI判定）</span>
                    </label>
                </div>

                {/* ゴミ箱（D&D専用ターゲット） */}
                <div
                    role="region"
                    aria-label="ゴミ箱エリア。付箋をここにドロップして削除"
                    onDragOver={(e) => handleDragOver("trash", e)}
                    onDragLeave={resetDragTarget}
                    onDrop={(e) => handleDrop("trash", onTrashDrop, e)}
                    className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-semibold transition-all select-none cursor-default border [&>*]:pointer-events-none ${activeDragTarget === "trash"
                            ? "bg-rose-200 border-2 border-rose-500 text-rose-900 ring-2 ring-inset ring-rose-400 font-bold shadow-md"
                            : "bg-rose-50/60 border-rose-200/80 text-rose-600"
                        }`}
                >
                    <span className="text-base">🗑️</span>
                    <span>ゴミ箱</span>
                </div>
            </div>

            {/* 2行目: パーソナルコピー */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-2.5">
                <span className="text-sm font-semibold text-zinc-600 whitespace-nowrap shrink-0">
                    パーソナルコピー:
                </span>
                <div className="flex flex-wrap gap-2 max-h-28 overflow-y-auto p-1.5 pr-2 w-full [scrollbar-width:thin] [scrollbar-color:theme(colors.zinc.200)_transparent] [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:bg-zinc-200 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-track]:bg-transparent">
                    {members.map((m) => {
                        const targetId = `member-${m.ownerId}`;
                        const isHovered = activeDragTarget === targetId;
                        return (
                            <div
                                key={m.ownerId}
                                role="region"
                                aria-label={`${m.name} のパーソナルボードへ付箋をドロップしてコピー`}
                                onDragOver={(e) => handleDragOver(targetId, e)}
                                onDragLeave={resetDragTarget}
                                onDrop={(e) =>
                                    handleDrop(targetId, (noteId) => onMemberDrop(noteId, m.ownerId), e)
                                }
                                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-sm font-medium transition-all select-none cursor-default border [&>*]:pointer-events-none ${isHovered
                                        ? "bg-sky-200 border-2 border-sky-500 text-sky-950 ring-2 ring-inset ring-sky-400 font-bold shadow-md"
                                        : "bg-zinc-50 border-zinc-200 text-zinc-700"
                                    }`}
                            >
                                <span className="flex items-center justify-center w-5 h-5 rounded-full bg-zinc-200 text-zinc-600 text-xs font-bold">
                                    {m.name.charAt(0)}
                                </span>
                                <span>{m.name}</span>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* 3行目: チーム一括コピー */}
            {teams.length > 0 && (
                <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-2.5 pt-1 border-t border-zinc-100/60">
                    <span className="text-sm font-semibold text-zinc-600 whitespace-nowrap shrink-0">
                        チーム一括コピー:
                    </span>
                    <div className="flex flex-wrap gap-2 max-h-28 overflow-y-auto p-1.5 pr-2 w-full [scrollbar-width:thin] [scrollbar-color:theme(colors.zinc.200)_transparent] [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:bg-zinc-200 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-track]:bg-transparent">
                        {teams.map((t) => {
                            const targetId = `team-${t.id}`;
                            const isHovered = activeDragTarget === targetId;
                            return (
                                <div
                                    key={t.id}
                                    role="region"
                                    aria-label={`${t.name} チーム所属メンバー全員へ一括コピー（${t.member_count}名）`}
                                    onDragOver={(e) => handleDragOver(targetId, e)}
                                    onDragLeave={resetDragTarget}
                                    onDrop={(e) =>
                                        handleDrop(
                                            targetId,
                                            (noteId) => onTeamDrop(noteId, t.id, t.name),
                                            e
                                        )
                                    }
                                    className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-sm font-semibold transition-all select-none cursor-default border [&>*]:pointer-events-none ${isHovered
                                            ? "bg-indigo-200 border-2 border-indigo-600 text-indigo-950 ring-2 ring-inset ring-indigo-400 font-bold shadow-md"
                                            : "bg-indigo-50/70 border-indigo-200 text-indigo-700"
                                        }`}
                                >
                                    <span className="text-xs">👥</span>
                                    <span>{t.name}</span>
                                    <span className="text-xs font-normal text-indigo-500 bg-indigo-100/80 px-1.5 py-0.5 rounded-full">
                                        {t.member_count ?? 0}名
                                    </span>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
};