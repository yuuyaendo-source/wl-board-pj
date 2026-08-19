import { useState, useEffect } from "react";
import styles from "./NoteInputDialog.module.css";

export default function NoteInputDialog({
    onSubmit,
    onCancel,
    initialText = "",
    initialDueDate = ""
}) {
    const [text, setText] = useState(initialText);
    const [dueDate, setDueDate] = useState(initialDueDate);

    useEffect(() => {
        setText(initialText || "");
        setDueDate(initialDueDate || "");
    }, [initialText, initialDueDate]);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!text.trim()) return;
        onSubmit(text, dueDate || null);
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
                            {isEditing ? "保存" : "作成"}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}