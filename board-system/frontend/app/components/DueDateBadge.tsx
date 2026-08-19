"use client";

import React from "react";

export function calcDaysLeft(dueDateStr: string | null | undefined): number | null {
    if (!dueDateStr) return null;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const [y, m, d] = dueDateStr.split("-").map(Number);
    if (!y || !m || !d) return null;
    const due = new Date(y, m - 1, d);
    due.setHours(0, 0, 0, 0);
    return Math.round((due.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
}

export function getDueDateBorderClass(dueDateStr: string | null | undefined): string {
    const days = calcDaysLeft(dueDateStr);
    if (days === null) return "";

    // 背景色(bg-)の指定を外し、外枠(border/ring)の強調のみに留めることで付箋の元の色を維持します
    if (days < 0) {
        return "ring-2 ring-red-500 border-red-500";
    }
    if (days === 0) {
        return "ring-2 ring-amber-500 border-amber-500";
    }
    if (days > 0 && days <= 3) {
        return "border-2 border-orange-400";
    }
    return "";
}

interface DueDateBadgeProps {
    dueDate: string | null | undefined;
    className?: string;
}

export default function DueDateBadge({ dueDate, className = "" }: DueDateBadgeProps) {
    if (!dueDate) return null;

    const days = calcDaysLeft(dueDate);
    if (days === null) return null;

    let label = "";
    let badgeCls = "";

    // Taskボード・付箋ボードと完全に同等の文言と色使い（白抜き文字等）に統一
    if (days < 0) {
        label = `⚠️ 期限切れ（${Math.abs(days)}日経過）`;
        badgeCls = "bg-red-600 text-white font-extrabold text-sm py-1 px-3 shadow-md animate-pulse";
    } else if (days === 0) {
        label = "🔥 本期日が期限！";
        badgeCls = "bg-amber-500 text-white font-extrabold text-sm py-1 px-3 shadow-md";
    } else if (days <= 3) {
        label = `⏰ 期限まであと${days}日`;
        badgeCls = "bg-orange-500 text-white font-bold text-xs py-1 px-2.5 shadow-sm";
    } else if (days <= 10) {
        label = `📅 期限まであと${days}日`;
        badgeCls = "bg-yellow-400 text-zinc-900 font-bold text-xs py-1 px-2.5 shadow-sm";
    } else {
        label = `📅 期限: ${dueDate}`;
        badgeCls = "bg-blue-100 text-blue-800 font-semibold text-xs py-1 px-2.5";
    }

    return (
        <span
            className={`inline-flex items-center gap-1 rounded-lg border leading-none ${badgeCls} ${className}`}
            title={`期限日: ${dueDate}`}
        >
            {label}
        </span>
    );
}