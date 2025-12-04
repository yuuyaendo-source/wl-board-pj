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

export default function Toolbar({ onAddNote, color, setColor, scale, setScale, onDownload, onUpload, onToggleCommentPanel, onCenter }) {
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
                    + 付箋
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
                <button onClick={() => setScale(s => Math.max(0.5, s - 0.1))}>-</button>
                <span>{Math.round(scale * 100)}%</span>
                <button onClick={() => setScale(s => Math.min(2, s + 0.1))}>+</button>
            </div>

            <div className={styles.divider} />

            <div className={styles.group}>
                <button onClick={onDownload} title="ボードをダウンロード">💾</button>
                <input
                    type="file"
                    accept=".json"
                    onChange={handleFileUpload}
                    style={{ display: 'none' }}
                    ref={(ref) => { if (fileInputRef) fileInputRef.current = ref; }}
                />
                <button onClick={() => document.querySelector('input[type="file"]')?.click()} title="ボードをアップロード">📂</button>
            </div>

            <div className={styles.divider} />

            <div className={styles.group}>
                <button onClick={onCenter} title="中央に戻る">🎯</button>
            </div>

            <div className={styles.divider} />

            <div className={styles.group}>
                <button onClick={onToggleCommentPanel} title="コメント一覧">📝</button>
            </div>
        </div>
    );
}

