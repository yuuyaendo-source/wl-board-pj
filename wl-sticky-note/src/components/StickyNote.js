import { useState, useRef, useEffect } from "react";
import LinkifiedText from "./LinkifiedText";
import styles from "./StickyNote.module.css";

const COLORS = [
    "#ffeb3b", "#a7ffeb", "#ffcdd2", "#e1bee7",
    "#fff9c4", "#c5e1a5", "#ffccbc", "#b3e5fc", "#ffffff"
];

function calcDaysLeft(dueDateStr) {
    if (!dueDateStr) return null;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const [y, m, d] = dueDateStr.split("-").map(Number);
    const due = new Date(y, m - 1, d);
    due.setHours(0, 0, 0, 0);
    return Math.round((due.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
}

export default function StickyNote({ note, onUpdate, onDelete, scale, onMouseDown, onMouseUp }) {
    const [isDragging, setIsDragging] = useState(false);
    const [appendText, setAppendText] = useState("");
    const [showColorPicker, setShowColorPicker] = useState(false);
    const [showDatePicker, setShowDatePicker] = useState(false);
    const noteRef = useRef(null);
    const offset = useRef({ x: 0, y: 0 });

    const isLarge = note.ratioW && note.ratioW >= 0.2;
    const dueDateVal = note.dueDate || note.due_date || "";
    const daysLeft = calcDaysLeft(dueDateVal);

    const handleMouseDown = (e) => {
        if (onMouseDown) onMouseDown(e); // Propagate to parent for line drawing
        if (e.defaultPrevented || e.altKey) return; // Don't drag if line drawing
        if (note.pinned) return; // Don't drag if pinned

        if (e.target.tagName === "TEXTAREA" || e.target.tagName === "INPUT" || e.target.closest('button')) return; // Allow text selection and button clicks

        e.stopPropagation(); // Prevent board scroll when dragging note
        e.preventDefault(); // Also prevent default to ensure board drag doesn't start

        setIsDragging(true);
        const rect = noteRef.current.getBoundingClientRect();
        offset.current = {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top,
        };
    };

    const handleTouchStart = (e) => {
        if (note.pinned) return;
        if (e.target.tagName === "TEXTAREA" || e.target.tagName === "INPUT" || e.target.closest('button')) return;

        setIsDragging(true);
        const touch = e.touches[0];
        const rect = noteRef.current.getBoundingClientRect();
        offset.current = {
            x: touch.clientX - rect.left,
            y: touch.clientY - rect.top,
        };
    };

    useEffect(() => {
        const handleMouseMove = (e) => {
            if (!isDragging) return;

            const parentRect = noteRef.current.parentElement.getBoundingClientRect();

            const newX = (e.clientX - parentRect.left - offset.current.x) / scale;
            const newY = (e.clientY - parentRect.top - offset.current.y) / scale;

            onUpdate({ ...note, x: newX, y: newY });
        };

        const handleMouseUp = () => {
            setIsDragging(false);
        };

        const handleTouchMove = (e) => {
            if (!isDragging) return;
            e.preventDefault(); // Prevent scrolling while dragging

            const touch = e.touches[0];
            const parentRect = noteRef.current.parentElement.getBoundingClientRect();

            const newX = (touch.clientX - parentRect.left - offset.current.x) / scale;
            const newY = (touch.clientY - parentRect.top - offset.current.y) / scale;

            onUpdate({ ...note, x: newX, y: newY });
        };

        const handleTouchEnd = () => {
            setIsDragging(false);
        };

        if (isDragging) {
            window.addEventListener("mousemove", handleMouseMove);
            window.addEventListener("mouseup", handleMouseUp);
            window.addEventListener("touchmove", handleTouchMove, { passive: false });
            window.addEventListener("touchend", handleTouchEnd);
        }

        return () => {
            window.removeEventListener("mousemove", handleMouseMove);
            window.removeEventListener("mouseup", handleMouseUp);
            window.removeEventListener("touchmove", handleTouchMove);
            window.removeEventListener("touchend", handleTouchEnd);
        };
    }, [isDragging, note, onUpdate, scale]);

    const togglePin = () => {
        onUpdate({ ...note, pinned: !note.pinned });
    };

    const changeColor = (newColor) => {
        onUpdate({ ...note, color: newColor });
        setShowColorPicker(false);
    };

    const handleDueDateChange = (newDate) => {
        onUpdate({ ...note, dueDate: newDate, due_date: newDate });
        setShowDatePicker(false);
    };

    const submitAppend = () => {
        const trimmed = appendText.trim();
        if (!trimmed) return;
        const newText = (note.text || "").trim() ? `${(note.text || "").trim()}\n${trimmed}` : trimmed;
        onUpdate({ ...note, text: newText });
        setAppendText("");
    };

    let badgeBg = "bg-zinc-200 text-zinc-700";
    let badgeText = `📅 ${dueDateVal}`;
    if (daysLeft !== null) {
        if (daysLeft < 0) {
            badgeBg = "bg-red-500 text-white";
            badgeText = `📅 期限切れ (${Math.abs(daysLeft)}日)`;
        } else if (daysLeft === 0) {
            badgeBg = "bg-orange-500 text-white";
            badgeText = "📅 今日が期限";
        }
    }

    return (
        <div
            ref={noteRef}
            data-sticky-note="true"
            className={`${styles.note} ${note.pinned ? styles.pinned : ''} ${isLarge ? styles.large : ''} ${note.gray ? styles.gray : ''}`}
            style={{
                left: note.x,
                top: note.y,
                backgroundColor: note.gray ? '#e0e0e0' : (note.color || COLORS[0]),
                transform: `scale(${isDragging ? 1.05 : 1})`,
                zIndex: isDragging ? 1000 : 1,
            }}
            onMouseDown={handleMouseDown}
            onMouseUp={onMouseUp}
            onTouchStart={handleTouchStart}
        >
            <button
                className={styles.pinButton}
                onClick={togglePin}
                onMouseDown={(e) => e.stopPropagation()}
                title={note.pinned ? "ピン留めを外す" : "ピン留めする"}
            >
                {note.pinned ? "📌" : "📍"}
            </button>
            <button
                className={styles.colorButton}
                onClick={() => setShowColorPicker(!showColorPicker)}
                onMouseDown={(e) => e.stopPropagation()}
                title="色を変更"
            >
                🎨
            </button>
            <button
                style={{ position: "absolute", top: "4px", right: "28px", background: "none", border: "none", cursor: "pointer", fontSize: "12px" }}
                onClick={(e) => {
                    e.stopPropagation();
                    setShowDatePicker(!showDatePicker);
                }}
                onMouseDown={(e) => e.stopPropagation()}
                title="期限を設定"
            >
                📅
            </button>
            <button
                className={styles.deleteButton}
                onClick={(e) => {
                    e.stopPropagation();
                    if (window.confirm("この付箋を削除してもよろしいですか？")) {
                        onDelete(note.id);
                    }
                }}
                onMouseDown={(e) => e.stopPropagation()}
                title="削除"
            >
                🗑️
            </button>

            {showColorPicker && (
                <div className={styles.colorPicker}>
                    {COLORS.map((c) => (
                        <button
                            key={c}
                            className={styles.colorOption}
                            style={{ backgroundColor: c }}
                            onClick={() => changeColor(c)}
                            onMouseDown={(e) => e.stopPropagation()}
                        />
                    ))}
                </div>
            )}

            {showDatePicker && (
                <div
                    style={{
                        position: "absolute",
                        top: "28px",
                        right: "8px",
                        background: "#fff",
                        padding: "6px",
                        borderRadius: "6px",
                        boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                        zIndex: 10,
                        display: "flex",
                        alignItems: "center",
                        gap: "4px"
                    }}
                    onClick={(e) => e.stopPropagation()}
                    onMouseDown={(e) => e.stopPropagation()}
                >
                    <input
                        type="date"
                        value={dueDateVal}
                        onChange={(e) => handleDueDateChange(e.target.value)}
                        style={{ fontSize: "12px", padding: "2px" }}
                    />
                    {dueDateVal && (
                        <button
                            type="button"
                            onClick={() => handleDueDateChange("")}
                            style={{ fontSize: "10px", padding: "2px 4px" }}
                        >
                            消去
                        </button>
                    )}
                </div>
            )}

            {note.imageUrl && (
                <div className={styles.imageContainer}>
                    <img src={note.imageUrl} alt="Sticky note capture" className={styles.image} />
                </div>
            )}

            {dueDateVal && (
                <div style={{ marginTop: "16px", marginBottom: "4px" }}>
                    <span
                        onClick={(e) => {
                            e.stopPropagation();
                            setShowDatePicker(!showDatePicker);
                        }}
                        style={{
                            fontSize: "11px",
                            fontWeight: "bold",
                            padding: "2px 6px",
                            borderRadius: "4px",
                            cursor: "pointer",
                            display: "inline-block"
                        }}
                        className={badgeBg}
                    >
                        {badgeText}
                    </span>
                </div>
            )}

            {/* 既存テキストは表示のみ（URLはリンク化）。追記のみ可能 */}
            <div className={styles.noteContent} style={{ marginTop: dueDateVal ? "4px" : "18px" }}>
                {(note.text || "").trim() ? (
                    <LinkifiedText text={note.text} className={styles.linkifiedText} />
                ) : null}
            </div>
            <textarea
                className={styles.appendInput}
                placeholder={note.text ? "追記... (Shift+Enter: 改行 / Enter: 反映)" : "入力... (Shift+Enter: 改行 / Enter: 反映)"}
                value={appendText}
                onChange={(e) => setAppendText(e.target.value)}
                onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        submitAppend();
                    }
                }}
                onBlur={() => appendText.trim() && submitAppend()}
            />
            {note.groupId && (
                <div className={styles.groupBadge} title={`Group ID: ${note.groupId}`}>
                    🔗 Group
                </div>
            )}
            {note.author && (
                <div className={styles.authorBadge} title={`作成者: ${note.author}`}>
                    {note.author}
                </div>
            )}
        </div>
    );
}