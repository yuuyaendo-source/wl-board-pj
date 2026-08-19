"use client";

import React from "react";

export function calcDaysLeft(dueDateStr: string | null | undefined): number | null {
    if (!dueDateStr) return null;
    const due = new Date(dueDateStr + "T00:00:00");
    if (isNaN(due.getTime())) return null;

    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const dueDay = new Date(due.getFullYear(), due.getMonth(), due.getDate());

    const diffTime = dueDay.getTime() - today.getTime();
    return Math.round(diffTime / (1000 * 60 * 60 * 24));
}

export function getDueDateBorderClass(dueDateStr: string | null | undefined): string {
    const days = calcDaysLeft(dueDateStr);
    if (days === null) return "";

    if (days < 0) {
        return "border-2 border-red-500 bg-red-50/20";
    }
    if (days === 0) {
        return "border-2 border-orange-500 bg-orange-50/20";
    }
    if (days > 0 && days <= 3) {
        return "border-2 border-amber-400";
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

    if (days < 0) {
        return (
            <span
                className={`inline-flex items-center gap-1 rounded-md bg-red-100 px-2 py-0.5 text-xs font-bold text-red-700 animate-pulse ${className}`}
                title={`期限日: ${dueDate}`}
            >
                ⚠️ 期限切れ（{Math.abs(days)}日経過）
            </span>
        );
    }

    if (days === 0) {
        return (
            <span
                className={`inline-flex items-center gap-1 rounded-md bg-orange-100 px-2 py-0.5 text-xs font-bold text-orange-800 ${className}`}
                title={`期限日: ${dueDate}`}
            >
                🔥 本期日が期限！
            </span>
        );
    }

    if (days > 0 && days <= 3) {
        return (
            <span
                className={`inline-flex items-center gap-1 rounded-md bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-800 ${className}`}
                title={`期限日: ${dueDate}`}
            >
                ⏰ 期限まであと{days}日
            </span>
        );
    }

    return (
        <span
            className={`inline-flex items-center gap-1 rounded-md bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700 ${className}`}
            title={`期限日: ${dueDate}`}
        >
            📅 期限: {dueDate}
        </span>
    );
}