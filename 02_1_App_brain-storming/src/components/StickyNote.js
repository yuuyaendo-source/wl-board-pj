import { useState, useRef, useEffect } from "react";
import styles from "./StickyNote.module.css";

const COLORS = [
    "#ffeb3b", "#a7ffeb", "#ffcdd2", "#e1bee7",
    "#fff9c4", "#c5e1a5", "#ffccbc", "#b3e5fc", "#ffffff"
];

export default function StickyNote({ note, onUpdate, scale, onMouseDown, onMouseUp }) {
    const [isDragging, setIsDragging] = useState(false);
    const noteRef = useRef(null);
    const offset = useRef({ x: 0, y: 0 });

    const handleMouseDown = (e) => {
        if (onMouseDown) onMouseDown(e); // Propagate to parent for line drawing
        if (e.defaultPrevented || e.altKey) return; // Don't drag if line drawing
        if (note.pinned) return; // Don't drag if pinned

        if (e.target.tagName === "TEXTAREA") return; // Allow text selection
        setIsDragging(true);
        const rect = noteRef.current.getBoundingClientRect();
        offset.current = {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top,
        };
    };

    useEffect(() => {
        const handleMouseMove = (e) => {
            if (!isDragging) return;

            // Calculate new position relative to parent (canvas)
            // We need to account for scale
            const parentRect = noteRef.current.parentElement.getBoundingClientRect();

            const newX = (e.clientX - parentRect.left - offset.current.x) / scale;
            const newY = (e.clientY - parentRect.top - offset.current.y) / scale;

            onUpdate({ ...note, x: newX, y: newY });
        };

        const handleMouseUp = () => {
            setIsDragging(false);
        };

        if (isDragging) {
            window.addEventListener("mousemove", handleMouseMove);
            window.addEventListener("mouseup", handleMouseUp);
        }

        return () => {
            window.removeEventListener("mousemove", handleMouseMove);
            window.removeEventListener("mouseup", handleMouseUp);
        };
    }, [isDragging, note, onUpdate, scale]);

    const togglePin = () => {
        onUpdate({ ...note, pinned: !note.pinned });
    };

    const [showColorPicker, setShowColorPicker] = useState(false);

    const changeColor = (newColor) => {
        onUpdate({ ...note, color: newColor });
        setShowColorPicker(false);
    };

    return (
        <div
            ref={noteRef}
            className={`${styles.note} ${note.pinned ? styles.pinned : ''}`}
            style={{
                left: note.x,
                top: note.y,
                backgroundColor: note.color,
                transform: `scale(${isDragging ? 1.05 : 1})`,
                zIndex: isDragging ? 1000 : 1,
            }}
            onMouseDown={handleMouseDown}
            onMouseUp={onMouseUp}
        >
            <button
                className={styles.pinButton}
                onClick={togglePin}
                title={note.pinned ? "ピン留めを外す" : "ピン留めする"}
            >
                {note.pinned ? "📌" : "📍"}
            </button>
            <button
                className={styles.colorButton}
                onClick={() => setShowColorPicker(!showColorPicker)}
                title="色を変更"
            >
                🎨
            </button>
            {showColorPicker && (
                <div className={styles.colorPicker}>
                    {COLORS.map((c) => (
                        <button
                            key={c}
                            className={styles.colorOption}
                            style={{ backgroundColor: c }}
                            onClick={() => changeColor(c)}
                        />
                    ))}
                </div>
            )}
            <textarea
                value={note.text}
                onChange={(e) => onUpdate({ ...note, text: e.target.value })}
                placeholder="Type here..."
                className={styles.textarea}
            />
            {note.groupId && (
                <div className={styles.groupBadge} title={`Group ID: ${note.groupId}`}>
                    🔗 Group
                </div>
            )}
        </div>
    );
}
