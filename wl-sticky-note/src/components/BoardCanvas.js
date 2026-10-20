import styles from "./BoardCanvas.module.css";
import StickyNote from "./StickyNote";

export default function BoardCanvas({
    notes,
    onUpdateNote,
    onDeleteNote,
    scale,
    pan,
    selectedNoteIds = [],
    onSelectNote,
    onMoveSelectedNotes,
    selectionBox,
    isSpacePressed
}) {
    const baseWidth = 4000;
    const baseHeight = 4000;

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
        <div className={styles.canvasOuter}>
            <div
                className={styles.canvas}
                style={{
                    width: `${baseWidth}px`,
                    height: `${baseHeight}px`,
                    transform: `translate(${pan.x}px, ${pan.y}px) scale(${scale})`,
                    transformOrigin: "0 0",
                }}
            >
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
                        isSpacePressed={isSpacePressed}
                    />
                ))}
            </div>
        </div>
    );
}