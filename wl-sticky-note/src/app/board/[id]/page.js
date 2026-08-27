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

// 開発: localhost / 本番: wlboardsys.internal.wonder-link.com または 172.16.1.203（同一オリジンなら空でOK）
const SOCKET_SERVER_URL = typeof window !== "undefined" ? window.location.origin : "http://localhost:3000";
const TRASH_AREA = { x: 3600, y: 3600 };
const TRASH_COLOR = "#e0e0e0";

export const MIN_SCALE = 0.3;
export const MAX_SCALE = 2.5;

const isGrayNote = (note) => Boolean(note?.gray || note?.is_gray || note?.isGray);

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
    const [hideGrayNotes, setHideGrayNotes] = useState(false);
    const [username, setUsername] = useState("");
    const [showUserDialog, setShowUserDialog] = useState(false);
    const [showNoteDialog, setShowNoteDialog] = useState(false);
    const [participants, setParticipants] = useState([]);

    // 複数選択・パン移動関連ステート
    const [selectedNoteIds, setSelectedNoteIds] = useState([]);
    const [isSpacePressed, setIsSpacePressed] = useState(false);
    const [isDraggingBoard, setIsDraggingBoard] = useState(false);
    const [selectionBox, setSelectionBox] = useState(null);

    const boardContainerRef = useRef(null);
    const canvasOuterRef = useRef(null);
    const nameSaveTimeoutRef = useRef(null);
    const boardIdRef = useRef(boardId);
    boardIdRef.current = boardId;

    const dragStart = useRef({ x: 0, y: 0 });
    const scrollStart = useRef({ left: 0, top: 0 });
    const isBoxSelecting = useRef(false);
    const selectionStartPos = useRef({ x: 0, y: 0 });
    const initialSelectedIds = useRef([]);

    // Spaceキーの押下監視（テキスト入力エリアでのスクロール防止 & 干渉ガード）
    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.code === 'Space') {
                if (e.target.closest('input, textarea, select, [contenteditable="true"]')) {
                    return;
                }
                e.preventDefault();
                setIsSpacePressed(true);
            }
        };

        const handleKeyUp = (e) => {
            if (e.code === 'Space') {
                setIsSpacePressed(false);
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        window.addEventListener('keyup', handleKeyUp);
        return () => {
            window.removeEventListener('keydown', handleKeyDown);
            window.removeEventListener('keyup', handleKeyUp);
        };
    }, []);

    useEffect(() => {
        if (!boardId) return;

        // ユーザー名が保存されているか確認
        const savedUsername = localStorage.getItem('wl-sticky-note-username');
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
            const currentUsername = localStorage.getItem('wl-sticky-note-username');
            if (currentUsername) {
                socket.emit("user-join", { boardId, username: currentUsername });
            }
        });

        socket.on("init-board", (data) => {
            setNotes(data.notes || []);
            setLines(data.lines || []);
            setTitle((data.name !== undefined && data.name !== null) ? String(data.name) : "");
        });

        socket.on("board-name-updated", ({ name }) => {
            setTitle(name != null ? String(name) : "");
        });

        socket.on("note-added", (note) => {
            setNotes((prev) => {
                if (prev.some(n => n.id === note.id)) return prev;
                // AI生成付箋は現在のビューポート中央付近に配置
                let placed = note;
                if (note.author === "AI" && boardContainerRef.current && canvasOuterRef.current) {
                    const container = boardContainerRef.current;
                    const canvasRect = canvasOuterRef.current.getBoundingClientRect();
                    const containerRect = container.getBoundingClientRect();
                    const cx = (containerRect.width / 2 + container.scrollLeft - (canvasRect.left - containerRect.left + container.scrollLeft)) / scale - 100;
                    const cy = (containerRect.height / 2 + container.scrollTop - (canvasRect.top - containerRect.top + container.scrollTop)) / scale - 100;
                    placed = { ...note, x: cx, y: cy };
                    socket.emit("update-note", { boardId, note: placed });
                }
                return [...prev, placed];
            });
        });

        socket.on("note-updated", (updatedNote) => {
            setNotes((prev) =>
                prev.map((n) => (n.id === updatedNote.id ? updatedNote : n))
            );
        });

        socket.on("note-deleted", (noteId) => {
            setNotes((prev) => prev.filter((n) => n.id !== noteId));
            setSelectedNoteIds((prev) => prev.filter(id => id !== noteId));
        });

        socket.on("line-added", (line) => {
            setLines((prev) => [...prev, line]);
        });

        // ボード全削除時のイベント（サーバーからの通知）
        socket.on("board-cleared", () => {
            console.log("Board cleared by server.");
            setNotes([]);
            setLines([]);
            setSelectedNoteIds([]);
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
            socket.off("init-board");
            socket.off("board-name-updated");
            socket.off("note-added");
            socket.off("note-updated");
            socket.off("note-deleted");
            socket.off("line-added");
            socket.off("board-cleared");
            socket.off("users-list");
            socket.off("user-joined");
            socket.off("user-left");
            socket.off("disconnect");
            socket.disconnect();
        };
    }, [boardId, scale]);

    // ボードの絶対中心 (2000, 2000) を画面中央にスクロール合わせする処理
    const scrollToCenter = useCallback((smooth = false) => {
        const container = boardContainerRef.current;
        if (!container) return;

        const targetCenterX = 2000 * scale;
        const targetCenterY = 2000 * scale;

        const scrollX = targetCenterX - container.clientWidth / 2;
        const scrollY = targetCenterY - container.clientHeight / 2;

        container.scrollTo({
            left: Math.max(0, scrollX),
            top: Math.max(0, scrollY),
            behavior: smooth ? 'smooth' : 'auto'
        });
    }, [scale]);

    // 初期ロード時に中央へスクロール
    useEffect(() => {
        setTimeout(() => {
            scrollToCenter(false);
        }, 100);
    }, [scrollToCenter]);

    const handleCenter = () => {
        scrollToCenter(true);
    };

    useEffect(() => {
        const container = boardContainerRef.current;
        if (!container) return;

        const handleWheel = (e) => {
            // テキスト入力エリア・モーダル・スクロール可能エリアでのスクロール時はズームを除外
            if (e.target.closest('textarea, input, select, [data-scrollable="true"]')) {
                return;
            }

            e.preventDefault();

            // deltaY に応じた連続的なスムーズズーム計算（トラックパッド・マウス双方に対応）
            const zoomFactor = Math.exp(-e.deltaY * 0.0015);

            setScale((prevScale) => {
                const newScale = Math.min(Math.max(MIN_SCALE, prevScale * zoomFactor), MAX_SCALE);
                if (Math.abs(newScale - prevScale) < 0.001) return prevScale;

                // マウスカーソルのコンテナ内相対座標
                const rect = container.getBoundingClientRect();
                const mouseX = e.clientX - rect.left;
                const mouseY = e.clientY - rect.top;

                // ズーム前のキャンバス内座標
                const targetX = (container.scrollLeft + mouseX) / prevScale;
                const targetY = (container.scrollTop + mouseY) / prevScale;

                // 新スケール適用後のスクロール位置を計算・適用
                requestAnimationFrame(() => {
                    container.scrollLeft = targetX * newScale - mouseX;
                    container.scrollTop = targetY * newScale - mouseY;
                });

                return newScale;
            });
        };

        container.addEventListener("wheel", handleWheel, { passive: false });
        return () => {
            container.removeEventListener("wheel", handleWheel);
        };
    }, []);

    const handleUserSubmit = (newUsername) => {
        setUsername(newUsername);
        localStorage.setItem('wl-sticky-note-username', newUsername);
        setShowUserDialog(false);

        // ユーザー参加イベントを送信
        if (socket && socket.connected) {
            socket.emit("user-join", { boardId, username: newUsername });
        }
    };

    const addNote = (initialText = "", dueDate = null) => {
        const timestamp = Date.now().toString(36);
        const random = Math.random().toString(36).substr(2, 9);

        const container = boardContainerRef.current;
        const canvasOuter = canvasOuterRef.current;
        if (!container || !canvasOuter) return;

        const containerRect = container.getBoundingClientRect();
        const canvasRect = canvasOuter.getBoundingClientRect();

        const screenCenterX = containerRect.width / 2;
        const screenCenterY = containerRect.height / 2;

        const noteX = (screenCenterX - (canvasRect.left - containerRect.left)) / scale - 100 + (Math.random() * 20 - 10);
        const noteY = (screenCenterY - (canvasRect.top - containerRect.top)) / scale - 100 + (Math.random() * 20 - 10);

        const newNote = {
            id: `${timestamp}-${random}`,
            text: initialText,
            x: noteX,
            y: noteY,
            color: color,
            dueDate: dueDate || null,
            pinned: false,
            author: username,
            createdAt: Date.now()
        };
        setNotes((prev) => [...prev, newNote]);
        socket.emit("add-note", { boardId, note: newNote });
    };

    const handleNoteSubmit = (text, dueDate) => {
        addNote(text, dueDate);
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

    // 複数選択された付箋の一括移動ハンドラー（ピン留め除外・通信スロットル制御）
    const handleMoveSelectedNotes = useCallback((draggedNoteId, dx, dy) => {
        const currentNotes = notesRef.current;
        const isTargetSelected = selectedNoteIds.includes(draggedNoteId);
        const moveIds = isTargetSelected ? selectedNoteIds : [draggedNoteId];

        const notesToUpdate = currentNotes
            .filter(n => moveIds.includes(n.id) && !n.pinned)
            .map(n => ({
                ...n,
                x: n.x + dx,
                y: n.y + dy
            }));

        if (notesToUpdate.length === 0) return;

        setNotes((prev) => prev.map((n) => {
            const updated = notesToUpdate.find(un => un.id === n.id);
            return updated || n;
        }));

        if (updateTimeout.current) clearTimeout(updateTimeout.current);
        updateTimeout.current = setTimeout(() => {
            notesToUpdate.forEach(note => {
                socket.emit("update-note", { boardId, note });
            });
        }, 100);
    }, [boardId, selectedNoteIds]);

    const handleSelectNote = useCallback((noteId, isShift) => {
        setSelectedNoteIds((prev) => {
            if (isShift) {
                return prev.includes(noteId)
                    ? prev.filter(id => id !== noteId)
                    : [...prev, noteId];
            } else {
                return prev.includes(noteId) ? prev : [noteId];
            }
        });
    }, []);

    const addLine = (line) => {
        setLines((prev) => [...prev, line]);
        socket.emit("add-line", { boardId, line });
    };

    const deleteNote = (noteId) => {
        // ボードから付箋を削除（右下への移動ではなく削除）
        setNotes((prev) => prev.filter((n) => n.id !== noteId));
        setSelectedNoteIds((prev) => prev.filter(id => id !== noteId));
        socket.emit("delete-note", { boardId, noteId });
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
        if (isGrayNote(note) && hideGrayNotes) {
            setHideGrayNotes(false);
        }
        setSelectedNoteIds([note.id]);
        const container = boardContainerRef.current;
        if (container) {
            const isLarge = note.ratioW && note.ratioW >= 0.2;
            const noteW = isLarge ? 320 : 200;
            const noteH = isLarge ? 320 : 200;

            // 最大拡大率に設定
            const targetScale = MAX_SCALE;
            setScale(targetScale);

            // 付箋の真の中心（キャンバスの100%座標系）
            const noteCenterX = note.x + noteW / 2;
            const noteCenterY = note.y + noteH / 2;

            // 最大拡大後の中心位置
            const scaledCenterX = noteCenterX * targetScale;
            const scaledCenterY = noteCenterY * targetScale;

            // 付箋を中央に表示するためのスクロール位置を計算
            const targetLeft = scaledCenterX - container.clientWidth / 2;
            const targetTop = scaledCenterY - container.clientHeight / 2;

            requestAnimationFrame(() => {
                container.scrollTo({
                    left: Math.max(0, targetLeft),
                    top: Math.max(0, targetTop),
                    behavior: 'smooth'
                });
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

    // ボード全削除処理
    const handleClearAllNotes = async () => {
        if (!boardId) return;
        const confirmed = window.confirm("本当にこのボード上のすべての付箋と線を削除しますか？この操作は取り消せません。");
        if (!confirmed) return;

        try {
            // REST API経由でサーバーに削除を依頼
            const response = await fetch(`/api/boards/${boardId}/clear`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
            });

            const data = await response.json();
            if (response.ok && data.success) {
                console.log(data.message);
                // 念のためローカル状態も即時クリア
                setNotes([]);
                setLines([]);
                setSelectedNoteIds([]);
            } else {
                console.error('Failed to clear board:', data.error || response.statusText);
                alert('ボードのクリアに失敗しました。');
            }
        } catch (error) {
            console.error('Error clearing board:', error);
            alert('ボードのクリア中にエラーが発生しました。');
        }
    };

    const getCanvasCoords = (e) => {
        const canvasOuter = canvasOuterRef.current;
        if (!canvasOuter) return { x: 0, y: 0 };
        const rect = canvasOuter.getBoundingClientRect();
        const x = (e.clientX - rect.left) / scale;
        const y = (e.clientY - rect.top) / scale;
        return { x, y };
    };

    const handleMouseDown = (e) => {
        // コンテナまたはキャンバスを直接クリックした場合のみドラッグ（付箋以外）
        // data属性を使って付箋内かどうか判定
        const isClickingNote = e.target.closest('[data-sticky-note]');

        // 1. パン移動開始: 中ボタン(button===1) または Spaceキー押下(button===0 && isSpacePressed)
        if (e.button === 1 || (e.button === 0 && isSpacePressed)) {
            e.preventDefault();
            setIsDraggingBoard(true);
            dragStart.current = { x: e.clientX, y: e.clientY };
            const container = boardContainerRef.current;
            scrollStart.current = { left: container.scrollLeft, top: container.scrollTop };
            container.style.cursor = 'grabbing';
            return;
        }

        // 2. 範囲選択開始: 付箋以外をクリック & 通常左ボタン(button===0) & !isSpacePressed
        if (!isClickingNote && e.button === 0) {
            const coords = getCanvasCoords(e);
            isBoxSelecting.current = true;
            selectionStartPos.current = coords;
            initialSelectedIds.current = e.shiftKey ? [...selectedNoteIds] : [];

            setSelectionBox({
                startX: coords.x,
                startY: coords.y,
                currentX: coords.x,
                currentY: coords.y,
                isShift: e.shiftKey
            });
        }
    };

    const handleMouseMove = (e) => {
        if (isDraggingBoard) {
            e.preventDefault();
            const container = boardContainerRef.current;
            const dx = e.clientX - dragStart.current.x;
            const dy = e.clientY - dragStart.current.y;
            container.scrollLeft = scrollStart.current.left - dx;
            container.scrollTop = scrollStart.current.top - dy;
            return;
        }

        if (isBoxSelecting.current) {
            e.preventDefault();
            const coords = getCanvasCoords(e);
            const startX = selectionStartPos.current.x;
            const startY = selectionStartPos.current.y;
            const currentX = coords.x;
            const currentY = coords.y;

            setSelectionBox(prev => prev ? ({ ...prev, currentX, currentY }) : null);

            const left = Math.min(startX, currentX);
            const top = Math.min(startY, currentY);
            const right = Math.max(startX, currentX);
            const bottom = Math.max(startY, currentY);

            const visibleList = hideGrayNotes ? notes.filter(n => !isGrayNote(n)) : notes;
            const intersectedIds = visibleList.filter(note => {
                const isLarge = note.ratioW && note.ratioW >= 0.2;
                const noteW = isLarge ? 320 : 200;
                const noteH = isLarge ? 320 : 200;
                const noteLeft = note.x;
                const noteTop = note.y;
                const noteRight = note.x + noteW;
                const noteBottom = note.y + noteH;

                return !(noteRight < left || noteLeft > right || noteBottom < top || noteTop > bottom);
            }).map(n => n.id);

            if (selectionBox?.isShift) {
                const base = initialSelectedIds.current;
                const combined = Array.from(new Set([...base, ...intersectedIds]));
                setSelectedNoteIds(combined);
            } else {
                setSelectedNoteIds(intersectedIds);
            }
        }
    };

    const handleMouseUp = () => {
        if (isDraggingBoard) {
            setIsDraggingBoard(false);
            if (boardContainerRef.current) {
                boardContainerRef.current.style.cursor = isSpacePressed ? 'grab' : 'default';
            }
        }

        if (isBoxSelecting.current) {
            if (selectionBox) {
                const dx = Math.abs(selectionBox.currentX - selectionBox.startX);
                const dy = Math.abs(selectionBox.currentY - selectionBox.startY);
                if (dx < 5 && dy < 5 && !selectionBox.isShift) {
                    setSelectedNoteIds([]);
                }
            }
            isBoxSelecting.current = false;
            setSelectionBox(null);
        }
    };

    const visibleNotes = hideGrayNotes ? notes.filter(n => !isGrayNote(n)) : notes;

    return (
        <div
            className={styles.boardContainer}
            ref={boardContainerRef}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            style={{ cursor: isSpacePressed ? 'grab' : 'default' }}
        >
            <div className={styles.header}>
                <input
                    type="text"
                    value={title}
                    onChange={(e) => {
                        const v = e.target.value;
                        setTitle(v);
                        if (nameSaveTimeoutRef.current) clearTimeout(nameSaveTimeoutRef.current);
                        nameSaveTimeoutRef.current = setTimeout(() => {
                            if (socket && boardIdRef.current) {
                                socket.emit("board-set-name", { boardId: boardIdRef.current, name: v });
                            }
                        }, 600);
                    }}
                    onBlur={() => {
                        if (nameSaveTimeoutRef.current) {
                            clearTimeout(nameSaveTimeoutRef.current);
                            nameSaveTimeoutRef.current = null;
                        }
                        if (socket && boardIdRef.current) {
                            socket.emit("board-set-name", { boardId: boardIdRef.current, name: title });
                        }
                    }}
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
                onClearAllNotes={handleClearAllNotes}
                hideGrayNotes={hideGrayNotes}
                onToggleHideGrayNotes={() => setHideGrayNotes(!hideGrayNotes)}
            />

            <div className={styles.canvasWrapper}>
                <BoardCanvas
                    canvasOuterRef={canvasOuterRef}
                    notes={visibleNotes}
                    lines={lines}
                    onUpdateNote={updateNote}
                    onDeleteNote={deleteNote}
                    onAddLine={addLine}
                    scale={scale}
                    selectedNoteIds={selectedNoteIds}
                    onSelectNote={handleSelectNote}
                    onMoveSelectedNotes={handleMoveSelectedNotes}
                    selectionBox={selectionBox}
                />
            </div>

            {showCommentPanel && (
                <CommentListPanel
                    notes={visibleNotes}
                    onJumpToNote={handleJumpToNote}
                    onGroupNotes={handleGroupNotes}
                    onUngroupNotes={handleUngroupNotes}
                    onClose={() => setShowCommentPanel(false)}
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