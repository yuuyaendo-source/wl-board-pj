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
        /* 外側ラッパー：画面全体（min-100%）にドット背景を維持しつつ描画サイズを確保 */
        <div
            className={styles.canvasOuter}
            style={{
                width: `${scaledWidth}px`,
                height: `${scaledHeight}px`,
            }}
        >
            {/* 内側キャンバス：元の4000pxのスケール変形領域 */}
            <div
                className={styles.canvas}
                style={{
                    width: `${baseWidth}px`,
                    height: `${baseHeight}px`,
                    transform: `scale(${scale})`,
                    transformOrigin: "0 0",
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