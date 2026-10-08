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
    if (!y || !m || !d) return null;
    const due = new Date(y, m - 1, d);
    due.setHours(0, 0, 0, 0);
    return Math.round((due.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
}

export default function StickyNote({
    note,
    onUpdate,
    onDelete,
    scale,
    isSelected,
    onSelect,
    onMoveSelectedNotes,
    onMouseDown,
    onMouseUp,
    isSpacePressed
}) {
    const [isDragging, setIsDragging] = useState(false);
    const [appendText, setAppendText] = useState("");
    const [showColorPicker, setShowColorPicker] = useState(false);
    const [showDatePicker, setShowDatePicker] = useState(false);

    const dueDateVal = note.dueDate ?? "";
    const [tempDueDate, setTempDueDate] = useState(dueDateVal);

    const noteRef = useRef(null);
    const lastMousePos = useRef({ x: 0, y: 0 });

    const dragOffset = useRef({ x: 0, y: 0 });
    const initialPos = useRef({ x: note.x, y: note.y });

    // ★跳ね防止：ドラッグ完了から親のprops更新完了までの間、最新位置を保護保持するRef
    const lastDraggedPos = useRef(null);

    const isLarge = note.ratioW && note.ratioW >= 0.2;
    const daysLeft = calcDaysLeft(dueDateVal);

    useEffect(() => {
        setTempDueDate(note.dueDate ?? "");
    }, [note.dueDate]);

    // ★親から新しい note.x, note.y が届いたら保護フラグをクリア
    useEffect(() => {
        if (lastDraggedPos.current) {
            if (Math.abs(note.x - lastDraggedPos.current.x) < 0.1 && Math.abs(note.y - lastDraggedPos.current.y) < 0.1) {
                lastDraggedPos.current = null;
            }
        }
    }, [note.x, note.y]);

    useEffect(() => {
        if (!isDragging && noteRef.current && !lastDraggedPos.current) {
            noteRef.current.style.left = `${note.x}px`;
            noteRef.current.style.top = `${note.y}px`;
            noteRef.current.style.transform = "none";
            noteRef.current.style.transition = "";
            noteRef.current.style.willChange = "auto";
        }
    }, [note.x, note.y, isDragging]);

    const handleMouseDown = (e) => {
        if (onMouseDown) onMouseDown(e);
        if (e.defaultPrevented || e.altKey) return;

        if (e.button === 1 || (e.button === 0 && isSpacePressed)) {
            return;
        }

        if (e.button !== 0) return;
        if (note.pinned) return;

        if (e.target.tagName === "TEXTAREA" || e.target.tagName === "INPUT" || e.target.closest('button')) return;

        e.stopPropagation();

        if (onSelect) {
            onSelect(note.id, e.shiftKey);
        }

        lastDraggedPos.current = null;
        setIsDragging(true);
        lastMousePos.current = { x: e.clientX, y: e.clientY };
        dragOffset.current = { x: 0, y: 0 };
        initialPos.current = { x: note.x, y: note.y };
    };

    const handleTouchStart = (e) => {
        if (note.pinned || isSpacePressed) return;
        if (e.target.tagName === "TEXTAREA" || e.target.tagName === "INPUT" || e.target.closest('button')) return;

        if (onSelect) {
            onSelect(note.id, false);
        }

        lastDraggedPos.current = null;
        setIsDragging(true);
        const touch = e.touches[0];
        lastMousePos.current = { x: touch.clientX, y: touch.clientY };
        dragOffset.current = { x: 0, y: 0 };
        initialPos.current = { x: note.x, y: note.y };
    };

    useEffect(() => {
        const moveSelectedNotes = () => {
            if (!isSelected || !onMoveSelectedNotes) return;
            document
                .querySelectorAll(`[data-sticky-note="true"].${styles.selected}`)
                .forEach((el) => {
                    if (el === noteRef.current || el.classList.contains(styles.pinned)) return;
                    el.style.willChange = "transform";
                    el.style.transition = "none";
                    el.style.transform = `translate3d(${dragOffset.current.x}px, ${dragOffset.current.y}px, 0)`;
                });
        };

        const moveDrag = (clientX, clientY) => {
            if (!isDragging) return;
            const dx = (clientX - lastMousePos.current.x) / scale;
            const dy = (clientY - lastMousePos.current.y) / scale;
            lastMousePos.current = { x: clientX, y: clientY };
            dragOffset.current.x += dx;
            dragOffset.current.y += dy;

            if (noteRef.current) {
                noteRef.current.style.willChange = "transform";
                noteRef.current.style.transition = "none";
                noteRef.current.style.transform = `translate3d(${dragOffset.current.x}px, ${dragOffset.current.y}px, 0)`;
            }
            moveSelectedNotes();
        };

        const finishDrag = () => {
            if (!isDragging) return;
            setIsDragging(false);

            const { x: dx, y: dy } = dragOffset.current;

            if (dx === 0 && dy === 0) {
                if (noteRef.current) {
                    noteRef.current.style.transform = "none";
                }
                return;
            }

            const newX = initialPos.current.x + dx;
            const newY = initialPos.current.y + dy;

            lastDraggedPos.current = { x: newX, y: newY };

            if (noteRef.current) {
                noteRef.current.style.transition = "none";
                noteRef.current.style.left = `${newX}px`;
                noteRef.current.style.top = `${newY}px`;
                noteRef.current.style.transform = "none";
            }

            if (onMoveSelectedNotes && isSelected) {
                document
                    .querySelectorAll(`[data-sticky-note="true"].${styles.selected}`)
                    .forEach((el) => {
                        if (el === noteRef.current || el.classList.contains(styles.pinned)) return;
                        const currentLeft = parseFloat(el.style.left) || 0;
                        const currentTop = parseFloat(el.style.top) || 0;
                        el.style.transition = "none";
                        el.style.left = `${currentLeft + dx}px`;
                        el.style.top = `${currentTop + dy}px`;
                        el.style.transform = "none";
                    });

                onMoveSelectedNotes(note.id, dx, dy);
                return;
            }
            onUpdate({ ...note, x: newX, y: newY });
        };

        const handleMouseMove = (e) => moveDrag(e.clientX, e.clientY);
        const handleTouchMove = (e) => {
            e.preventDefault();
            const touch = e.touches[0];
            if (touch) moveDrag(touch.clientX, touch.clientY);
        };

        if (isDragging) {
            window.addEventListener("mousemove", handleMouseMove);
            window.addEventListener("mouseup", finishDrag);
            window.addEventListener("touchmove", handleTouchMove, { passive: false });
            window.addEventListener("touchend", finishDrag);
        }

        return () => {
            window.removeEventListener("mousemove", handleMouseMove);
            window.removeEventListener("mouseup", finishDrag);
            window.removeEventListener("touchmove", handleTouchMove);
            window.removeEventListener("touchend", finishDrag);
        };
    }, [isDragging, note, onUpdate, onMoveSelectedNotes, scale, isSelected]);

    const togglePin = () => {
        onUpdate({ ...note, pinned: !note.pinned });
    };

    const changeColor = (newColor) => {
        onUpdate({ ...note, color: newColor });
        setShowColorPicker(false);
    };

    const saveDueDate = (newDate) => {
        onUpdate({ ...note, dueDate: newDate });
        setShowDatePicker(false);
    };

    const submitAppend = () => {
        const trimmed = appendText.trim();
        if (!trimmed) return;
        const newText = (note.text || "").trim() ? `${(note.text || "").trim()}\n${trimmed}` : trimmed;
        onUpdate({ ...note, text: newText });
        setAppendText("");
    };

    let badgeClass = styles.badgeDefault;
    let cardHighlightClass = "";
    let badgeText = `📅 期限: ${dueDateVal}`;

    if (daysLeft !== null) {
        if (daysLeft < 0) {
            badgeClass = styles.badgeExpired;
            cardHighlightClass = styles.noteExpiredBorder;
            badgeText = `⚠️ 期限切れ（${Math.abs(daysLeft)}日経過）`;
        } else if (daysLeft === 0) {
            badgeClass = styles.badgeToday;
            cardHighlightClass = styles.noteTodayBorder;
            badgeText = "🔥 本期日が期限！";
        } else if (daysLeft <= 3) {
            badgeClass = styles.badgeToday;
            badgeText = `⏰ 期限まであと${daysLeft}日`;
        } else if (daysLeft <= 10) {
            badgeClass = styles.badgeWarning;
            badgeText = `📅 期限まであと${daysLeft}日`;
        }
    }

    let displayX = note.x;
    let displayY = note.y;
    if (lastDraggedPos.current) {
        displayX = lastDraggedPos.current.x;
        displayY = lastDraggedPos.current.y;
    }

    return (
        <div
            ref={noteRef}
            data-sticky-note="true"
            data-note-id={note.id}
            className={`${styles.note} ${note.pinned ? styles.pinned : ''} ${isSelected ? styles.selected : ''} ${isLarge ? styles.large : ''} ${note.gray ? styles.gray : ''} ${cardHighlightClass}`}
            style={{
                left: displayX,
                top: displayY,
                backgroundColor: note.gray ? '#e0e0e0' : (note.color || COLORS[0]),
                zIndex: isDragging ? 1000 : (isSelected ? 500 : 1),
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
                className={styles.dateButton}
                onClick={(e) => {
                    e.stopPropagation();
                    setTempDueDate(dueDateVal);
                    setShowDatePicker(!showDatePicker);
                    setShowColorPicker(false);
                }}
                onMouseDown={(e) => e.stopPropagation()}
                title="期限を設定"
            >
                📅
            </button>
            <button
                className={styles.colorButton}
                onClick={(e) => {
                    e.stopPropagation();
                    setShowColorPicker(!showColorPicker);
                    setShowDatePicker(false);
                }}
                onMouseDown={(e) => e.stopPropagation()}
                title="色を変更"
            >
                🎨
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
                    className={styles.datePickerPopover}
                    onClick={(e) => e.stopPropagation()}
                    onMouseDown={(e) => e.stopPropagation()}
                    onTouchStart={(e) => e.stopPropagation()}
                >
                    <input
                        type="date"
                        value={tempDueDate}
                        onChange={(e) => setTempDueDate(e.target.value)}
                        onMouseDown={(e) => e.stopPropagation()}
                        className={styles.dateInput}
                    />
                    <button
                        type="button"
                        onClick={() => saveDueDate(tempDueDate)}
                        className={styles.saveBtn}
                    >
                        保存
                    </button>
                    {dueDateVal && (
                        <button
                            type="button"
                            onClick={() => saveDueDate("")}
                            className={styles.clearBtn}
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
                <div className={styles.dueDateContainer}>
                    <span
                        onClick={(e) => {
                            e.stopPropagation();
                            setTempDueDate(dueDateVal);
                            setShowDatePicker(!showDatePicker);
                            setShowColorPicker(false);
                        }}
                        onMouseDown={(e) => e.stopPropagation()}
                        className={`${styles.dueDateBadge} ${badgeClass}`}
                    >
                        {badgeText}
                    </span>
                </div>
            )}

            <div className={styles.noteContent}>
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
                onMouseDown={(e) => e.stopPropagation()}
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