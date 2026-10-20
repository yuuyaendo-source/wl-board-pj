// サーバー設定
// Next.js + Express + Socket.IO を組み合わせたWebアプリケーションサーバー
// 役割: フロントエンドの配信、Socket.IOによるリアルタイム通信、APIエンドポイントの提供

require('dotenv').config(); // PM2 起動時も .env を読み込む（AI_BOARD_URL, AI_BOARD_INSECURE_SSL 等）

const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const next = require('next');
const fs = require('fs');
const fsPromises = fs.promises;
const path = require('path');
const { Agent, fetch: undiciFetch } = require('undici');

// AI-Board 連携先（本番: .env に AI_BOARD_URL を設定。例: http://wlboardsys.local）
const AI_BOARD_BASE = (process.env.AI_BOARD_URL || 'http://127.0.0.1:5000').replace(/\/$/, '');
// Board System API（付箋削除連携: 付箋ボードで削除したら Task/Personal からも削除）
const BOARD_SYSTEM_API_BASE = (process.env.BOARD_SYSTEM_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
// 付箋追加時に AI-Board へ通知するボードID（カンマ区切り。本番連携先: wl）
const AI_BOARD_LINK_BOARD_IDS = (process.env.AI_BOARD_LINK_BOARD_IDS || 'wl').split(',').map(s => s.trim()).filter(Boolean);
// 不適切な付箋内容を検知するキーワード（カンマ区切り。空ならチェックしない。環境変数 INAPPROPRIATE_KEYWORDS で上書き可）
const INAPPROPRIATE_KEYWORDS = (process.env.INAPPROPRIATE_KEYWORDS || '')
    .split(',')
    .map(s => s.trim().toLowerCase())
    .filter(Boolean);

function isInappropriateText(text) {
    if (!text || typeof text !== 'string') return false;
    if (INAPPROPRIATE_KEYWORDS.length === 0) return false;
    const lower = text.toLowerCase();
    return INAPPROPRIATE_KEYWORDS.some(kw => lower.includes(kw));
}

// TLS 検証の局所化設定（undici.Agent を使用してグローバル無効化を廃止）
const insecureDispatcher = new Agent({ connect: { rejectUnauthorized: false } });

function isInternalServiceUrl(url) {
    if (!url) return false;
    return (AI_BOARD_BASE && url.startsWith(AI_BOARD_BASE)) ||
        (BOARD_SYSTEM_API_BASE && url.startsWith(BOARD_SYSTEM_API_BASE));
}

function safeFetch(url, options = {}) {
    const fetchOptions = { ...options };
    if (isInternalServiceUrl(url)) {
        fetchOptions.dispatcher = insecureDispatcher;
    }
    return undiciFetch(url, fetchOptions);
}

// 開発環境かどうかの判定
const dev = process.env.NODE_ENV !== 'production';
const app = next({ dev });
const handle = app.getRequestHandler();

// ポート設定
const port = process.env.PORT || 3000;
// データ保存用ディレクトリ（Docker では /app/data をボリュームマウントして永続化する）
const DATA_DIR = process.env.DATA_DIR || __dirname;
// DATA_DIR が存在しない場合は作成
if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
}
const DATA_FILE = path.join(DATA_DIR, 'boards.json');

