import Image from "next/image";
import Link from "next/link";
import styles from "./page.module.css";

// AI-Board (02_2) の config.json の board_id と一致させること
const AI_BOARD_LINK_BOARD_ID = "board_20260125";

export default function Home() {
  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <h1 className={styles.title}>付箋掲示板 (Postit)</h1>

        <div className={styles.card}>
          <h2 style={{ marginTop: 0, fontSize: "1.25rem" }}>AI-Board 連携用</h2>
          <p style={{ color: "#555", marginBottom: 16 }}>
            AI-Board の付箋検知・アップロードはこのボードに反映されます。同じ board_id を開いてください。
          </p>
          <Link href={`/board/${AI_BOARD_LINK_BOARD_ID}`} className={styles.primaryButton}>
            付箋ボードを開く (board_20260125)
          </Link>
        </div>

        <div className={styles.actions}>
          <Link href="/board/test" className={styles.secondaryButton}>
            テスト用ボード (/board/test)
          </Link>
        </div>
      </main>
    </div>
  );
}
