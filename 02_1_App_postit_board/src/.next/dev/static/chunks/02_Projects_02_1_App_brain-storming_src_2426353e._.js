(globalThis.TURBOPACK || (globalThis.TURBOPACK = [])).push([typeof document === "object" ? document.currentScript : undefined,
"[project]/02_Projects/02_1_App_brain-storming/src/app/board/[id]/page.js [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>BoardPage
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$navigation$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/node_modules/next/navigation.js [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
;
const SOCKET_SERVER_URL = "http://localhost:3000"; // Ensure this matches your server
const TRASH_AREA = {
    x: 3600,
    y: 3600
};
const TRASH_COLOR = "#e0e0e0";
let socket;
function BoardPage() {
    _s();
    const params = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$navigation$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useParams"])();
    const boardId = params?.id;
    const [notes, setNotes] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])([]);
    const [lines, setLines] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])([]);
    const [color, setColor] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("#ffeb3b"); // Default yellow
    const [isConnected, setIsConnected] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const [scale, setScale] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(1);
    const [title, setTitle] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("");
    const [showCommentPanel, setShowCommentPanel] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const [username, setUsername] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("");
    const [showUserDialog, setShowUserDialog] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const [participants, setParticipants] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])([]);
    const [showParticipantsList, setShowParticipantsList] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const boardContainerRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "BoardPage.useEffect": ()=>{
            if (!boardId) return;
            // Check if user has a saved username
            const savedUsername = localStorage.getItem('brainstorming-username');
            if (savedUsername) {
                setUsername(savedUsername);
            } else {
                setShowUserDialog(true);
            }
            // Initialize Socket.io connection with reconnection options
            socket = io({
                reconnection: true,
                reconnectionDelay: 1000,
                reconnectionDelayMax: 5000,
                reconnectionAttempts: Infinity
            });
            socket.on("connect", {
                "BoardPage.useEffect": ()=>{
                    console.log("Connected to server");
                    setIsConnected(true);
                    socket.emit("join-board", boardId);
                    // Send user info if username is set
                    const currentUsername = localStorage.getItem('brainstorming-username');
                    if (currentUsername) {
                        socket.emit("user-join", {
                            boardId,
                            username: currentUsername
                        });
                    }
                }
            }["BoardPage.useEffect"]);
            socket.on("init-board", {
                "BoardPage.useEffect": (data)=>{
                    setNotes(data.notes || []);
                    setLines(data.lines || []);
                }
            }["BoardPage.useEffect"]);
            socket.on("note-added", {
                "BoardPage.useEffect": (note)=>{
                    setNotes({
                        "BoardPage.useEffect": (prev)=>{
                            // Prevent duplicate - check if note with this ID already exists
                            if (prev.some({
                                "BoardPage.useEffect": (n)=>n.id === note.id
                            }["BoardPage.useEffect"])) {
                                return prev;
                            }
                            return [
                                ...prev,
                                note
                            ];
                        }
                    }["BoardPage.useEffect"]);
                }
            }["BoardPage.useEffect"]);
            socket.on("note-updated", {
                "BoardPage.useEffect": (updatedNote)=>{
                    setNotes({
                        "BoardPage.useEffect": (prev)=>prev.map({
                                "BoardPage.useEffect": (n)=>n.id === updatedNote.id ? updatedNote : n
                            }["BoardPage.useEffect"])
                    }["BoardPage.useEffect"]);
                }
            }["BoardPage.useEffect"]);
            socket.on("note-deleted", {
                "BoardPage.useEffect": (noteId)=>{
                    setNotes({
                        "BoardPage.useEffect": (prev)=>prev.filter({
                                "BoardPage.useEffect": (n)=>n.id !== noteId
                            }["BoardPage.useEffect"])
                    }["BoardPage.useEffect"]);
                }
            }["BoardPage.useEffect"]);
            socket.on("line-added", {
                "BoardPage.useEffect": (line)=>{
                    setLines({
                        "BoardPage.useEffect": (prev)=>[
                                ...prev,
                                line
                            ]
                    }["BoardPage.useEffect"]);
                }
            }["BoardPage.useEffect"]);
            // User events
            socket.on("users-list", {
                "BoardPage.useEffect": (usersList)=>{
                    setParticipants(usersList);
                }
            }["BoardPage.useEffect"]);
            socket.on("user-joined", {
                "BoardPage.useEffect": ({ username: newUsername })=>{
                    console.log(`${newUsername} joined the board`);
                }
            }["BoardPage.useEffect"]);
            socket.on("user-left", {
                "BoardPage.useEffect": ({ username: leftUsername })=>{
                    console.log(`${leftUsername} left the board`);
                }
            }["BoardPage.useEffect"]);
            socket.on("disconnect", {
                "BoardPage.useEffect": ()=>{
                    console.log("Disconnected from server");
                    setIsConnected(false);
                }
            }["BoardPage.useEffect"]);
            return ({
                "BoardPage.useEffect": ()=>{
                    socket.disconnect();
                }
            })["BoardPage.useEffect"];
        }
    }["BoardPage.useEffect"], [
        boardId
    ]);
    // Scroll to center on initial load
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "BoardPage.useEffect": ()=>{
            const container = boardContainerRef.current;
            if (container) {
                // Wait a bit for layout
                setTimeout({
                    "BoardPage.useEffect": ()=>{
                        const scrollX = (4000 - container.clientWidth) / 2;
                        const scrollY = (4000 - container.clientHeight) / 2;
                        container.scrollTo(scrollX, scrollY);
                    }
                }["BoardPage.useEffect"], 100);
            }
        }
    }["BoardPage.useEffect"], []);
    const handleCenter = ()=>{
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
    const handleUserSubmit = (newUsername)=>{
        setUsername(newUsername);
        localStorage.setItem('brainstorming-username', newUsername);
        setShowUserDialog(false);
        // Send user-join event to server
        if (socket && socket.connected) {
            socket.emit("user-join", {
                boardId,
                username: newUsername
            });
        }
    };
    const addNote = ()=>{
        // Generate more unique ID with timestamp + random
        const timestamp = Date.now().toString(36);
        const random = Math.random().toString(36).substr(2, 9);
        // Position new notes near the bottom center of the CURRENT VIEWPORT
        const container = boardContainerRef.current;
        if (!container) return;
        const viewportWidth = container.clientWidth;
        const viewportHeight = container.clientHeight;
        const scrollLeft = container.scrollLeft;
        const scrollTop = container.scrollTop;
        // Calculate center x relative to the board
        const centerX = scrollLeft + viewportWidth / 2 - 100; // Center minus half note width
        // Calculate bottom y relative to the board (near toolbar)
        // Toolbar is at bottom 20px + padding ~50px. Let's place it 200px from bottom.
        const bottomY = scrollTop + viewportHeight - 300;
        const newNote = {
            id: `${timestamp}-${random}`,
            text: "",
            x: centerX + Math.random() * 20 - 10,
            y: bottomY + Math.random() * 20 - 10,
            color: color,
            pinned: false,
            author: username,
            createdAt: Date.now()
        };
        // Optimistic update
        setNotes((prev)=>[
                ...prev,
                newNote
            ]);
        socket.emit("add-note", {
            boardId,
            note: newNote
        });
    };
    const notesRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(notes);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "BoardPage.useEffect": ()=>{
            notesRef.current = notes;
        }
    }["BoardPage.useEffect"], [
        notes
    ]);
    const updateTimeout = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    const updateNote = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useCallback"])({
        "BoardPage.useCallback[updateNote]": (updatedNote)=>{
            const currentNotes = notesRef.current;
            const originalNote = currentNotes.find({
                "BoardPage.useCallback[updateNote].originalNote": (n)=>n.id === updatedNote.id
            }["BoardPage.useCallback[updateNote].originalNote"]);
            let notesToUpdate = [
                updatedNote
            ];
            if (originalNote && updatedNote.groupId) {
                const dx = updatedNote.x - originalNote.x;
                const dy = updatedNote.y - originalNote.y;
                if (dx !== 0 || dy !== 0) {
                    const groupNotes = currentNotes.filter({
                        "BoardPage.useCallback[updateNote].groupNotes": (n)=>n.groupId === updatedNote.groupId && n.id !== updatedNote.id
                    }["BoardPage.useCallback[updateNote].groupNotes"]);
                    const additionalUpdates = groupNotes.map({
                        "BoardPage.useCallback[updateNote].additionalUpdates": (n)=>({
                                ...n,
                                x: n.x + dx,
                                y: n.y + dy
                            })
                    }["BoardPage.useCallback[updateNote].additionalUpdates"]);
                    notesToUpdate = [
                        ...notesToUpdate,
                        ...additionalUpdates
                    ];
                }
            }
            // Logic for restoring from trash (logical deletion recovery)
            if (originalNote && originalNote.groupId === 'trash') {
                const isMoved = updatedNote.x !== originalNote.x || updatedNote.y !== originalNote.y;
                const isColorChanged = updatedNote.color !== TRASH_COLOR;
                if (isMoved || isColorChanged) {
                    // Restore from trash if moved or color changed
                    updatedNote.groupId = null;
                // If it was only moved but color is still gray, keep it gray unless user changed it?
                // Spec says "manually change color AND move". Let's assume ANY action restores it.
                // If color changed, it's already updated in updatedNote.color
                }
            }
            setNotes({
                "BoardPage.useCallback[updateNote]": (prev)=>{
                    return prev.map({
                        "BoardPage.useCallback[updateNote]": (n)=>{
                            const updated = notesToUpdate.find({
                                "BoardPage.useCallback[updateNote].updated": (un)=>un.id === n.id
                            }["BoardPage.useCallback[updateNote].updated"]);
                            return updated || n;
                        }
                    }["BoardPage.useCallback[updateNote]"]);
                }
            }["BoardPage.useCallback[updateNote]"]);
            // Debounce: only send to server after 100ms of no updates
            if (updateTimeout.current) {
                clearTimeout(updateTimeout.current);
            }
            updateTimeout.current = setTimeout({
                "BoardPage.useCallback[updateNote]": ()=>{
                    notesToUpdate.forEach({
                        "BoardPage.useCallback[updateNote]": (note)=>{
                            socket.emit("update-note", {
                                boardId,
                                note
                            });
                        }
                    }["BoardPage.useCallback[updateNote]"]);
                }
            }["BoardPage.useCallback[updateNote]"], 100);
        }
    }["BoardPage.useCallback[updateNote]"], [
        boardId
    ]);
    const addLine = (line)=>{
        setLines((prev)=>[
                ...prev,
                line
            ]);
        socket.emit("add-line", {
            boardId,
            line
        });
    };
    const deleteNote = (noteId)=>{
        // Logical deletion: Move to trash area and change color
        const noteToDelete = notes.find((n)=>n.id === noteId);
        if (!noteToDelete) return;
        const offset = Math.random() * 20 - 10;
        const trashNote = {
            ...noteToDelete,
            color: TRASH_COLOR,
            groupId: 'trash',
            x: TRASH_AREA.x + offset,
            y: TRASH_AREA.y + offset,
            pinned: false // Unpin if pinned
        };
        // Optimistic update
        setNotes((prev)=>prev.map((n)=>n.id === noteId ? trashNote : n));
        socket.emit("update-note", {
            boardId,
            note: trashNote
        });
    };
    const handleDownload = ()=>{
        const boardData = {
            id: boardId,
            title,
            notes,
            lines,
            exportedAt: new Date().toISOString()
        };
        const dataStr = JSON.stringify(boardData, null, 2);
        const dataBlob = new Blob([
            dataStr
        ], {
            type: 'application/json'
        });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `board-${boardId}-${Date.now()}.json`;
        link.click();
        URL.revokeObjectURL(url);
    };
    const handleUpload = (file)=>{
        const reader = new FileReader();
        reader.onload = (e)=>{
            try {
                const boardData = JSON.parse(e.target.result);
                if (boardData.title) setTitle(boardData.title);
                if (boardData.notes) setNotes(boardData.notes);
                if (boardData.lines) setLines(boardData.lines);
                // Emit to server to sync with other clients
                boardData.notes?.forEach((note)=>{
                    socket.emit("add-note", {
                        boardId,
                        note
                    });
                });
                alert('ボードを復元しました!');
            } catch (error) {
                console.error('Error parsing board data:', error);
                alert('ファイルの読み込みに失敗しました。');
            }
        };
        reader.readAsText(file);
    };
    const handleJumpToNote = (note)=>{
        const container = boardContainerRef.current;
        if (container) {
            // Calculate scroll position to center the note
            const noteX = note.x * scale;
            const noteY = note.y * scale;
            const centerX = noteX - container.clientWidth / 2 + 100;
            const centerY = noteY - container.clientHeight / 2 + 100;
            container.scrollTo({
                left: Math.max(0, centerX),
                top: Math.max(0, centerY),
                behavior: 'smooth'
            });
            // Highlight effect
            setTimeout(()=>{
                const noteElement = document.querySelector(`[data-note-id="${note.id}"]`);
                if (noteElement) {
                    noteElement.style.animation = 'highlight 1s';
                    setTimeout(()=>noteElement.style.animation = '', 1000);
                }
            }, 500);
        }
    };
    const handleGroupNotes = (noteIds)=>{
        const groupId = `group-${Date.now()}`;
        // Calculate center position from selected notes
        const selectedNotes = notes.filter((n)=>noteIds.includes(n.id));
        if (selectedNotes.length === 0) return;
        const centerX = selectedNotes.reduce((sum, n)=>sum + n.x, 0) / selectedNotes.length;
        const centerY = selectedNotes.reduce((sum, n)=>sum + n.y, 0) / selectedNotes.length;
        // Arrange notes in a pile (slightly overlapped)
        const updatedNotes = selectedNotes.map((note, index)=>{
            // Offset each note slightly to create a messy pile effect
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
        setNotes((prev)=>prev.map((n)=>{
                const updated = updatedNotes.find((un)=>un.id === n.id);
                return updated || n;
            }));
        // Update on server
        updatedNotes.forEach((note)=>{
            socket.emit("update-note", {
                boardId,
                note
            });
        });
        alert(`${noteIds.length}個の付箋をグループ化しました`);
    };
    const handleUngroupNotes = (noteIds)=>{
        const updatedNotes = notes.filter((n)=>noteIds.includes(n.id)).map((n)=>{
            return {
                ...n,
                groupId: null
            };
        });
        setNotes((prev)=>prev.map((n)=>{
                const updated = updatedNotes.find((un)=>un.id === n.id);
                return updated || n;
            }));
        // Update on server
        updatedNotes.forEach((note)=>{
            socket.emit("update-note", {
                boardId,
                note
            });
        });
        alert(`${noteIds.length}個の付箋のグループ化を解除しました`);
    };
    const [isDraggingBoard, setIsDraggingBoard] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const dragStart = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])({
        x: 0,
        y: 0
    });
    const scrollStart = (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])({
        left: 0,
        top: 0
    });
    const handleMouseDown = (e)=>{
        // Only drag if clicking on the container or canvas directly (not notes)
        // Check if the event target is within a sticky note using data attribute
        const isClickingNote = e.target.closest('[data-sticky-note]');
        if (!isClickingNote) {
            setIsDraggingBoard(true);
            dragStart.current = {
                x: e.clientX,
                y: e.clientY
            };
            const container = boardContainerRef.current;
            scrollStart.current = {
                left: container.scrollLeft,
                top: container.scrollTop
            };
            container.style.cursor = 'grabbing';
        }
    };
    const handleMouseMove = (e)=>{
        if (!isDraggingBoard) return;
        e.preventDefault();
        const container = boardContainerRef.current;
        const dx = e.clientX - dragStart.current.x;
        const dy = e.clientY - dragStart.current.y;
        container.scrollLeft = scrollStart.current.left - dx;
        container.scrollTop = scrollStart.current.top - dy;
    };
    const handleMouseUp = ()=>{
        setIsDraggingBoard(false);
        if (boardContainerRef.current) {
            boardContainerRef.current.style.cursor = 'grab';
        }
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: styles.boardContainer,
        ref: boardContainerRef,
        onMouseDown: handleMouseDown,
        onMouseMove: handleMouseMove,
        onMouseUp: handleMouseUp,
        onMouseLeave: handleMouseUp,
        style: {
            cursor: 'grab'
        },
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: styles.header,
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                        type: "text",
                        value: title,
                        onChange: (e)=>setTitle(e.target.value),
                        placeholder: "ボードタイトルを入力...",
                        className: styles.titleInput
                    }, void 0, false, {
                        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/app/board/[id]/page.js",
                        lineNumber: 458,
                        columnNumber: 17
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: styles.status,
                        children: isConnected ? "🟢 Online" : "🔴 Offline"
                    }, void 0, false, {
                        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/app/board/[id]/page.js",
                        lineNumber: 465,
                        columnNumber: 17
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/app/board/[id]/page.js",
                lineNumber: 457,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(Toolbar, {
                onAddNote: addNote,
                color: color,
                setColor: setColor,
                scale: scale,
                setScale: setScale,
                onDownload: handleDownload,
                onUpload: handleUpload,
                onToggleCommentPanel: ()=>setShowCommentPanel(!showCommentPanel),
                onCenter: handleCenter,
                onToggleParticipants: ()=>setShowParticipantsList(!showParticipantsList)
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/app/board/[id]/page.js",
                lineNumber: 470,
                columnNumber: 13
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: styles.canvasWrapper,
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(BoardCanvas, {
                    notes: notes,
                    lines: lines,
                    onUpdateNote: updateNote,
                    onDeleteNote: deleteNote,
                    onAddLine: addLine,
                    scale: scale
                }, void 0, false, {
                    fileName: "[project]/02_Projects/02_1_App_brain-storming/src/app/board/[id]/page.js",
                    lineNumber: 484,
                    columnNumber: 17
                }, this)
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/app/board/[id]/page.js",
                lineNumber: 483,
                columnNumber: 13
            }, this),
            showCommentPanel && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(CommentListPanel, {
                notes: notes,
                onJumpToNote: handleJumpToNote,
                onGroupNotes: handleGroupNotes,
                onUngroupNotes: handleUngroupNotes,
                onClose: ()=>setShowCommentPanel(false)
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/app/board/[id]/page.js",
                lineNumber: 495,
                columnNumber: 17
            }, this),
            showParticipantsList && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(ParticipantsList, {
                participants: participants,
                onClose: ()=>setShowParticipantsList(false)
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/app/board/[id]/page.js",
                lineNumber: 505,
                columnNumber: 17
            }, this),
            showUserDialog && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(UserDialog, {
                onSubmit: handleUserSubmit
            }, void 0, false, {
                fileName: "[project]/02_Projects/02_1_App_brain-storming/src/app/board/[id]/page.js",
                lineNumber: 512,
                columnNumber: 17
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/02_Projects/02_1_App_brain-storming/src/app/board/[id]/page.js",
        lineNumber: 448,
        columnNumber: 9
    }, this);
}
_s(BoardPage, "SYs7lIZEPTb8lwU587QWqX85ofY=", false, function() {
    return [
        __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$navigation$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useParams"]
    ];
});
_c = BoardPage;
var _c;
__turbopack_context__.k.register(_c, "BoardPage");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/02_Projects/02_1_App_brain-storming/src/node_modules/next/dist/compiled/react/cjs/react-jsx-dev-runtime.development.js [app-client] (ecmascript)", ((__turbopack_context__, module, exports) => {
"use strict";

