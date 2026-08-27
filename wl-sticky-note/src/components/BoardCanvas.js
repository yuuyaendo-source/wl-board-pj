import styles from "./BoardCanvas.module.css";
import StickyNote from "./StickyNote";

export default function BoardCanvas({
    notes,
    lines,
    onUpdateNote,
    onDeleteNote,
    onAddLine,
    scale,
    selectedNoteIds = [],
    onSelectNote,
    onMoveSelectedNotes,
    selectionBox
}) {
    // 範囲選択ボックス（正規化計算）
    let boxStyle = null;
    if (selectionBox) {
        const left = Math.min(selectionBox.startX, selectionBox.currentX);
        const top = Math.min(selectionBox.startY, selectionBox.currentY);
        const width = Math.abs(selectionBox.currentX - selectionBox.startX);
        const height = Math.abs(selectionBox.currentY - selectionBox.startY);

        boxStyle = {
            left: `${left}px`,
            top: `${top}px`,
            width: `${width}px`,
            height: `${height}px`,
        };
    }

    return (
        <div
            className={styles.canvas}
            style={{
                transform: `scale(${scale})`,
                transformOrigin: "0 0",
                width: "4000px",
                height: "4000px"
            }}
        >
            <svg className={styles.svgLayer}>
                {lines.map((line, i) => (
                    <line
                        key={i}
                        x1={line.x1}
                        y1={line.y1}
                        x2={line.x2}
                        y2={line.y2}
                        stroke="#333"
                        strokeWidth="2"
                    />
                ))}
            </svg>

            {selectionBox && boxStyle && (
                <div className={styles.selectionBox} style={boxStyle} />
            )}

            {notes.map((note) => (
                <StickyNote
                    key={note.id}
                    note={note}
                    onUpdate={onUpdateNote}
                    onDelete={onDeleteNote}
                    scale={scale}
                    isSelected={selectedNoteIds.includes(note.id)}
                    onSelect={onSelectNote}
                    onMoveSelectedNotes={onMoveSelectedNotes}
                />
            ))}
        </div>
    );
}