// サーバー設定
// Next.js + Express + Socket.IO を組み合わせたWebアプリケーションサーバー
// 役割: フロントエンドの配信、Socket.IOによるリアルタイム通信、APIエンドポイントの提供

require('dotenv').config();

const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const next = require('next');
const fs = require('fs');
const fsPromises = fs.promises;
const path = require('path');
const { Agent, fetch: undiciFetch } = require('undici');

const AI_BOARD_BASE = (process.env.AI_BOARD_URL || 'http://127.0.0.1:5000').replace(/\/$/, '');
const BOARD_SYSTEM_API_BASE = (process.env.BOARD_SYSTEM_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const AI_BOARD_LINK_BOARD_IDS = (process.env.AI_BOARD_LINK_BOARD_IDS || 'wl').split(',').map(s => s.trim()).filter(Boolean);
const INAPPROPRIATE_KEYWORDS = (process.env.INAPPROPRIATE_KEYWORDS || '')
    .split(',')
    .map(s => s.trim().toLowerCase())
    .filter(Boolean);
const INTERNAL_API_SECRET = process.env.INTERNAL_API_SECRET || 'wl-internal-secret-change-in-production';
const ALLOWED_ORIGINS = new Set(
    (process.env.CORS_ALLOWED_ORIGINS || 'http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,https://wlboardsys.internal.wonder-link.com')
        .split(',').map(value => value.trim().replace(/\/$/, '')).filter(Boolean)
);

function isAllowedOrigin(origin) {
    if (!origin) return false;
    const normalized = origin.replace(/\/$/, '');
    if (ALLOWED_ORIGINS.has(normalized)) return true;
    try {
        const { hostname } = new URL(normalized);
        if (hostname === 'localhost' || hostname === '127.0.0.1') return true;
        if (/^172\.(1[6-9]|2[0-9]|3[0-1])\.\d+\.\d+$/.test(hostname)) return true;
        if (/^192\.168\.\d+\.\d+$/.test(hostname)) return true;
        if (/^10\.\d+\.\d+\.\d+$/.test(hostname)) return true;
    } catch (e) {
        return false;
    }
    return false;
}

function isInappropriateText(text) {
    if (!text || typeof text !== 'string') return false;
    if (INAPPROPRIATE_KEYWORDS.length === 0) return false;
    const lower = text.toLowerCase();
    return INAPPROPRIATE_KEYWORDS.some(kw => lower.includes(kw));
}

// 座標値の健全性検証（有限値かつ極端な巨大値を防止）
function isValidCoordinate(val) {
    return typeof val === 'number' && Number.isFinite(val) && val >= -50000 && val <= 50000;
}

// 付箋データの型安全性とDoS防止サニタイズ
function sanitizeNotePayload(rawNote) {
    if (!rawNote || typeof rawNote !== 'object' || Array.isArray(rawNote)) {
        return null;
    }

    const id = String(rawNote.id || '').trim().slice(0, 64);
    if (!id) return null;

    const x = isValidCoordinate(rawNote.x) ? Math.round(rawNote.x * 100) / 100 : 2000;
    const y = isValidCoordinate(rawNote.y) ? Math.round(rawNote.y * 100) / 100 : 2000;
    const text = typeof rawNote.text === 'string' ? rawNote.text.slice(0, 10000) : '';
    const color = typeof rawNote.color === 'string' ? rawNote.color.slice(0, 32) : '#ffeb3b';
    const author = typeof rawNote.author === 'string' ? rawNote.author.slice(0, 50) : '';
    const dueDate = rawNote.dueDate ? String(rawNote.dueDate).slice(0, 10) : null;

    return {
        ...rawNote,
        id,
        x,
        y,
        text,
        color,
        author,
        dueDate,
        pinned: Boolean(rawNote.pinned),
        gray: Boolean(rawNote.gray),
        is_personal_only: Boolean(rawNote.is_personal_only || rawNote.isPersonalOnly),
        createdAt: typeof rawNote.createdAt === 'number' && Number.isFinite(rawNote.createdAt) ? rawNote.createdAt : Date.now()
    };
}

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

const dev = process.env.NODE_ENV !== 'production';
const app = next({ dev });
const handle = app.getRequestHandler();

const port = process.env.PORT || 3000;
const DATA_DIR = process.env.DATA_DIR || __dirname;
if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
}
const DATA_FILE = path.join(DATA_DIR, 'boards.json');

