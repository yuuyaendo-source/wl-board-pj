import { useState } from "react";
import styles from "./NoteInputDialog.module.css";

export default function NoteInputDialog({ onSubmit, onCancel }) {
    const [text, setText] = useState("");
    const [dueDate, setDueDate] = useState("");

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!text.trim()) return;
        onSubmit(text, dueDate || null);
    };

    return (
        <div className={styles.overlay} onClick={onCancel}>
            <div className={styles.dialog} onClick={(e) => e.stopPropagation()}>
                <h2 className={styles.title}>付箋を作成</h2>
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
                        <input
                            type="date"
                            value={dueDate}
                            onChange={(e) => setDueDate(e.target.value)}
                            style={{
                                padding: "6px 10px",
                                borderRadius: "6px",
                                border: "1px solid #ccc",
                                fontSize: "14px",
                                cursor: "pointer",
                            }}
                        />
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
                            作成
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}