"use client";

import React from "react";
// 共通ユーティリティからインポート
import { getDueDateStatusText } from "@shared/utils/dueDate";

interface DueDateBadgeProps {
    dueDate: string | null | undefined;
    className?: string;
}

export default function DueDateBadge({ dueDate, className = "" }: DueDateBadgeProps) {
    if (!dueDate) return null;

    // utils/dueDate.ts の共通判定関数を利用
    const statusInfo = getDueDateStatusText(dueDate);
    if (statusInfo.daysLeft === null) return null;

    let badgeCls = "";

    // 状態に応じたスタイルを適用
    if (statusInfo.status === "expired") {
        badgeCls = "bg-red-600 text-white font-extrabold text-sm py-1 px-3 shadow-md animate-pulse";
    } else if (statusInfo.status === "today") {
        badgeCls = "bg-amber-500 text-white font-extrabold text-sm py-1 px-3 shadow-md";
    } else if (statusInfo.daysLeft !== null && statusInfo.daysLeft <= 3) {
        badgeCls = "bg-orange-500 text-white font-bold text-xs py-1 px-2.5 shadow-sm";
    } else if (statusInfo.daysLeft !== null && statusInfo.daysLeft <= 10) {
        badgeCls = "bg-yellow-400 text-zinc-900 font-bold text-xs py-1 px-2.5 shadow-sm";
    } else {
        badgeCls = "bg-blue-100 text-blue-800 font-semibold text-xs py-1 px-2.5";
    }

    return (
        <span
            className={`inline-flex items-center gap-1 rounded-lg border leading-none ${badgeCls} ${className}`}
            title={`期限日: ${dueDate}`}
        >
            {statusInfo.label}
        </span>
    );
}