"use client";

import { useState } from "react";
import styles from "./CommentListPanel.module.css";

export default function CommentListPanel({ notes, onJumpToNote, onGroupNotes, onUngroupNotes, onClose }) {
    const [selectedNotes, setSelectedNotes] = useState([]);

    const toggleSelection = (noteId) => {
        if (selectedNotes.includes(noteId)) {
            setSelectedNotes(selectedNotes.filter(id => id !== noteId));
        } else {
            setSelectedNotes([...selectedNotes, noteId]);
        }
    };

    const handleGroupSelected = () => {
        if (selectedNotes.length < 2) {
            alert("グループ化するには2つ以上の付箋を選択してください");
            return;
        }
        onGroupNotes(selectedNotes);
        setSelectedNotes([]);
    };

    const handleUngroupSelected = () => {
        if (selectedNotes.length === 0) {
            alert("解除する付箋を選択してください");
            return;
        }
        onUngroupNotes(selectedNotes);
        setSelectedNotes([]);
    };

    return (
        <div className={styles.panel}>
            <div className={styles.header}>
                <h2>コメント一覧</h2>
                <button onClick={onClose} className={styles.closeButton}>✕</button>
            </div>

            <div className={styles.actions}>
                <span>{selectedNotes.length} 個選択中</span>
                <div className={styles.actionButtons}>
                    {selectedNotes.length >= 2 && (
                        <button onClick={handleGroupSelected} className={styles.groupButton}>
                            グループ化
                        </button>
                    )}
                    {selectedNotes.length > 0 && (
                        <button onClick={handleUngroupSelected} className={styles.ungroupButton}>
                            解除
                        </button>
                    )}
                </div>
            </div>

            <div className={styles.noteList}>
                {notes.map((note) => (
                    <div
                        key={note.id}
                        className={`${styles.noteItem} ${selectedNotes.includes(note.id) ? styles.selected : ''}`}
                    >
                        <input
                            type="checkbox"
                            checked={selectedNotes.includes(note.id)}
                            onChange={() => toggleSelection(note.id)}
                            className={styles.checkbox}
                        />
                        <div
                            className={styles.notePreview}
                            style={{ backgroundColor: note.color }}
                            onClick={() => onJumpToNote(note)}
                        >
                            <div className={styles.noteText}>
                                {note.text || "(空白)"}
                            </div>
                            {note.pinned && <span className={styles.pinnedBadge}>📌</span>}
                            {note.groupId && <span className={styles.groupBadge}>Group {note.groupId}</span>}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
