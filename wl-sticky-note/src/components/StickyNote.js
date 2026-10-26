import { useState, useRef, useEffect } from "react";
import LinkifiedText from "./LinkifiedText";
import styles from "./StickyNote.module.css";
import { getDueDateStatusText, formatWithDay } from "@shared/utils/dueDate";
import { isGrayNote } from "@shared/utils/grayNote";

const COLORS = [
    "#ffeb3b", "#a7ffeb", "#ffcdd2", "#e1bee7",
    "#fff9c4", "#c5e1a5", "#ffccbc", "#b3e5fc", "#ffffff"
];

export default function StickyNote({
    note,
    onUpdate,
    onDelete,
    scale,
    isSelected,
    onSelect,
    onMoveSelectedNotes,
    isSpacePressed
}) {
    const [isDragging, setIsDragging] = useState(false);
    const [appendText, setAppendText] = useState("");
    const appendTextRef = useRef(""); // 修正⑦: 最新入力を同期管理するRef
    const [showColorPicker, setShowColorPicker] = useState(false);
    const [showDatePicker, setShowDatePicker] = useState(false);

    const dueDateVal = note.dueDate ?? "";
    const [tempDueDate, setTempDueDate] = useState(dueDateVal);

    const noteRef = useRef(null);
    const dateInputRef = useRef(null);
    const lastMousePos = useRef({ x: 0, y: 0 });

    const dragOffset = useRef({ x: 0, y: 0 });
    const initialPos = useRef({ x: note.x, y: note.y });

    // 跳ね防止：ドラッグ完了から親のprops更新完了までの間、最新位置を保護保持するRef
    const lastDraggedPos = useRef(null);

    const dueDateStatus = getDueDateStatusText(dueDateVal);

    useEffect(() => {
        setTempDueDate(note.dueDate ?? "");
    }, [note.dueDate]);

    // 連動移動時：直接掴んでいない付箋もドラッグ確定座標を受け取って保護保持する
    useEffect(() => {
        const handleRemoteDragged = (e) => {
            const moved = e.detail?.[note.id];
            if (moved) {
                lastDraggedPos.current = { x: moved.x, y: moved.y };
            }
        };
        window.addEventListener("wl-note-dragged", handleRemoteDragged);
        return () => window.removeEventListener("wl-note-dragged", handleRemoteDragged);
    }, [note.id]);

    // 親から新しい note.x, note.y が届いたら保護フラグをクリア
    useEffect(() => {
        if (lastDraggedPos.current) {
            if (Math.abs(note.x - lastDraggedPos.current.x) < 0.1 && Math.abs(note.y - lastDraggedPos.current.y) < 0.1) {
                lastDraggedPos.current = null;
            }
        }
    }, [note.x, note.y]);

    useEffect(() => {
        const isFollowing = noteRef.current?.getAttribute("data-drag-following") === "true";
        if (!isDragging && !isFollowing && noteRef.current && !lastDraggedPos.current) {
            noteRef.current.style.left = `${note.x}px`;
            noteRef.current.style.top = `${note.y}px`;
            noteRef.current.style.transform = "none";
            noteRef.current.style.transition = "";
            noteRef.current.style.willChange = "auto";
        }
    }, [note.x, note.y, isDragging]);

    const handleMouseDown = (e) => {
        if (e.defaultPrevented || e.altKey) return;

        if (e.button === 1 || (e.button === 0 && isSpacePressed)) {
            return;
        }

        if (e.button !== 0) return;
        if (note.pinned) return;

        if (
            e.target.tagName === "TEXTAREA" ||
            e.target.tagName === "INPUT" ||
            e.target.closest('button') ||
            e.target.closest('a')
        ) return;

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
        if (
            e.target.tagName === "TEXTAREA" ||
            e.target.tagName === "INPUT" ||
            e.target.closest('button') ||
            e.target.closest('a')
        ) return;

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
                    el.setAttribute("data-drag-following", "true");
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
                document
                    .querySelectorAll(`[data-sticky-note="true"][data-drag-following="true"]`)
                    .forEach((el) => {
                        el.removeAttribute("data-drag-following");
                        el.style.transform = "none";
                    });
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
                const movedNotes = {};
                movedNotes[note.id] = { x: newX, y: newY };

                document
                    .querySelectorAll(`[data-sticky-note="true"].${styles.selected}`)
                    .forEach((el) => {
                        if (el === noteRef.current || el.classList.contains(styles.pinned)) return;
                        const currentLeft = parseFloat(el.style.left) || 0;
                        const currentTop = parseFloat(el.style.top) || 0;
                        const targetX = currentLeft + dx;
                        const targetY = currentTop + dy;
                        el.style.transition = "none";
                        el.style.left = `${targetX}px`;
                        el.style.top = `${targetY}px`;
                        el.style.transform = "none";
                        el.removeAttribute("data-drag-following");

                        const nid = el.getAttribute("data-note-id");
                        if (nid) {
                            movedNotes[nid] = { x: targetX, y: targetY };
                        }
                    });

                // 連動移動したすべての付箋のドラッグ確定座標を各インスタンスに同期
                window.dispatchEvent(new CustomEvent("wl-note-dragged", { detail: movedNotes }));

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

    // 修正⑦: 入力変更ハンドラでRefを同期更新
    const handleAppendChange = (e) => {
        setAppendText(e.target.value);
        appendTextRef.current = e.target.value;
    };

    // 修正⑦: Refを参照し、送信時に即時初期化して二重発火を抑止
    const submitAppend = () => {
        const trimmed = appendTextRef.current.trim();
        if (!trimmed) return;
        appendTextRef.current = "";
        setAppendText("");
        const newText = (note.text || "").trim() ? `${(note.text || "").trim()}\n${trimmed}` : trimmed;
        onUpdate({ ...note, text: newText });
    };

    const handleOpenPicker = (e) => {
        e.stopPropagation();
        if (dateInputRef.current) {
            if (typeof dateInputRef.current.showPicker === "function") {
                try {
                    dateInputRef.current.showPicker();
                } catch {
                    dateInputRef.current.focus();
                }
            } else {
                dateInputRef.current.click();
            }
        }
    };

    let badgeClass = styles.badgeDefault;
    let cardHighlightClass = "";
    let badgeText = `📅 期限: ${formatWithDay(dueDateVal)}`;

    if (dueDateStatus.status === "expired") {
        badgeClass = styles.badgeExpired;
        cardHighlightClass = styles.noteExpiredBorder;
        badgeText = dueDateStatus.label;
    } else if (dueDateStatus.status === "today") {
        badgeClass = styles.badgeToday;
        cardHighlightClass = styles.noteTodayBorder;
        badgeText = dueDateStatus.label;
    } else if (dueDateStatus.status === "urgent") {
        badgeClass = styles.badgeToday;
        badgeText = dueDateStatus.label;
    } else if (dueDateStatus.daysLeft !== null && dueDateStatus.daysLeft <= 10) {
        badgeClass = styles.badgeWarning;
        badgeText = dueDateStatus.label;
    }

    let displayX = note.x;
    let displayY = note.y;
    if (lastDraggedPos.current) {
        displayX = lastDraggedPos.current.x;
        displayY = lastDraggedPos.current.y;
    }

    const isGray = isGrayNote(note);

    return (
        <div
            ref={noteRef}
            data-sticky-note="true"
            data-note-id={note.id}
            className={`${styles.note} ${note.pinned ? styles.pinned : ''} ${isSelected ? styles.selected : ''} ${isGray ? styles.gray : ''} ${cardHighlightClass}`}
            style={{
                left: displayX,
                top: displayY,
                backgroundColor: isGray ? '#e0e0e0' : (note.color || COLORS[0]),
                zIndex: isDragging ? 1000 : (isSelected ? 500 : 1),
            }}
            onMouseDown={handleMouseDown}
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
                    <div style={{ position: "relative", display: "inline-flex", alignItems: "center" }}>
                        <button
                            type="button"
                            onClick={handleOpenPicker}
                            style={{
                                fontSize: "12px",
                                padding: "4px 8px",
                                border: "1px solid #ccc",
                                borderRadius: "4px",
                                background: "#fff",
                                cursor: "pointer",
                                display: "flex",
                                alignItems: "center",
                                gap: "4px"
                            }}
                        >
                            <span>{tempDueDate ? formatWithDay(tempDueDate) : "未設定"}</span>
                            <span>📅</span>
                        </button>
                        <input
                            ref={dateInputRef}
                            type="date"
                            value={tempDueDate}
                            onChange={(e) => setTempDueDate(e.target.value)}
                            onMouseDown={(e) => e.stopPropagation()}
                            tabIndex={-1}
                            aria-hidden="true"
                            style={{
                                position: "absolute",
                                width: 0,
                                height: 0,
                                opacity: 0,
                                pointerEvents: "none"
                            }}
                        />
                    </div>
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
                onChange={handleAppendChange}
                onKeyDown={(e) => {
                    // 日本語IME変換中のEnter打鍵（確定操作）時は送信処理をバイパス
                    if (e.nativeEvent.isComposing || e.keyCode === 229) return;
                    if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        submitAppend();
                    }
                }}
                onBlur={() => appendTextRef.current.trim() && submitAppend()}
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