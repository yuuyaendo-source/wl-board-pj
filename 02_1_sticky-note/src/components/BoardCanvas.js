import { useRef, useState } from "react";
import styles from "./BoardCanvas.module.css";
import StickyNote from "./StickyNote";

export default function BoardCanvas({ notes, lines, onUpdateNote, onDeleteNote, onAddLine, scale }) {
    const [drawingLine, setDrawingLine] = useState(null); // { startNoteId, startX, startY, currentX, currentY }

    // Handle line drawing logic here if needed, or keep it simple for now
    // For MVP, we'll just render notes and lines

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

            {notes.map((note) => (
                <StickyNote
                    key={note.id}
                    note={note}
                    onUpdate={onUpdateNote}
                    onDelete={onDeleteNote}
                    scale={scale}
                />
            ))}
        </div>
    );
}
