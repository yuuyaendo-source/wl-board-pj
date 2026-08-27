import styles from "./BoardCanvas.module.css";
import StickyNote from "./StickyNote";

export default function BoardCanvas({
    canvasOuterRef,
    canvasRef,
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
    const baseWidth = 4000;
    const baseHeight = 4000;

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

    const scaledWidth = baseWidth * scale;
    const scaledHeight = baseHeight * scale;

    return (
        /* 外側ラッパー：flexShrink: 0 で横幅の潰れを防止 */
        <div
            ref={canvasOuterRef}
            className={styles.canvasOuter}
            style={{
                width: `max(100%, ${scaledWidth}px)`,
                height: `max(calc(100vh - 60px), ${scaledHeight}px)`,
                flexShrink: 0,
            }}
        >
            {/* 内側キャンバス：中心(2000, 2000)を基準に全方位へ拡大縮小 */}
            <div
                ref={canvasRef}
                className={styles.canvas}
                style={{
                    width: `${baseWidth}px`,
                    height: `${baseHeight}px`,
                    left: `calc(50% - ${baseWidth / 2}px)`,
                    top: `calc(50% - ${baseHeight / 2}px)`,
                    transform: `scale(${scale})`,
                    transformOrigin: "center center",
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
        </div>
    );
}