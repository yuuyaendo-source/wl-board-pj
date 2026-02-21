import styles from "./ParticipantsList.module.css";

export default function ParticipantsList({ participants, onClose }) {
    return (
        <div className={styles.panel}>
            <div className={styles.header}>
                <h3 className={styles.title}>
                    👥 参加者 ({participants.length})
                </h3>
                <button onClick={onClose} className={styles.closeButton}>
                    ✕
                </button>
            </div>

            <div className={styles.list}>
                {participants.length === 0 ? (
                    <div className={styles.empty}>
                        参加者がいません
                    </div>
                ) : (
                    participants.map((participant) => (
                        <div key={participant.socketId} className={styles.participant}>
                            <div className={styles.avatar}>
                                {participant.username.charAt(0).toUpperCase()}
                            </div>
                            <div className={styles.info}>
                                <div className={styles.name}>{participant.username}</div>
                                <div className={styles.status}>🟢 オンライン</div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
