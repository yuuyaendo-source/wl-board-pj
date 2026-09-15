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

    // ドラッグ中のパフォーマンス最適化用Ref
    const dragOffset = useRef({ x: 0, y: 0 });
    const initialPos = useRef({ x: note.x, y: note.y });

    const isLarge = note.ratioW && note.ratioW >= 0.2;
    const daysLeft = calcDaysLeft(dueDateVal);

    useEffect(() => {
        setTempDueDate(note.dueDate ?? "");
    }, [note.dueDate]);

    // ドラッグ中でない場合は props の座標・選択状態をDOMへ同期
    useEffect(() => {
        if (!isDragging && noteRef.current) {
            noteRef.current.style.left = `${note.x}px`;
            noteRef.current.style.top = `${note.y}px`;
            noteRef.current.style.transform = `scale(1)`;
        }
    }, [note.x, note.y, isDragging]);

    const handleMouseDown = (e) => {
        if (onMouseDown) onMouseDown(e);
        if (e.defaultPrevented || e.altKey) return;

        // 中ボタン(button===1) または Spaceキー押下(button===0 && isSpacePressed) の場合は、
        // 付箋の選択・移動を行わず親要素（ボード）のパン移動へ透過させる
        if (e.button === 1 || (e.button === 0 && isSpacePressed)) {
            return;
        }

        if (e.button !== 0) return;
        if (note.pinned) return;

        if (e.target.tagName === "TEXTAREA" || e.target.tagName === "INPUT" || e.target.closest('button')) return;

        e.stopPropagation();

        // 選択ハンドリング（Shiftキー考慮）
        if (onSelect) {
            onSelect(note.id, e.shiftKey);
        }

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

        setIsDragging(true);
        const touch = e.touches[0];
        lastMousePos.current = { x: touch.clientX, y: touch.clientY };
        dragOffset.current = { x: 0, y: 0 };
        initialPos.current = { x: note.x, y: note.y };
    };

    useEffect(() => {
        const handleMouseMove = (e) => {
            if (!isDragging) return;

            const dx = (e.clientX - lastMousePos.current.x) / scale;
            const dy = (e.clientY - lastMousePos.current.y) / scale;
            lastMousePos.current = { x: e.clientX, y: e.clientY };

            dragOffset.current.x += dx;
            dragOffset.current.y += dy;

            // ReactのStateを即時更新せず、DOMを直接操作してフレームレートを向上
            if (noteRef.current) {
                const newX = initialPos.current.x + dragOffset.current.x;
                const newY = initialPos.current.y + dragOffset.current.y;
                noteRef.current.style.left = `${newX}px`;
                noteRef.current.style.top = `${newY}px`;
                noteRef.current.style.transform = `scale(1.05)`;
            }

            if (isSelected && onMoveSelectedNotes) {
                const selectedEls = document.querySelectorAll(`[data-sticky-note="true"].${styles.selected}`);
                selectedEls.forEach(el => {
                    if (el !== noteRef.current && !el.classList.contains(styles.pinned)) {
                        const currentLeft = parseFloat(el.style.left) || 0;
                        const currentTop = parseFloat(el.style.top) || 0;
                        el.style.left = `${currentLeft + dx}px`;
                        el.style.top = `${currentTop + dy}px`;
                    }
                });
            }
        };

        const handleMouseUp = () => {
            if (isDragging) {
                setIsDragging(false);
                const dx = dragOffset.current.x;
                const dy = dragOffset.current.y;

                // ドラッグ終了時にまとめて1回だけサーバー更新・ステート更新
                if (dx !== 0 || dy !== 0) {
                    if (onMoveSelectedNotes && isSelected) {
                        onMoveSelectedNotes(note.id, dx, dy);
                    } else {
                        onUpdate({ ...note, x: initialPos.current.x + dx, y: initialPos.current.y + dy });
                    }
                }
            }
        };

        const handleTouchMove = (e) => {
            if (!isDragging) return;
            e.preventDefault();

            const touch = e.touches[0];
            const dx = (touch.clientX - lastMousePos.current.x) / scale;
            const dy = (touch.clientY - lastMousePos.current.y) / scale;
            lastMousePos.current = { x: touch.clientX, y: touch.clientY };

            dragOffset.current.x += dx;
            dragOffset.current.y += dy;

            if (noteRef.current) {
                const newX = initialPos.current.x + dragOffset.current.x;
                const newY = initialPos.current.y + dragOffset.current.y;
                noteRef.current.style.left = `${newX}px`;
                noteRef.current.style.top = `${newY}px`;
                noteRef.current.style.transform = `scale(1.05)`;
            }

            if (isSelected && onMoveSelectedNotes) {
                const selectedEls = document.querySelectorAll(`[data-sticky-note="true"].${styles.selected}`);
                selectedEls.forEach(el => {
                    if (el !== noteRef.current && !el.classList.contains(styles.pinned)) {
                        const currentLeft = parseFloat(el.style.left) || 0;
                        const currentTop = parseFloat(el.style.top) || 0;
                        el.style.left = `${currentLeft + dx}px`;
                        el.style.top = `${currentTop + dy}px`;
                    }
                });
            }
        };

        const handleTouchEnd = () => {
            if (isDragging) {
                setIsDragging(false);
                const dx = dragOffset.current.x;
                const dy = dragOffset.current.y;

                if (dx !== 0 || dy !== 0) {
                    if (onMoveSelectedNotes && isSelected) {
                        onMoveSelectedNotes(note.id, dx, dy);
                    } else {
                        onUpdate({ ...note, x: initialPos.current.x + dx, y: initialPos.current.y + dy });
                    }
                }
            }
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

    return (
        <div
            ref={noteRef}
            data-sticky-note="true"
            data-note-id={note.id}
            className={`${styles.note} ${note.pinned ? styles.pinned : ''} ${isSelected ? styles.selected : ''} ${isLarge ? styles.large : ''} ${note.gray ? styles.gray : ''} ${cardHighlightClass}`}
            style={{
                left: note.x,
                top: note.y,
                backgroundColor: note.gray ? '#e0e0e0' : (note.color || COLORS[0]),
                transform: `scale(${isDragging ? 1.05 : 1})`,
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