app.prepare().then(() => {
    const server = express();
    const httpServer = http.createServer(server);
    const io = new Server(httpServer);

    // リクエストボディのサイズ制限を緩和（画像データ受信のため）
    server.use(express.json({ limit: '50mb' }));
    server.use(express.urlencoded({ extended: true, limit: '50mb' }));

    // CORS設定（Python側からのリクエストを許可）
    server.use((req, res, next) => {
        res.header('Access-Control-Allow-Origin', '*');
        res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS');
        res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
        if (req.method === 'OPTIONS') {
            return res.sendStatus(200);
        }
        next();
    });

    // ボードデータの読み込み（なければ空で初期化）
    // null prototype prevents special property names (for example __proto__) from
    // resolving to inherited object properties when a boardId is used as a key.
    let boards = Object.create(null);
    if (fs.existsSync(DATA_FILE)) {
        try {
            const loadedBoards = JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
            if (loadedBoards && typeof loadedBoards === 'object' && !Array.isArray(loadedBoards)) {
                boards = Object.assign(Object.create(null), loadedBoards);
            }
            // 既存ボードに name が無い場合は空文字を補完（ボード名保存対応）
            for (const id of Object.keys(boards)) {
                if (boards[id].name === undefined) boards[id].name = '';
            }
        } catch (e) {
            console.error('Error loading boards:', e);
        }
    }

    // アトミック保存および排他制御
    // 頻繁なディスク書き込みや高頻度リクエストによる競合を防ぐため isSaving フラグでロック制御
    let isSaving = false;
    let needsResave = false;
    let saveTimeout = null;

    const flushBoardsToDiskAsync = async () => {
        if (isSaving) {
            // 保存中に更新が入った場合は、完了後に必ず最新状態を保存する。
            needsResave = true;
            return;
        }
        isSaving = true;
        needsResave = false;
        const dataStr = JSON.stringify(boards, null, 2);
        const tempFile = `${DATA_FILE}.tmp`;
        try {
            await fsPromises.writeFile(tempFile, dataStr, 'utf8');
            await fsPromises.rename(tempFile, DATA_FILE);
            console.log(`✅ Boards saved to disk (${Buffer.byteLength(dataStr)} bytes)`);
        } catch (err) {
            console.error('❌ Failed to save boards.json:', err.message);
            try { await fsPromises.unlink(tempFile); } catch (e) { } // 失敗時は一時ファイルを確実に消去
        } finally {
            isSaving = false;
            if (needsResave) {
                saveBoards();
            }
        }
    };

    const saveBoards = () => {
        if (saveTimeout) clearTimeout(saveTimeout);
        saveTimeout = setTimeout(() => flushBoardsToDiskAsync(), 500);
    };

    // シャットダウン制御（非同期書き込み完了待機付き＆同期アトミック保存）
    const handleShutdown = async (signal) => {
        console.log(`Received ${signal}. Closing connections and flushing data...`);
        if (saveTimeout) clearTimeout(saveTimeout);

        // 実行中の非同期保存があれば完了するまで待機（競合破綻を防止）
        while (isSaving) {
            await new Promise((resolve) => setTimeout(resolve, 50));
        }

        const exitProcess = () => {
            const tempFile = `${DATA_FILE}.tmp`;
            try {
                const dataStr = JSON.stringify(boards, null, 2);
                fs.writeFileSync(tempFile, dataStr, 'utf8');
                fs.renameSync(tempFile, DATA_FILE);
                console.log(`✅ Graceful shutdown save completed (${Buffer.byteLength(dataStr)} bytes)`);
            } catch (err) {
                console.error('Shutdown save error:', err);
                try { fs.unlinkSync(tempFile); } catch (e) { }
            }
            process.exit(0);
        };

        if (io) io.close();
        if (httpServer) {
            httpServer.close(() => exitProcess());
        } else {
            exitProcess();
        }
    };

    process.on('SIGINT', () => handleShutdown('SIGINT'));
    process.on('SIGTERM', () => handleShutdown('SIGTERM'));

    // ボードごとのユーザー管理
    const boardUsers = Object.create(null); // { boardId: { socketId: { username, joinedAt } } }

    io.on('connection', (socket) => {
        console.log('Client connected:', socket.id);

        // ボードに参加
        socket.on('join-board', (boardId) => {
            socket.join(boardId);
            console.log(`Socket ${socket.id} joined board ${boardId}`);

            if (!boards[boardId]) {
                boards[boardId] = { notes: [], name: '' };
                saveBoards();
            }

            socket.emit('init-board', boards[boardId]);
        });

        // ボード名の変更（保存して参加者に配信）
        socket.on('board-set-name', ({ boardId, name }) => {
            if (!boards[boardId]) return;
            const trimmed = (name || '').toString().trim().slice(0, 200);
            boards[boardId].name = trimmed;
            saveBoards();
            io.to(boardId).emit('board-name-updated', { name: trimmed });
        });

        // ユーザー参加通知
        socket.on('user-join', ({ boardId, username }) => {
            console.log(`User ${username} (${socket.id}) joined board ${boardId}`);

            if (!boardUsers[boardId]) {
                boardUsers[boardId] = Object.create(null);
            }

            boardUsers[boardId][socket.id] = {
                socketId: socket.id,
                username,
                joinedAt: Date.now()
            };

            socket.to(boardId).emit('user-joined', {
                socketId: socket.id,
                username
            });
        });

        // 付箋追加
        socket.on('add-note', ({ boardId, note }) => {
            if (boards[boardId]) {
                if (isInappropriateText(note.text)) {
                    console.log('Add-note rejected: inappropriate content');
                    return;
                }
                boards[boardId].notes.push(note);
                io.to(boardId).emit('note-added', note);
                saveBoards();

                // 連携ボード（例: wl）で追加された付箋を AI-Board に通知（Web で追加→AI表示・AIコメント）
                if (AI_BOARD_LINK_BOARD_IDS.includes(boardId) && note.author && note.author !== 'Real Cam') {
                    try {
                        safeFetch(`${AI_BOARD_BASE}/api/receive_note`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                id: note.id,
                                text: note.text || '',
                                author: note.author || 'Unknown'
                            })
                        }).catch(err => console.error('Failed to notify AI-Board (add-note):', err.message));
                    } catch (e) {
                        console.error('Error notifying AI-Board (add-note):', e);
                    }
                }
            }
        });

        // 付箋更新
        socket.on('update-note', ({ boardId, note }) => {
            if (boards[boardId]) {
                const index = boards[boardId].notes.findIndex((n) => n.id === note.id);
                if (index !== -1) {
                    if (isInappropriateText(note.text)) {
                        boards[boardId].notes = boards[boardId].notes.filter((n) => n.id !== note.id);
                        io.to(boardId).emit('note-deleted', note.id);
                        saveBoards();
                        const url = `${BOARD_SYSTEM_API_BASE}/sticky_notes/by_postit?board_id=${encodeURIComponent(boardId)}&note_id=${encodeURIComponent(String(note.id))}`;
                        safeFetch(url, { method: 'DELETE' }).catch((err) => console.error('Board System delete by_postit:', err.message));
                        return;
                    }
                    boards[boardId].notes[index] = note;
                    socket.to(boardId).emit('note-updated', note);
                    saveBoards();

                    // Board System: 付箋ボードの追記内容・期限を同期
                    try {
                        safeFetch(`${BOARD_SYSTEM_API_BASE}/sticky_notes/sync_from_postit`, {
                            method: 'PATCH',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                board_id: boardId,
                                note_id: String(note.id),
                                content: note.text || '',
                                due_date: note.dueDate ?? null
                            })
                        }).catch(err => console.error('Board System sync_from_postit:', err.message));
                    } catch (e) {
                        console.error('Error syncing to Board System:', e);
                    }

                    // AI-Board (Python) に通知（位置だけの更新・AI自身の付箋のときは通知しない）
                    if (note.author !== 'Real Cam' && note.author !== 'AI') {
                        try {
                            safeFetch(`${AI_BOARD_BASE}/api/receive_note`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    id: note.id,
                                    text: note.text,
                                    author: note.author
                                })
                            }).catch(err => console.error('Failed to notify AI-Board:', err.message));
                        } catch (e) {
                            console.error('Error notifying AI-Board:', e);
                        }
                    }
                }
            }
        });

        // 付箋削除（Board System 連携: 同じ付箋を Task/Personal からも削除）
        socket.on('delete-note', ({ boardId, noteId }) => {
            if (boards[boardId]) {
                boards[boardId].notes = boards[boardId].notes.filter((n) => n.id !== noteId);
                io.to(boardId).emit('note-deleted', noteId);
                saveBoards();
                const url = `${BOARD_SYSTEM_API_BASE}/sticky_notes/by_postit?board_id=${encodeURIComponent(boardId)}&note_id=${encodeURIComponent(String(noteId))}`;
                safeFetch(url, { method: 'DELETE' }).catch((err) => console.error('Board System delete by_postit:', err.message));
            }
        });


        // 切断処理
        socket.on('disconnect', () => {
            console.log('Client disconnected:', socket.id);

            Object.keys(boardUsers).forEach((boardId) => {
                if (boardUsers[boardId][socket.id]) {
                    const username = boardUsers[boardId][socket.id].username;
                    delete boardUsers[boardId][socket.id];

                    socket.to(boardId).emit('user-left', {
                        socketId: socket.id,
                        username
                    });
                }
            });
        });
    });

    // REST API: 死活確認
    server.get('/api/health', (req, res) => {
        res.json({ ok: true, message: 'Express API is running' });
    });

    // REST API: ボードのサマリー取得（デスクトップアプリのポーリング用）
    server.get('/api/boards/:id/summary', (req, res) => {
        try {
            const boardId = req.params.id;
            if (!boards[boardId]) {
                return res.status(404).json({ error: `Board ${boardId} not found` });
            }
            const notes = boards[boardId].notes || [];
            const lastNoteAt = notes.length
                ? Math.max(...notes.map((n) => n.createdAt || 0))
                : 0;
            return res.json({
                boardId,
                notesCount: notes.length,
                lastNoteAt,
            });
        } catch (error) {
            console.error('Error getting board summary:', error);
            return res.status(500).json({ error: 'Internal server error' });
        }
    });

    // REST API: ボードの付箋全件取得
    server.get('/api/boards/:id/notes', (req, res) => {
        try {
            const boardId = req.params.id;
            if (!boards[boardId]) {
                boards[boardId] = { notes: [], name: '' };
                saveBoards();
            }
            const notes = (boards[boardId].notes || []).map((n) => ({
                id: n.id,
                text: n.text || '',
                author: n.author || '',
                createdAt: n.createdAt || 0,
                gray: !!n.gray,
                dueDate: n.dueDate ?? null,
            }));
            return res.json({ boardId, notes });
        } catch (error) {
            console.error('Error getting board notes:', error);
            return res.status(500).json({ error: 'Internal server error' });
        }
    });

    // REST API: 付箋のグレー化またはテキスト・期限更新
    server.patch('/api/boards/:id/notes/:noteId', (req, res) => {
        try {
            const boardId = req.params.id;
            const noteId = req.params.noteId;
            const { gray, text, dueDate, due_date } = req.body || {};
            if (!boards[boardId]) {
                return res.status(404).json({ error: `Board ${boardId} not found` });
            }
            const note = (boards[boardId].notes || []).find((n) => String(n.id) === String(noteId));
            if (!note) {
                return res.status(404).json({ error: 'Note not found' });
            }
            if (gray !== undefined) note.gray = gray === true;
            if (text !== undefined) note.text = String(text);
            const targetDueDate = dueDate !== undefined ? dueDate : due_date;
            if (targetDueDate !== undefined) {
                note.dueDate = targetDueDate || null;
                delete note.due_date;
            }
            io.to(boardId).emit('note-updated', note);
            saveBoards();
            return res.json({ success: true, note });
        } catch (error) {
            console.error('Error patching board note:', error);
            return res.status(500).json({ error: 'Internal server error' });
        }
    });

    // REST API: 付箋1件削除
    server.delete('/api/boards/:id/notes/:noteId', (req, res) => {
        try {
            const boardId = req.params.id;
            const noteId = req.params.noteId;
            if (!boards[boardId]) {
                return res.status(404).json({ error: `Board ${boardId} not found` });
            }
            const before = boards[boardId].notes.length;
            boards[boardId].notes = boards[boardId].notes.filter((n) => String(n.id) !== String(noteId));
            if (boards[boardId].notes.length < before) {
                io.to(boardId).emit('note-deleted', noteId);
                saveBoards();
            }
            return res.status(204).end();
        } catch (error) {
            console.error('Error deleting board note:', error);
            return res.status(500).json({ error: 'Internal server error' });
        }
    });

    // REST API: 外部から付箋を追加するエンドポイント
    server.post('/api/sticky_notes', (req, res) => {
        try {
            const { boardId, note } = req.body;

            if (!boardId || !note) {
                return res.status(400).json({ error: 'boardId and note are required' });
            }

            if (!boards[boardId]) {
                boards[boardId] = { notes: [], name: '' };
            }

            const existingIndex = boards[boardId].notes.findIndex((n) => n.id === note.id);
            if (existingIndex >= 0) {
                boards[boardId].notes[existingIndex] = note;
                io.to(boardId).emit('note-updated', note);
            } else {
                boards[boardId].notes.push(note);
                io.to(boardId).emit('note-added', note);
            }
            saveBoards();

            if (existingIndex < 0 && note.author !== 'AI') {
                try {
                    safeFetch(`${AI_BOARD_BASE}/api/receive_note`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            id: note.id,
                            text: note.text,
                            author: note.author
                        })
                    }).catch(err => console.error('Failed to notify AI-Board:', err.message));
                } catch (e) {
                    console.error('Error notifying AI-Board:', e);
                }
            }

            console.log(`Note ${existingIndex >= 0 ? 'updated' : 'added'} via API: ${note.id} to board ${boardId}`);
            res.json({ success: true, note });
        } catch (error) {
            console.error('Error adding note via API:', error);
            res.status(500).json({ error: 'Internal server error' });
        }
    });

    // REST API: 特定のボードの全付箋を削除するエンドポイント
    server.post('/api/boards/:id/clear', (req, res) => {
        try {
            const boardId = req.params.id;

            if (!boards[boardId]) {
                return res.status(404).json({ error: `Board ${boardId} not found` });
            }

            boards[boardId].notes = [];
            saveBoards();

            io.to(boardId).emit('board-cleared');
            console.log(`Board ${boardId} cleared via REST API.`);

            try {
                safeFetch(`${AI_BOARD_BASE}/api/clear_board`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ boardId })
                }).catch(err => console.error('Failed to notify AI-Board clear:', err.message));
            } catch (e) {
                console.error('Error notifying AI-Board clear:', e);
            }

            return res.json({ success: true, message: `Board ${boardId} cleared.` });
        } catch (error) {
            console.error('Error clearing board via REST API:', error);
            return res.status(500).json({ error: 'Internal server error' });
        }
    });

    server.use((req, res) => {
        return handle(req, res);
    });

    httpServer.listen(port, (err) => {
        if (err) throw err;
        console.log(`> Ready on http://localhost:${port}`);
    });
});