app.prepare().then(() => {
    const server = express();
    const httpServer = http.createServer(server);
    const io = new Server(httpServer, {
        cors: {
            origin: (origin, callback) => {
                if (!origin || isAllowedOrigin(origin)) {
                    callback(null, true);
                } else {
                    callback(new Error('Not allowed by CORS'));
                }
            },
            methods: ['GET', 'POST'],
        },
        maxHttpBufferSize: 1e6 // 1MB 制限で DoS を遮断
    });

    server.use((req, res, next) => {
        res.vary('Origin');
        const origin = req.get('origin');
        const allowed = isAllowedOrigin(origin);
        if (allowed) {
            res.header('Access-Control-Allow-Origin', origin);
        }
        res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS');
        res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization, x-internal-secret');
        if (req.method === 'OPTIONS') {
            return allowed ? res.sendStatus(204) : res.sendStatus(403);
        }
        next();
    });

    // 内部 API ガード
    server.use('/api', (req, res, next) => {
        const origin = req.get('origin');
        const internalSecret = req.get('x-internal-secret');
        const isMutation = ['POST', 'PUT', 'PATCH', 'DELETE'].includes(req.method);
        const fetchSite = req.get('sec-fetch-site');

        if (internalSecret && internalSecret === INTERNAL_API_SECRET) {
            return next();
        }

        if (isMutation && !origin) {
            const contentType = req.get('content-type') || '';
            if ((fetchSite && fetchSite !== 'same-origin') ||
                (!fetchSite && /^(application\/x-www-form-urlencoded|multipart\/form-data|text\/plain)/i.test(contentType))) {
                return res.sendStatus(403);
            }
        }
        if (isMutation && origin && !isAllowedOrigin(origin)) {
            return res.sendStatus(403);
        }
        return next();
    });

    server.use(express.json({ limit: '10mb' }));
    server.use(express.urlencoded({ extended: true, limit: '10mb' }));

    let boards = Object.create(null);
    if (fs.existsSync(DATA_FILE)) {
        try {
            const content = fs.readFileSync(DATA_FILE, 'utf8');
            if (content.trim()) {
                const loadedBoards = JSON.parse(content);
                if (loadedBoards && typeof loadedBoards === 'object' && !Array.isArray(loadedBoards)) {
                    boards = Object.assign(Object.create(null), loadedBoards);
                }
                for (const id of Object.keys(boards)) {
                    if (boards[id].name === undefined) boards[id].name = '';
                    if (!Array.isArray(boards[id].notes)) boards[id].notes = [];
                }
            }
        } catch (e) {
            console.error('❌ CRITICAL: Failed to parse boards.json:', e.message);
            const corruptBackup = `${DATA_FILE}.corrupt.${Date.now()}`;
            try {
                fs.copyFileSync(DATA_FILE, corruptBackup);
                console.error(`⚠️ Saved corrupted file to ${corruptBackup} to prevent total loss.`);
            } catch (copyErr) {
                console.error('Failed to backup corrupt file:', copyErr);
            }
            const tempFile = `${DATA_FILE}.tmp`;
            if (fs.existsSync(tempFile)) {
                try {
                    const tempContent = fs.readFileSync(tempFile, 'utf8');
                    const loadedTemp = JSON.parse(tempContent);
                    if (loadedTemp && typeof loadedTemp === 'object') {
                        boards = Object.assign(Object.create(null), loadedTemp);
                        console.log('✅ Recovered boards from .tmp file successfully.');
                    }
                } catch (tempErr) {
                    console.error('Failed to recover from .tmp file:', tempErr);
                }
            }
        }
    }

    let isSaving = false;
    let needsResave = false;
    let saveTimeout = null;
    let isDirty = false;

    // 非同期アトミック永続化
    const flushBoardsToDiskAsync = async () => {
        if (isSaving) {
            needsResave = true;
            return;
        }
        if (!isDirty) {
            return;
        }

        isSaving = true;
        needsResave = false;
        isDirty = false;

        const tempFile = `${DATA_FILE}.tmp`;
        try {
            const dataStr = JSON.stringify(boards, null, 2);
            await fsPromises.writeFile(tempFile, dataStr, 'utf8');
            await fsPromises.rename(tempFile, DATA_FILE);
        } catch (err) {
            isDirty = true; // 失敗時は変更状態を巻き戻す
            console.error('❌ Failed to save boards.json:', err.message);
            try { await fsPromises.unlink(tempFile); } catch (e) { }
        } finally {
            isSaving = false;
            if (needsResave) {
                saveBoards();
            }
        }
    };

    const saveBoards = () => {
        isDirty = true;
        if (saveTimeout) clearTimeout(saveTimeout);
        // 高頻度なドラッグ移動時は 400ms スロットルでディスクI/Oとシリアライズ負荷を抑制
        saveTimeout = setTimeout(() => flushBoardsToDiskAsync(), 400);
    };

    const handleShutdown = async (signal) => {
        console.log(`Received ${signal}. Closing connections and flushing data...`);
        if (saveTimeout) clearTimeout(saveTimeout);

        while (isSaving) {
            await new Promise((resolve) => setTimeout(resolve, 50));
        }

        const exitProcess = () => {
            if (isDirty) {
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

    io.on('connection', (socket) => {
        socket.on('join-board', (boardId) => {
            if (!boardId || typeof boardId !== 'string') return;
            const safeBoardId = boardId.slice(0, 64);
            socket.join(safeBoardId);

            if (!boards[safeBoardId]) {
                boards[safeBoardId] = { notes: [], name: '' };
                saveBoards();
            }

            socket.emit('init-board', boards[safeBoardId]);
        });

        socket.on('board-set-name', ({ boardId, name }) => {
            if (!boardId || typeof boardId !== 'string' || !boards[boardId]) return;
            const trimmed = (name || '').toString().trim().slice(0, 200);
            if (boards[boardId].name === trimmed) return;
            boards[boardId].name = trimmed;
            saveBoards();
            io.to(boardId).emit('board-name-updated', { name: trimmed });
        });

        socket.on('add-note', ({ boardId, note }) => {
            if (!boardId || typeof boardId !== 'string' || !boards[boardId] || !note) return;
            const sanitized = sanitizeNotePayload(note);
            if (!sanitized) return;

            if (isInappropriateText(sanitized.text)) {
                socket.emit('note-rejected', { reason: 'inappropriate_content' });
                return;
            }

            // 重複チェック
            if (boards[boardId].notes.some((n) => n.id === sanitized.id)) {
                return;
            }

            boards[boardId].notes.push(sanitized);
            io.to(boardId).emit('note-added', sanitized);
            saveBoards();

            if (AI_BOARD_LINK_BOARD_IDS.includes(boardId) && sanitized.author && sanitized.author !== 'Real Cam') {
                try {
                    safeFetch(`${AI_BOARD_BASE}/api/receive_note`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            id: sanitized.id,
                            text: sanitized.text || '',
                            author: sanitized.author || 'Unknown'
                        })
                    }).catch(err => console.error('Failed to notify AI-Board (add-note):', err.message));
                } catch (e) {
                    console.error('Error notifying AI-Board (add-note):', e);
                }
            }
        });

        socket.on('update-note', ({ boardId, note }) => {
            if (!boardId || typeof boardId !== 'string' || !boards[boardId] || !note || !note.id) return;
            const index = boards[boardId].notes.findIndex((n) => n.id === note.id);
            if (index === -1) return;

            const oldNote = boards[boardId].notes[index];
            const sanitized = sanitizeNotePayload(note);
            if (!sanitized) return;

            const mergedNote = {
                ...oldNote,
                ...sanitized,
                gray: sanitized.gray !== undefined ? sanitized.gray : oldNote.gray,
                is_personal_only: sanitized.is_personal_only !== undefined
                    ? sanitized.is_personal_only
                    : (oldNote.is_personal_only ?? false),
                dueDate: sanitized.dueDate !== undefined ? sanitized.dueDate : oldNote.dueDate
            };

            const isTextChanged = oldNote.text !== mergedNote.text;
            const isDueDateChanged = oldNote.dueDate !== mergedNote.dueDate;

            if (isInappropriateText(mergedNote.text)) {
                socket.emit('note-rejected', { reason: 'inappropriate_content' });
                boards[boardId].notes = boards[boardId].notes.filter((n) => n.id !== note.id);
                io.to(boardId).emit('note-deleted', note.id);
                saveBoards();
                const url = `${BOARD_SYSTEM_API_BASE}/sticky_notes/by_postit?board_id=${encodeURIComponent(boardId)}&note_id=${encodeURIComponent(String(note.id))}`;
                safeFetch(url, { method: 'DELETE' }).catch((err) => console.error('Board System delete by_postit:', err.message));
                return;
            }

            boards[boardId].notes[index] = mergedNote;
            socket.to(boardId).emit('note-updated', mergedNote);
            saveBoards();

            if (isTextChanged || isDueDateChanged) {
                try {
                    safeFetch(`${BOARD_SYSTEM_API_BASE}/sticky_notes/sync_from_postit`, {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            board_id: boardId,
                            note_id: String(mergedNote.id),
                            content: mergedNote.text || '',
                            due_date: mergedNote.dueDate || ""
                        })
                    }).catch(err => console.error('Board System sync_from_postit:', err.message));
                } catch (e) {
                    console.error('Error syncing to Board System:', e);
                }
            }

            if (AI_BOARD_LINK_BOARD_IDS.includes(boardId) && isTextChanged && mergedNote.author !== 'Real Cam' && mergedNote.author !== 'AI') {
                try {
                    safeFetch(`${AI_BOARD_BASE}/api/receive_note`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            id: mergedNote.id,
                            text: mergedNote.text,
                            author: mergedNote.author
                        })
                    }).catch(err => console.error('Failed to notify AI-Board:', err.message));
                } catch (e) {
                    console.error('Error notifying AI-Board:', e);
                }
            }
        });

        socket.on('delete-note', ({ boardId, noteId }) => {
            if (!boardId || !boards[boardId] || !noteId) return;
            const beforeLen = boards[boardId].notes.length;
            boards[boardId].notes = boards[boardId].notes.filter((n) => n.id !== noteId);
            if (boards[boardId].notes.length < beforeLen) {
                io.to(boardId).emit('note-deleted', noteId);
                saveBoards();
                const url = `${BOARD_SYSTEM_API_BASE}/sticky_notes/by_postit?board_id=${encodeURIComponent(boardId)}&note_id=${encodeURIComponent(String(noteId))}`;
                safeFetch(url, { method: 'DELETE' }).catch((err) => console.error('Board System delete by_postit:', err.message));
            }
        });
    });

    server.get('/api/health', (req, res) => {
        res.json({ ok: true, message: 'Express API is running' });
    });

    server.get('/api/boards/:id/summary', (req, res) => {
        try {
            const boardId = req.params.id;
            if (!boards[boardId]) {
                return res.status(404).json({ error: `Board ${boardId} not found` });
            }
            const notes = boards[boardId].notes || [];
            const lastNoteAt = notes.reduce((max, n) => Math.max(max, n.createdAt || 0), 0);
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

    server.get('/api/boards/:id/notes', (req, res) => {
        try {
            const boardId = req.params.id;
            if (!boards[boardId]) {
                return res.json({ boardId, notes: [] });
            }
            const notes = (boards[boardId].notes || []).map((n) => ({
                id: n.id,
                text: n.text || '',
                author: n.author || '',
                createdAt: n.createdAt || 0,
                gray: !!n.gray,
                dueDate: n.dueDate ?? null,
                is_personal_only: Boolean(n.is_personal_only || n.isPersonalOnly || false),
            }));
            return res.json({ boardId, notes });
        } catch (error) {
            console.error('Error getting board notes:', error);
            return res.status(500).json({ error: 'Internal server error' });
        }
    });

    server.patch('/api/boards/:id/notes/:noteId', (req, res) => {
        try {
            const boardId = req.params.id;
            const noteId = req.params.noteId;
            const { gray, text, dueDate, due_date, is_personal_only, isPersonalOnly } = req.body || {};
            if (!boards[boardId]) {
                return res.status(404).json({ error: `Board ${boardId} not found` });
            }
            const note = (boards[boardId].notes || []).find((n) => String(n.id) === String(noteId));
            if (!note) {
                return res.status(404).json({ error: 'Note not found' });
            }
            if (gray !== undefined) note.gray = gray === true;
            if (text !== undefined) note.text = String(text).slice(0, 10000);
            const targetDueDate = dueDate !== undefined ? dueDate : due_date;
            if (targetDueDate !== undefined) {
                note.dueDate = targetDueDate ? String(targetDueDate).slice(0, 10) : null;
                delete note.due_date;
            }
            if (is_personal_only !== undefined || isPersonalOnly !== undefined) {
                note.is_personal_only = Boolean(is_personal_only !== undefined ? is_personal_only : isPersonalOnly);
            }
            io.to(boardId).emit('note-updated', note);
            saveBoards();
            return res.json({ success: true, note });
        } catch (error) {
            console.error('Error patching board note:', error);
            return res.status(500).json({ error: 'Internal server error' });
        }
    });

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

    server.post('/api/sticky_notes', (req, res) => {
        try {
            const { boardId, note } = req.body;

            if (!boardId || !note) {
                return res.status(400).json({ error: 'boardId and note are required' });
            }

            const sanitized = sanitizeNotePayload(note);
            if (!sanitized) {
                return res.status(400).json({ error: 'invalid note data' });
            }

            if (!boards[boardId]) {
                boards[boardId] = { notes: [], name: '' };
            }

            const existingIndex = boards[boardId].notes.findIndex((n) => n.id === sanitized.id);
            if (existingIndex >= 0) {
                boards[boardId].notes[existingIndex] = sanitized;
                io.to(boardId).emit('note-updated', sanitized);
            } else {
                boards[boardId].notes.push(sanitized);
                io.to(boardId).emit('note-added', sanitized);
            }
            saveBoards();

            if (existingIndex < 0 && sanitized.author !== 'AI') {
                try {
                    safeFetch(`${AI_BOARD_BASE}/api/receive_note`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            id: sanitized.id,
                            text: sanitized.text,
                            author: sanitized.author
                        })
                    }).catch(err => console.error('Failed to notify AI-Board:', err.message));
                } catch (e) {
                    console.error('Error notifying AI-Board:', e);
                }
            }

            res.json({ success: true, note: sanitized });
        } catch (error) {
            console.error('Error adding note via API:', error);
            res.status(500).json({ error: 'Internal server error' });
        }
    });

    server.post('/api/boards/:id/clear', (req, res) => {
        try {
            const boardId = req.params.id;

            if (!boards[boardId]) {
                return res.status(404).json({ error: `Board ${boardId} not found` });
            }

            boards[boardId].notes = [];
            saveBoards();

            io.to(boardId).emit('board-cleared');

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