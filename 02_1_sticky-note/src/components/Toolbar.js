import { useRef } from "react";
import styles from "./Toolbar.module.css";

const COLORS = [
    "#ffeb3b", // Yellow
    "#a7ffeb", // Cyan
    "#ffcdd2", // Pink
    "#e1bee7", // Purple
    "#fff9c4", // Light Yellow
    "#c5e1a5", // Light Green
    "#ffccbc", // Light Orange
    "#b3e5fc", // Light Blue
    "#ffffff"  // White
];

export default function Toolbar({
    onAddNote,
    color,
    setColor,
    scale,
    setScale,
    onDownload,
    onUpload,
    onToggleCommentPanel,
    onCenter,
    onClearAllNotes
}) {
    const fileInputRef = useRef(null);

    const handleFileUpload = (e) => {
        const file = e.target.files?.[0];
        if (file) {
            onUpload(file);
            e.target.value = ''; // Reset input
        }
    };

    return (
        <div className={styles.toolbar}>
            <div className={styles.group}>
                <button onClick={onAddNote} className={styles.addButton}>
                    付箋作成
                </button>
            </div>

            <div className={styles.divider} />

            <div className={styles.group}>
                {COLORS.map((c) => (
                    <button
                        key={c}
                        className={`${styles.colorBtn} ${color === c ? styles.active : ""}`}
                        style={{ backgroundColor: c }}
                        onClick={() => setColor(c)}
                    />
                ))}
            </div>

            <div className={styles.divider} />

            <div className={styles.group}>
                <button className={styles.textBtn} onClick={() => setScale(s => Math.max(0.5, s - 0.1))}>−</button>
                <span style={{ minWidth: '3ch', fontSize: '0.9rem' }}>{Math.round(scale * 100)}%</span>
                <button className={styles.textBtn} onClick={() => setScale(s => Math.min(2, s + 0.1))}>＋</button>
            </div>

            <div className={styles.divider} />

            {/* 並び順: センターへ戻る → 付箋一覧表示 → 付箋一覧保存 → 付箋データをインポート → 全削除 */}
            <div className={styles.group}>
                <span className={styles.iconBtnWrap} data-tooltip="センターへ戻る">
                    <button type="button" className={styles.iconBtn} onClick={onCenter} aria-label="センターへ戻る">🎯</button>
                </span>
            </div>

            <div className={styles.divider} />

            <div className={styles.group}>
                <span className={styles.iconBtnWrap} data-tooltip="付箋一覧表示">
                    <button type="button" className={styles.iconBtn} onClick={onToggleCommentPanel} aria-label="付箋一覧表示">📝</button>
                </span>
            </div>

            <div className={styles.divider} />

            <div className={styles.group}>
                <span className={styles.iconBtnWrap} data-tooltip="付箋一覧保存">
                    <button type="button" className={styles.iconBtn} onClick={onDownload} aria-label="付箋一覧保存">💾</button>
                </span>
            </div>

            <div className={styles.divider} />

            <div className={styles.group}>
                <input
                    type="file"
                    accept=".json"
                    onChange={handleFileUpload}
                    style={{ display: 'none' }}
                    ref={fileInputRef}
                />
                <span className={styles.iconBtnWrap} data-tooltip="付箋データをインポート">
                    <button type="button" className={styles.iconBtn} onClick={() => fileInputRef.current?.click()} aria-label="付箋データをインポート">📂</button>
                </span>
            </div>

            <div className={styles.divider} />

            <div className={styles.group}>
                <span className={styles.iconBtnWrap} data-tooltip="全削除">
                    <button
                        type="button"
                        onClick={onClearAllNotes}
                        className={`${styles.iconBtn} ${styles.delete}`}
                        aria-label="全削除"
                    >
                        🗑️
                    </button>
                </span>
            </div>

            <div className={styles.divider} />

            <div className={styles.group}>
                <span className={styles.iconBtnWrap} data-tooltip="Board System を開く">
                    <a
                        href={process.env.NEXT_PUBLIC_BOARD_SYSTEM_URL || "http://localhost:3001"}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={styles.iconBtn}
                        style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", textDecoration: "none" }}
                        aria-label="Board System を開く"
                    >
                        📋
                    </a>
                </span>
            </div>

        </div>
    );
}

