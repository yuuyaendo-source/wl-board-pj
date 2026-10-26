/**
 * 期限日（YYYY-MM-DD）から今日までの残り日数を計算する
 * @param dueDateStr YYYY-MM-DD 形式の文字列
 * @returns 残り日数（期限切れは負の数、当日は0）。無効値の場合は null
 */
export function calcDaysLeft(dueDateStr?: string | null): number | null {
    if (!dueDateStr) return null;

    const parts = dueDateStr.split("-").map(Number);
    if (parts.length !== 3) return null;
    const [y, m, d] = parts;
    if (!y || !m || !d) return null;

    const today = new Date();
    // 修正4: タイムゾーン遷移や夏時間による時間差のブレを防ぐため、年月日を直接 UTC 基準にして純粋なカレンダー日数を比較
    const utcToday = Date.UTC(today.getFullYear(), today.getMonth(), today.getDate());
    const utcDue = Date.UTC(y, m - 1, d);

    if (isNaN(utcDue)) return null;

    const MS_PER_DAY = 1000 * 60 * 60 * 24;
    return Math.trunc((utcDue - utcToday) / MS_PER_DAY);
}

/**
 * 期限日のフォーマット文字列（例: "⚠️ 期限切れ（2日経過）"）を取得する
 */
export function getDueDateStatusText(dueDateStr?: string | null): {
    daysLeft: number | null;
    label: string;
    status: "expired" | "today" | "urgent" | "normal" | "none";
} {
    const daysLeft = calcDaysLeft(dueDateStr);
    if (daysLeft === null) {
        return { daysLeft: null, label: "", status: "none" };
    }

    if (daysLeft < 0) {
        return {
            daysLeft,
            label: `⚠️ 期限切れ（${Math.abs(daysLeft)}日経過）`,
            status: "expired",
        };
    }
    if (daysLeft === 0) {
        return { daysLeft, label: "🔥 本日が期限！", status: "today" };
    }
    if (daysLeft <= 3) {
        return { daysLeft, label: `⏰ 期限まであと${daysLeft}日`, status: "urgent" };
    }
    if (daysLeft <= 10) {
        return { daysLeft, label: `📅 期限まであと${daysLeft}日`, status: "normal" };
    }
    return { daysLeft, label: `📅 期限: ${dueDateStr}`, status: "normal" };
}

/**
 * 期限日に応じたカードの枠線クラスを取得する
 */
export function getDueDateBorderClass(dueDateStr?: string | null): string {
    const daysLeft = calcDaysLeft(dueDateStr);
    if (daysLeft === null) return "";
    if (daysLeft < 0) return "border-2 border-red-500";
    if (daysLeft === 0) return "border-2 border-orange-500";
    return "";
}

/**
 * 期限日を "YYYY/MM/DD (曜日)" の形式にフォーマットする
 */
export function formatWithDay(dueDateStr?: string | null): string {
    if (!dueDateStr) return "";
    const parts = dueDateStr.split("-").map(Number);
    if (parts.length !== 3) return "";
    const [y, m, day] = parts;
    if (!y || !m || !day) return "";
    const d = new Date(y, m - 1, day);
    if (isNaN(d.getTime())) return "";
    const days = ["日", "月", "火", "水", "木", "金", "土"];
    const date = String(d.getDate()).padStart(2, "0");
    return `${d.getFullYear()}/${String(d.getMonth() + 1).padStart(2, "0")}/${date} (${days[d.getDay()]})`;
}