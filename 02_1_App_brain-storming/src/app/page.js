"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import styles from "./page.module.css";

export default function Home() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [boardId, setBoardId] = useState("");

  useEffect(() => {
    const savedName = localStorage.getItem("userName");
    if (savedName) setName(savedName);
  }, []);

  const handleStart = (targetBoardId) => {
    if (!name.trim()) {
      alert("名前を入力してください");
      return;
    }
    localStorage.setItem("userName", name);
    router.push(`/board/${targetBoardId}`);
  };

  const createNewBoard = () => {
    const newId = Math.random().toString(36).substring(2, 9);
    handleStart(newId);
  };

  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <h1 className={styles.title}>Brainstorming App</h1>

        <div className={styles.card}>
          <div className={styles.inputGroup}>
            <label>参加者名</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="あなたの名前"
              className={styles.input}
            />
          </div>

          <div className={styles.actions}>
            <button onClick={createNewBoard} className={styles.primaryButton}>
              新規ボード作成
            </button>

            <div className={styles.divider}>または</div>

            <div className={styles.joinGroup}>
              <input
                type="text"
                value={boardId}
                onChange={(e) => setBoardId(e.target.value)}
                placeholder="ボードIDを入力"
                className={styles.input}
              />
              <button
                onClick={() => boardId && handleStart(boardId)}
                className={styles.secondaryButton}
                disabled={!boardId}
              >
                再開
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
