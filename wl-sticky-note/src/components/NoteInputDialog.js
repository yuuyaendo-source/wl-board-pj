import { useState } from "react";
import styles from "./NoteInputDialog.module.css";

export default function NoteInputDialog({ onSubmit, onCancel }) {
    const [text, setText] = useState("");

    const handleSubmit = (e) => {
        e.preventDefault();
        onSubmit(text);
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
                    <div className={styles.buttons}>
                        <button type="button" onClick={onCancel} className={`${styles.button} ${styles.cancelButton}`}>
                            キャンセル
                        </button>
                        <button type="submit" className={`${styles.button} ${styles.submitButton}`}>
                            作成
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