/**
 * @license React
 * react-jsx-dev-runtime.development.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */ var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$build$2f$polyfills$2f$process$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = /*#__PURE__*/ __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/node_modules/next/dist/build/polyfills/process.js [app-client] (ecmascript)");
"use strict";
"production" !== ("TURBOPACK compile-time value", "development") && function() {
    function getComponentNameFromType(type) {
        if (null == type) return null;
        if ("function" === typeof type) return type.$$typeof === REACT_CLIENT_REFERENCE ? null : type.displayName || type.name || null;
        if ("string" === typeof type) return type;
        switch(type){
            case REACT_FRAGMENT_TYPE:
                return "Fragment";
            case REACT_PROFILER_TYPE:
                return "Profiler";
            case REACT_STRICT_MODE_TYPE:
                return "StrictMode";
            case REACT_SUSPENSE_TYPE:
                return "Suspense";
            case REACT_SUSPENSE_LIST_TYPE:
                return "SuspenseList";
            case REACT_ACTIVITY_TYPE:
                return "Activity";
            case REACT_VIEW_TRANSITION_TYPE:
                return "ViewTransition";
        }
        if ("object" === typeof type) switch("number" === typeof type.tag && console.error("Received an unexpected object in getComponentNameFromType(). This is likely a bug in React. Please file an issue."), type.$$typeof){
            case REACT_PORTAL_TYPE:
                return "Portal";
            case REACT_CONTEXT_TYPE:
                return type.displayName || "Context";
            case REACT_CONSUMER_TYPE:
                return (type._context.displayName || "Context") + ".Consumer";
            case REACT_FORWARD_REF_TYPE:
                var innerType = type.render;
                type = type.displayName;
                type || (type = innerType.displayName || innerType.name || "", type = "" !== type ? "ForwardRef(" + type + ")" : "ForwardRef");
                return type;
            case REACT_MEMO_TYPE:
                return innerType = type.displayName || null, null !== innerType ? innerType : getComponentNameFromType(type.type) || "Memo";
            case REACT_LAZY_TYPE:
                innerType = type._payload;
                type = type._init;
                try {
                    return getComponentNameFromType(type(innerType));
                } catch (x) {}
        }
        return null;
    }
    function testStringCoercion(value) {
        return "" + value;
    }
    function checkKeyStringCoercion(value) {
        try {
            testStringCoercion(value);
            var JSCompiler_inline_result = !1;
        } catch (e) {
            JSCompiler_inline_result = !0;
        }
        if (JSCompiler_inline_result) {
            JSCompiler_inline_result = console;
            var JSCompiler_temp_const = JSCompiler_inline_result.error;
            var JSCompiler_inline_result$jscomp$0 = "function" === typeof Symbol && Symbol.toStringTag && value[Symbol.toStringTag] || value.constructor.name || "Object";
            JSCompiler_temp_const.call(JSCompiler_inline_result, "The provided key is an unsupported type %s. This value must be coerced to a string before using it here.", JSCompiler_inline_result$jscomp$0);
            return testStringCoercion(value);
        }
    }
    function getTaskName(type) {
        if (type === REACT_FRAGMENT_TYPE) return "<>";
        if ("object" === typeof type && null !== type && type.$$typeof === REACT_LAZY_TYPE) return "<...>";
        try {
            var name = getComponentNameFromType(type);
            return name ? "<" + name + ">" : "<...>";
        } catch (x) {
            return "<...>";
        }
    }
    function getOwner() {
        var dispatcher = ReactSharedInternals.A;
        return null === dispatcher ? null : dispatcher.getOwner();
    }
    function UnknownOwner() {
        return Error("react-stack-top-frame");
    }
    function hasValidKey(config) {
        if (hasOwnProperty.call(config, "key")) {
            var getter = Object.getOwnPropertyDescriptor(config, "key").get;
            if (getter && getter.isReactWarning) return !1;
        }
        return void 0 !== config.key;
    }
    function defineKeyPropWarningGetter(props, displayName) {
        function warnAboutAccessingKey() {
            specialPropKeyWarningShown || (specialPropKeyWarningShown = !0, console.error("%s: `key` is not a prop. Trying to access it will result in `undefined` being returned. If you need to access the same value within the child component, you should pass it as a different prop. (https://react.dev/link/special-props)", displayName));
        }
        warnAboutAccessingKey.isReactWarning = !0;
        Object.defineProperty(props, "key", {
            get: warnAboutAccessingKey,
            configurable: !0
        });
    }
    function elementRefGetterWithDeprecationWarning() {
        var componentName = getComponentNameFromType(this.type);
        didWarnAboutElementRef[componentName] || (didWarnAboutElementRef[componentName] = !0, console.error("Accessing element.ref was removed in React 19. ref is now a regular prop. It will be removed from the JSX Element type in a future release."));
        componentName = this.props.ref;
        return void 0 !== componentName ? componentName : null;
    }
    function ReactElement(type, key, props, owner, debugStack, debugTask) {
        var refProp = props.ref;
        type = {
            $$typeof: REACT_ELEMENT_TYPE,
            type: type,
            key: key,
            props: props,
            _owner: owner
        };
        null !== (void 0 !== refProp ? refProp : null) ? Object.defineProperty(type, "ref", {
            enumerable: !1,
            get: elementRefGetterWithDeprecationWarning
        }) : Object.defineProperty(type, "ref", {
            enumerable: !1,
            value: null
        });
        type._store = {};
        Object.defineProperty(type._store, "validated", {
            configurable: !1,
            enumerable: !1,
            writable: !0,
            value: 0
        });
        Object.defineProperty(type, "_debugInfo", {
            configurable: !1,
            enumerable: !1,
            writable: !0,
            value: null
        });
        Object.defineProperty(type, "_debugStack", {
            configurable: !1,
            enumerable: !1,
            writable: !0,
            value: debugStack
        });
        Object.defineProperty(type, "_debugTask", {
            configurable: !1,
            enumerable: !1,
            writable: !0,
            value: debugTask
        });
        Object.freeze && (Object.freeze(type.props), Object.freeze(type));
        return type;
    }
    function jsxDEVImpl(type, config, maybeKey, isStaticChildren, debugStack, debugTask) {
        var children = config.children;
        if (void 0 !== children) if (isStaticChildren) if (isArrayImpl(children)) {
            for(isStaticChildren = 0; isStaticChildren < children.length; isStaticChildren++)validateChildKeys(children[isStaticChildren]);
            Object.freeze && Object.freeze(children);
        } else console.error("React.jsx: Static children should always be an array. You are likely explicitly calling React.jsxs or React.jsxDEV. Use the Babel transform instead.");
        else validateChildKeys(children);
        if (hasOwnProperty.call(config, "key")) {
            children = getComponentNameFromType(type);
            var keys = Object.keys(config).filter(function(k) {
                return "key" !== k;
            });
            isStaticChildren = 0 < keys.length ? "{key: someKey, " + keys.join(": ..., ") + ": ...}" : "{key: someKey}";
            didWarnAboutKeySpread[children + isStaticChildren] || (keys = 0 < keys.length ? "{" + keys.join(": ..., ") + ": ...}" : "{}", console.error('A props object containing a "key" prop is being spread into JSX:\n  let props = %s;\n  <%s {...props} />\nReact keys must be passed directly to JSX without using spread:\n  let props = %s;\n  <%s key={someKey} {...props} />', isStaticChildren, children, keys, children), didWarnAboutKeySpread[children + isStaticChildren] = !0);
        }
        children = null;
        void 0 !== maybeKey && (checkKeyStringCoercion(maybeKey), children = "" + maybeKey);
        hasValidKey(config) && (checkKeyStringCoercion(config.key), children = "" + config.key);
        if ("key" in config) {
            maybeKey = {};
            for(var propName in config)"key" !== propName && (maybeKey[propName] = config[propName]);
        } else maybeKey = config;
        children && defineKeyPropWarningGetter(maybeKey, "function" === typeof type ? type.displayName || type.name || "Unknown" : type);
        return ReactElement(type, children, maybeKey, getOwner(), debugStack, debugTask);
    }
    function validateChildKeys(node) {
        isValidElement(node) ? node._store && (node._store.validated = 1) : "object" === typeof node && null !== node && node.$$typeof === REACT_LAZY_TYPE && ("fulfilled" === node._payload.status ? isValidElement(node._payload.value) && node._payload.value._store && (node._payload.value._store.validated = 1) : node._store && (node._store.validated = 1));
    }
    function isValidElement(object) {
        return "object" === typeof object && null !== object && object.$$typeof === REACT_ELEMENT_TYPE;
    }
    var React = __turbopack_context__.r("[project]/02_Projects/02_1_App_brain-storming/src/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)"), REACT_ELEMENT_TYPE = Symbol.for("react.transitional.element"), REACT_PORTAL_TYPE = Symbol.for("react.portal"), REACT_FRAGMENT_TYPE = Symbol.for("react.fragment"), REACT_STRICT_MODE_TYPE = Symbol.for("react.strict_mode"), REACT_PROFILER_TYPE = Symbol.for("react.profiler"), REACT_CONSUMER_TYPE = Symbol.for("react.consumer"), REACT_CONTEXT_TYPE = Symbol.for("react.context"), REACT_FORWARD_REF_TYPE = Symbol.for("react.forward_ref"), REACT_SUSPENSE_TYPE = Symbol.for("react.suspense"), REACT_SUSPENSE_LIST_TYPE = Symbol.for("react.suspense_list"), REACT_MEMO_TYPE = Symbol.for("react.memo"), REACT_LAZY_TYPE = Symbol.for("react.lazy"), REACT_ACTIVITY_TYPE = Symbol.for("react.activity"), REACT_VIEW_TRANSITION_TYPE = Symbol.for("react.view_transition"), REACT_CLIENT_REFERENCE = Symbol.for("react.client.reference"), ReactSharedInternals = React.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE, hasOwnProperty = Object.prototype.hasOwnProperty, isArrayImpl = Array.isArray, createTask = console.createTask ? console.createTask : function() {
        return null;
    };
    React = {
        react_stack_bottom_frame: function(callStackForError) {
            return callStackForError();
        }
    };
    var specialPropKeyWarningShown;
    var didWarnAboutElementRef = {};
    var unknownOwnerDebugStack = React.react_stack_bottom_frame.bind(React, UnknownOwner)();
    var unknownOwnerDebugTask = createTask(getTaskName(UnknownOwner));
    var didWarnAboutKeySpread = {};
    exports.Fragment = REACT_FRAGMENT_TYPE;
    exports.jsxDEV = function(type, config, maybeKey, isStaticChildren) {
        var trackActualOwner = 1e4 > ReactSharedInternals.recentlyCreatedOwnerStacks++;
        if (trackActualOwner) {
            var previousStackTraceLimit = Error.stackTraceLimit;
            Error.stackTraceLimit = 10;
            var debugStackDEV = Error("react-stack-top-frame");
            Error.stackTraceLimit = previousStackTraceLimit;
        } else debugStackDEV = unknownOwnerDebugStack;
        return jsxDEVImpl(type, config, maybeKey, isStaticChildren, debugStackDEV, trackActualOwner ? createTask(getTaskName(type)) : unknownOwnerDebugTask);
    };
}();
}),
"[project]/02_Projects/02_1_App_brain-storming/src/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)", ((__turbopack_context__, module, exports) => {
"use strict";

var __TURBOPACK__imported__module__$5b$project$5d2f$02_Projects$2f$02_1_App_brain$2d$storming$2f$src$2f$node_modules$2f$next$2f$dist$2f$build$2f$polyfills$2f$process$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = /*#__PURE__*/ __turbopack_context__.i("[project]/02_Projects/02_1_App_brain-storming/src/node_modules/next/dist/build/polyfills/process.js [app-client] (ecmascript)");
'use strict';
if ("TURBOPACK compile-time falsy", 0) //TURBOPACK unreachable
;
else {
    module.exports = __turbopack_context__.r("[project]/02_Projects/02_1_App_brain-storming/src/node_modules/next/dist/compiled/react/cjs/react-jsx-dev-runtime.development.js [app-client] (ecmascript)");
}
}),
"[project]/02_Projects/02_1_App_brain-storming/src/node_modules/next/navigation.js [app-client] (ecmascript)", ((__turbopack_context__, module, exports) => {

module.exports = __turbopack_context__.r("[project]/02_Projects/02_1_App_brain-storming/src/node_modules/next/dist/client/components/navigation.js [app-client] (ecmascript)");
}),
]);

//# sourceMappingURL=02_Projects_02_1_App_brain-storming_src_2426353e._.js.map