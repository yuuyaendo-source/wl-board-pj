import { useState } from "react";
import styles from "./UserDialog.module.css";

export default function UserDialog({ onSubmit }) {
    const [username, setUsername] = useState("");
    const [error, setError] = useState("");

    const handleSubmit = (e) => {
        e.preventDefault();

        const trimmedName = username.trim();

        if (!trimmedName) {
            setError("名前を入力してください");
            return;
        }

        if (trimmedName.length > 20) {
            setError("名前は20文字以内にしてください");
            return;
        }

        onSubmit(trimmedName);
    };

    return (
        <div className={styles.overlay}>
            <div className={styles.dialog}>
                <h2 className={styles.title}>ボードに参加</h2>
                <p className={styles.description}>
                    あなたの名前を入力してください
                </p>

                <form onSubmit={handleSubmit}>
                    <input
                        type="text"
                        value={username}
                        onChange={(e) => {
                            setUsername(e.target.value);
                            setError("");
                        }}
                        placeholder="例：田中太郎"
                        className={styles.input}
                        autoFocus
                        maxLength={20}
                    />

                    {error && (
                        <div className={styles.error}>{error}</div>
                    )}

                    <button type="submit" className={styles.button}>
                        参加する
                    </button>
                </form>

                <p className={styles.note}>
                    ※この名前は付箋の作成者として表示されます
                </p>
            </div>
        </div>
    );
}
