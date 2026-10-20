import { useState, useEffect, useRef } from "react";
import styles from "./NoteInputDialog.module.css";
import { formatWithDay } from "@shared/utils/dueDate";

export default function NoteInputDialog({
    onSubmit,
    onCancel,
    initialText = "",
    initialDueDate = ""
}) {
    const [text, setText] = useState(initialText);
    const [dueDate, setDueDate] = useState(initialDueDate);
    const dateInputRef = useRef(null);

    useEffect(() => {
        setText(initialText || "");
        setDueDate(initialDueDate || "");
    }, [initialText, initialDueDate]);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!text.trim()) return;
        onSubmit(text, dueDate || null);
    };

    const handleOpenPicker = () => {
        if (dateInputRef.current) {
            if (typeof dateInputRef.current.showPicker === "function") {
                try {
                    dateInputRef.current.showPicker();
                } catch {
                    dateInputRef.current.focus();
                }
            } else {
                dateInputRef.current.click();
            }
        }
    };

    const isEditing = Boolean(initialText);

    return (
        <div className={styles.overlay} onClick={onCancel}>
            <div className={styles.dialog} onClick={(e) => e.stopPropagation()}>
                <h2 className={styles.title}>{isEditing ? "付箋を編集" : "付箋を作成"}</h2>
                <form onSubmit={handleSubmit}>
                    <textarea
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        placeholder="ここにテキストを入力..."
                        className={styles.textarea}
                        autoFocus
                    />
                    <div style={{ marginTop: "12px", display: "flex", alignItems: "center", gap: "8px" }}>
                        <label style={{ fontSize: "14px", color: "#555", fontWeight: "bold" }}>📅 期限:</label>
                        <div style={{ position: "relative", display: "inline-flex", alignItems: "center" }}>
                            <button
                                type="button"
                                onClick={handleOpenPicker}
                                style={{
                                    padding: "6px 10px",
                                    borderRadius: "6px",
                                    border: "1px solid #ccc",
                                    background: "#fff",
                                    fontSize: "14px",
                                    cursor: "pointer",
                                    display: "flex",
                                    alignItems: "center",
                                    gap: "6px"
                                }}
                            >
                                <span>{dueDate ? formatWithDay(dueDate) : "期限を設定"}</span>
                                <span>📅</span>
                            </button>
                            <input
                                ref={dateInputRef}
                                type="date"
                                value={dueDate}
                                onChange={(e) => setDueDate(e.target.value)}
                                tabIndex={-1}
                                aria-hidden="true"
                                style={{
                                    position: "absolute",
                                    width: 0,
                                    height: 0,
                                    opacity: 0,
                                    pointerEvents: "none"
                                }}
                            />
                        </div>
                        {dueDate && (
                            <button
                                type="button"
                                onClick={() => setDueDate("")}
                                style={{
                                    padding: "4px 8px",
                                    borderRadius: "4px",
                                    border: "1px solid #ccc",
                                    background: "#f0f0f0",
                                    fontSize: "12px",
                                    cursor: "pointer",
                                }}
                            >
                                クリア
                            </button>
                        )}
                    </div>
                    <div className={styles.buttons}>
                        <button type="button" onClick={onCancel} className={`${styles.button} ${styles.cancelButton}`}>
                            キャンセル
                        </button>
                        <button type="submit" className={`${styles.button} ${styles.submitButton}`} disabled={!text.trim()}>
                            {isEditing ? "保存" : "作成"}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}