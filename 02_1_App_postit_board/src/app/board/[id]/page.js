"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useParams } from "next/navigation";
import io from "socket.io-client";
import styles from "./page.module.css";
import BoardCanvas from "@/components/BoardCanvas";
import Toolbar from "@/components/Toolbar";
import CommentListPanel from "@/components/CommentListPanel";
import UserDialog from "@/components/UserDialog";
import NoteInputDialog from "@/components/NoteInputDialog";
import ParticipantsList from "@/components/ParticipantsList";

const SOCKET_SERVER_URL = "http://localhost:3000"; // サーバーのURLに合わせて変更してください
const TRASH_AREA = { x: 3600, y: 3600 };
const TRASH_COLOR = "#e0e0e0";

let socket;

export default function BoardPage() {
    const params = useParams();
    const boardId = params?.id;
    const [notes, setNotes] = useState([]);
    const [lines, setLines] = useState([]);
    const [color, setColor] = useState("#ffeb3b"); // デフォルト色（黄色）
    const [isConnected, setIsConnected] = useState(false);
    const [scale, setScale] = useState(1);
    const [title, setTitle] = useState("");
    const [showCommentPanel, setShowCommentPanel] = useState(false);
    const [username, setUsername] = useState("");
    const [showUserDialog, setShowUserDialog] = useState(false);
    const [showNoteDialog, setShowNoteDialog] = useState(false);
    const [participants, setParticipants] = useState([]);
    const [showParticipantsList, setShowParticipantsList] = useState(false);
    const boardContainerRef = useRef(null);

    useEffect(() => {
        if (!boardId) return;

        // ユーザー名が保存されているか確認
        const savedUsername = localStorage.getItem('brainstorming-username');
        if (savedUsername) {
            setUsername(savedUsername);
        } else {
            setShowUserDialog(true);
        }

        // Socket.io接続の初期化（再接続オプション付き）
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

            // ユーザー名が設定されていれば送信
            const currentUsername = localStorage.getItem('brainstorming-username');
            if (currentUsername) {
                socket.emit("user-join", { boardId, username: currentUsername });
            }
        });

        socket.on("init-board", (data) => {
            setNotes(data.notes || []);
            setLines(data.lines || []);
        });

        socket.on("note-added", (note) => {
            setNotes((prev) => {
                // 重複防止 - 既に同じIDの付箋があるかチェック
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

        socket.on("note-deleted", (noteId) => {
            setNotes((prev) => prev.filter((n) => n.id !== noteId));
        });

        socket.on("line-added", (line) => {
            setLines((prev) => [...prev, line]);
        });

        // ユーザーイベント
        socket.on("users-list", (usersList) => {
            setParticipants(usersList);
        });

        socket.on("user-joined", ({ username: newUsername }) => {
            console.log(`${newUsername} joined the board`);
        });

        socket.on("user-left", ({ username: leftUsername }) => {
            console.log(`${leftUsername} left the board`);
        });

        socket.on("disconnect", () => {
            console.log("Disconnected from server");
            setIsConnected(false);
        });

        return () => {
            socket.disconnect();
        };
    }, [boardId]);

    // 初期ロード時に中央へスクロール
    useEffect(() => {
        const container = boardContainerRef.current;
        if (container) {
            // レイアウト安定待ち
            setTimeout(() => {
                const scrollX = (4000 - container.clientWidth) / 2;
                const scrollY = (4000 - container.clientHeight) / 2;
                container.scrollTo(scrollX, scrollY);
            }, 100);
        }
    }, []);

    const handleCenter = () => {
        const container = boardContainerRef.current;
        if (container) {
            const scrollX = (4000 - container.clientWidth) / 2;
            const scrollY = (4000 - container.clientHeight) / 2;
            container.scrollTo({
                left: scrollX,
                top: scrollY,
                behavior: 'smooth'
            });
        }
    };

    const handleUserSubmit = (newUsername) => {
        setUsername(newUsername);
        localStorage.setItem('brainstorming-username', newUsername);
        setShowUserDialog(false);

        // ユーザー参加イベントを送信
        if (socket && socket.connected) {
            socket.emit("user-join", { boardId, username: newUsername });
        }
    };

    const addNote = (initialText = "") => {
        // タイムスタンプとランダム値でユニークIDを生成
        const timestamp = Date.now().toString(36);
        const random = Math.random().toString(36).substr(2, 9);

        // 現在のビューポートの下部中央付近に新しい付箋を配置
        const container = boardContainerRef.current;
        if (!container) return;

        const viewportWidth = container.clientWidth;
        const viewportHeight = container.clientHeight;
        const scrollLeft = container.scrollLeft;
        const scrollTop = container.scrollTop;

        // ボード相対の中央X座標
        const centerX = scrollLeft + (viewportWidth / 2) - 100; // 中央から付箋幅の半分を引く

        // ボード相対の下部Y座標（ツールバー付近）
        // ツールバーは下部20px + パディング約50px。下から300pxの位置に配置。
        const bottomY = scrollTop + viewportHeight - 300;

        const newNote = {
            id: `${timestamp}-${random}`,
            text: initialText,
            x: centerX + Math.random() * 20 - 10,
            y: bottomY + Math.random() * 20 - 10,
            color: color,
            pinned: false,
            author: username,
            createdAt: Date.now()
        };
        // 楽観的更新
        setNotes((prev) => [...prev, newNote]);
        socket.emit("add-note", { boardId, note: newNote });
    };

    const handleNoteSubmit = (text) => {
        addNote(text);
        setShowNoteDialog(false);
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

        // ゴミ箱からの復元ロジック（論理削除からの回復）
        if (originalNote && originalNote.groupId === 'trash') {
            const isMoved = updatedNote.x !== originalNote.x || updatedNote.y !== originalNote.y;
            const isColorChanged = updatedNote.color !== TRASH_COLOR;

            if (isMoved || isColorChanged) {
                // 移動または色変更でゴミ箱から復元
                updatedNote.groupId = null;
                // 色が変更された場合は updatedNote.color に反映済み
            }
        }

        setNotes((prev) => {
            return prev.map((n) => {
                const updated = notesToUpdate.find(un => un.id === n.id);
                return updated || n;
            });
        });

        // デバウンス: 100ms更新がない場合のみサーバーに送信
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

    const deleteNote = (noteId) => {
        // 論理削除: ゴミ箱エリアに移動し色を変更
        const noteToDelete = notes.find(n => n.id === noteId);
        if (!noteToDelete) return;

        const offset = Math.random() * 20 - 10;
        const trashNote = {
            ...noteToDelete,
            color: TRASH_COLOR,
            groupId: 'trash',
            x: TRASH_AREA.x + offset,
            y: TRASH_AREA.y + offset,
            pinned: false // ピン留め解除
        };

        // 楽観的更新
        setNotes((prev) => prev.map(n => n.id === noteId ? trashNote : n));
        socket.emit("update-note", { boardId, note: trashNote });
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

                // サーバーに送信して他クライアントと同期
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
            // 付箋を中央に表示するためのスクロール位置を計算
            const noteX = note.x * scale;
            const noteY = note.y * scale;
            const centerX = noteX - (container.clientWidth / 2) + 100;
            const centerY = noteY - (container.clientHeight / 2) + 100;

            container.scrollTo({
                left: Math.max(0, centerX),
                top: Math.max(0, centerY),
                behavior: 'smooth'
            });

            // ハイライト効果
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

        // 選択された付箋の中心位置を計算
        const selectedNotes = notes.filter(n => noteIds.includes(n.id));
        if (selectedNotes.length === 0) return;

        const centerX = selectedNotes.reduce((sum, n) => sum + n.x, 0) / selectedNotes.length;
        const centerY = selectedNotes.reduce((sum, n) => sum + n.y, 0) / selectedNotes.length;

        // 山積みに配置（少しずらす）
        const updatedNotes = selectedNotes.map((note, index) => {
            // 雑多な感じを出すために少しオフセット
            const offset = index * 10;
            const totalOffset = (selectedNotes.length - 1) * 10 / 2;

            const newX = centerX + offset - totalOffset;
            const newY = centerY + offset - totalOffset;

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

        // サーバー更新
        updatedNotes.forEach(note => {
            socket.emit("update-note", { boardId, note });
        });

        alert(`${noteIds.length}個の付箋をグループ化しました`);
    };

    const handleUngroupNotes = (noteIds) => {
        const updatedNotes = notes
            .filter(n => noteIds.includes(n.id))
            .map(n => {
                return {
                    ...n,
                    groupId: null,
                };
            });

        setNotes((prev) =>
            prev.map((n) => {
                const updated = updatedNotes.find(un => un.id === n.id);
                return updated || n;
            })
        );

        // サーバー更新
        updatedNotes.forEach(note => {
            socket.emit("update-note", { boardId, note });
        });

        alert(`${noteIds.length}個の付箋のグループ化を解除しました`);
    };

    const [isDraggingBoard, setIsDraggingBoard] = useState(false);
    const dragStart = useRef({ x: 0, y: 0 });
    const scrollStart = useRef({ left: 0, top: 0 });

    const handleMouseDown = (e) => {
        // コンテナまたはキャンバスを直接クリックした場合のみドラッグ（付箋以外）
        // data属性を使って付箋内かどうか判定
        const isClickingNote = e.target.closest('[data-sticky-note]');

        if (!isClickingNote) {
            setIsDraggingBoard(true);
            dragStart.current = { x: e.clientX, y: e.clientY };
            const container = boardContainerRef.current;
            scrollStart.current = { left: container.scrollLeft, top: container.scrollTop };
            container.style.cursor = 'grabbing';
        }
    };

    const handleMouseMove = (e) => {
        if (!isDraggingBoard) return;
        e.preventDefault();
        const container = boardContainerRef.current;
        const dx = e.clientX - dragStart.current.x;
        const dy = e.clientY - dragStart.current.y;
        container.scrollLeft = scrollStart.current.left - dx;
        container.scrollTop = scrollStart.current.top - dy;
    };

    const handleMouseUp = () => {
        setIsDraggingBoard(false);
        if (boardContainerRef.current) {
            boardContainerRef.current.style.cursor = 'grab';
        }
    };

    return (
        <div
            className={styles.boardContainer}
            ref={boardContainerRef}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            style={{ cursor: 'grab' }}
        >
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
                onAddNote={() => setShowNoteDialog(true)}
                color={color}
                setColor={setColor}
                scale={scale}
                setScale={setScale}
                onDownload={handleDownload}
                onUpload={handleUpload}
                onToggleCommentPanel={() => setShowCommentPanel(!showCommentPanel)}
                onCenter={handleCenter}
                onToggleParticipants={() => setShowParticipantsList(!showParticipantsList)}
            />

            <div className={styles.canvasWrapper}>
                <BoardCanvas
                    notes={notes}
                    lines={lines}
                    onUpdateNote={updateNote}
                    onDeleteNote={deleteNote}
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

            {showParticipantsList && (
                <ParticipantsList
                    participants={participants}
                    onClose={() => setShowParticipantsList(false)}
                />
            )}

            {showUserDialog && (
                <UserDialog onSubmit={handleUserSubmit} />
            )}

            {showNoteDialog && (
                <NoteInputDialog
                    onSubmit={handleNoteSubmit}
                    onCancel={() => setShowNoteDialog(false)}
                />
            )}
        </div>
    );
}
