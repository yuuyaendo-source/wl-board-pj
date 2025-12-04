"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useParams } from "next/navigation";
import io from "socket.io-client";
import styles from "./page.module.css";
import BoardCanvas from "@/components/BoardCanvas";
import Toolbar from "@/components/Toolbar";
import CommentListPanel from "@/components/CommentListPanel";

let socket;

export default function BoardPage() {
    const { id: boardId } = useParams();
    const [notes, setNotes] = useState([]);
    const [lines, setLines] = useState([]);
    const [color, setColor] = useState("#ffeb3b"); // Default yellow
    const [isConnected, setIsConnected] = useState(false);
    const [scale, setScale] = useState(1);
    const [title, setTitle] = useState("");
    const [showCommentPanel, setShowCommentPanel] = useState(false);
    const boardContainerRef = useRef(null);

    useEffect(() => {
        // Initialize Socket.io connection with reconnection options
        socket = io({
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
            reconnectionAttempts: Infinity
        });

        socket.on("connect", () => {
            console.log("Connected to server");
            setIsConnected(true);
            socket.emit("join-board", boardId);
        });

        socket.on("init-board", (data) => {
            setNotes(data.notes || []);
            setLines(data.lines || []);
        });

        socket.on("note-added", (note) => {
            setNotes((prev) => {
                // Prevent duplicate - check if note with this ID already exists
                if (prev.some(n => n.id === note.id)) {
                    return prev;
                }
                return [...prev, note];
            });
        });

        socket.on("note-updated", (updatedNote) => {
            setNotes((prev) =>
                prev.map((n) => (n.id === updatedNote.id ? updatedNote : n))
            );
        });

        socket.on("line-added", (line) => {
            setLines((prev) => [...prev, line]);
        });

        socket.on("disconnect", () => {
            console.log("Disconnected from server");
            setIsConnected(false);
        });

        return () => {
            socket.disconnect();
        };
    }, [boardId]);

    const addNote = () => {
        // Generate more unique ID with timestamp + random
        const timestamp = Date.now().toString(36);
        const random = Math.random().toString(36).substr(2, 9);

        // Position new notes at bottom center of viewport
        const container = document.querySelector(`.${styles.boardContainer}`);
        const containerRect = container?.getBoundingClientRect() || { width: window.innerWidth, height: window.innerHeight };
        const scrollLeft = container?.scrollLeft || 0;
        const scrollTop = container?.scrollTop || 0;

        const centerX = scrollLeft + (containerRect.width / 2) - 100; // Center minus half note width
        const bottomY = scrollTop + containerRect.height - 280; // Bottom minus note height and some margin

        const newNote = {
            id: `${timestamp}-${random}`,
            text: "",
            x: centerX + Math.random() * 20 - 10, // Small random offset
            y: bottomY + Math.random() * 20 - 10,
            color: color,
            pinned: false,
        };
        // Optimistic update
        setNotes((prev) => [...prev, newNote]);
        socket.emit("add-note", { boardId, note: newNote });
    };

    const notesRef = useRef(notes);
    useEffect(() => {
        notesRef.current = notes;
    }, [notes]);

    const updateTimeout = useRef(null);

    const updateNote = useCallback((updatedNote) => {
        const currentNotes = notesRef.current;
        const originalNote = currentNotes.find(n => n.id === updatedNote.id);

        let notesToUpdate = [updatedNote];

        if (originalNote && updatedNote.groupId) {
            const dx = updatedNote.x - originalNote.x;
            const dy = updatedNote.y - originalNote.y;

            if (dx !== 0 || dy !== 0) {
                const groupNotes = currentNotes.filter(
                    n => n.groupId === updatedNote.groupId && n.id !== updatedNote.id
                );

                const additionalUpdates = groupNotes.map(n => ({
                    ...n,
                    x: n.x + dx,
                    y: n.y + dy
                }));

                notesToUpdate = [...notesToUpdate, ...additionalUpdates];
            }
        }

        setNotes((prev) => {
            return prev.map((n) => {
                const updated = notesToUpdate.find(un => un.id === n.id);
                return updated || n;
            });
        });

        // Debounce: only send to server after 100ms of no updates
        if (updateTimeout.current) {
            clearTimeout(updateTimeout.current);
        }

        updateTimeout.current = setTimeout(() => {
            notesToUpdate.forEach(note => {
                socket.emit("update-note", { boardId, note });
            });
        }, 100);
    }, [boardId]);

    const addLine = (line) => {
        setLines((prev) => [...prev, line]);
        socket.emit("add-line", { boardId, line });
    };

    const handleDownload = () => {
        const boardData = {
            id: boardId,
            title,
            notes,
            lines,
            exportedAt: new Date().toISOString()
        };

        const dataStr = JSON.stringify(boardData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);

        const link = document.createElement('a');
        link.href = url;
        link.download = `board-${boardId}-${Date.now()}.json`;
        link.click();

        URL.revokeObjectURL(url);
    };

    const handleUpload = (file) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const boardData = JSON.parse(e.target.result);

                if (boardData.title) setTitle(boardData.title);
                if (boardData.notes) setNotes(boardData.notes);
                if (boardData.lines) setLines(boardData.lines);

                // Emit to server to sync with other clients
                boardData.notes?.forEach(note => {
                    socket.emit("add-note", { boardId, note });
                });

                alert('ボードを復元しました!');
            } catch (error) {
                console.error('Error parsing board data:', error);
                alert('ファイルの読み込みに失敗しました。');
            }
        };
        reader.readAsText(file);
    };

    const handleJumpToNote = (note) => {
        const container = boardContainerRef.current;
        if (container) {
            // Calculate scroll position to center the note
            const noteX = note.x * scale;
            const noteY = note.y * scale;
            const centerX = noteX - (container.clientWidth / 2) + 100;
            const centerY = noteY - (container.clientHeight / 2) + 100;

            container.scrollTo({
                left: Math.max(0, centerX),
                top: Math.max(0, centerY),
                behavior: 'smooth'
            });

            // Highlight effect
            setTimeout(() => {
                const noteElement = document.querySelector(`[data-note-id="${note.id}"]`);
                if (noteElement) {
                    noteElement.style.animation = 'highlight 1s';
                    setTimeout(() => noteElement.style.animation = '', 1000);
                }
            }, 500);
        }
    };

    const handleGroupNotes = (noteIds) => {
        const groupId = `group-${Date.now()}`;

        // Calculate center position from selected notes
        const selectedNotes = notes.filter(n => noteIds.includes(n.id));
        if (selectedNotes.length === 0) return;

        const centerX = selectedNotes.reduce((sum, n) => sum + n.x, 0) / selectedNotes.length;
        const centerY = selectedNotes.reduce((sum, n) => sum + n.y, 0) / selectedNotes.length;

        // Arrange notes in a circle around the center
        const radius = 250;
        const angleStep = (2 * Math.PI) / selectedNotes.length;

        const updatedNotes = selectedNotes.map((note, index) => {
            const angle = angleStep * index;
            const newX = centerX + Math.cos(angle) * radius;
            const newY = centerY + Math.sin(angle) * radius;

            return {
                ...note,
                x: newX,
                y: newY,
                groupId
            };
        });

        setNotes((prev) =>
            prev.map((n) => {
                const updated = updatedNotes.find(un => un.id === n.id);
                return updated || n;
            })
        );

        // Update on server
        updatedNotes.forEach(note => {
            socket.emit("update-note", { boardId, note });
        });

        alert(`${noteIds.length}個の付箋をグループ化しました`);
    };

    const handleUngroupNotes = (noteIds) => {
        setNotes((prev) =>
            prev.map((n) =>
                noteIds.includes(n.id) ? { ...n, groupId: null } : n
            )
        );

        // Update on server
        noteIds.forEach(noteId => {
            const note = notes.find(n => n.id === noteId);
            if (note) {
                socket.emit("update-note", { boardId, note: { ...note, groupId: null } });
            }
        });

        alert(`${noteIds.length}個の付箋のグループ化を解除しました`);
    };

    return (
        <div className={styles.boardContainer} ref={boardContainerRef}>
            <div className={styles.header}>
                <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="ボードタイトルを入力..."
                    className={styles.titleInput}
                />
                <div className={styles.status}>
                    {isConnected ? "🟢 Online" : "🔴 Offline"}
                </div>
            </div>

            <Toolbar
                onAddNote={addNote}
                color={color}
                setColor={setColor}
                scale={scale}
                setScale={setScale}
                onDownload={handleDownload}
                onUpload={handleUpload}
                onToggleCommentPanel={() => setShowCommentPanel(!showCommentPanel)}
            />

            <div className={styles.canvasWrapper}>
                <BoardCanvas
                    notes={notes}
                    lines={lines}
                    onUpdateNote={updateNote}
                    onAddLine={addLine}
                    scale={scale}
                />
            </div>

            {showCommentPanel && (
                <CommentListPanel
                    notes={notes}
                    onJumpToNote={handleJumpToNote}
                    onGroupNotes={handleGroupNotes}
                    onUngroupNotes={handleUngroupNotes}
                    onClose={() => setShowCommentPanel(false)}
                />
            )}
        </div>
    );
}
