// サーバー設定
// Next.js + Express + Socket.IO を組み合わせたWebアプリケーションサーバー
// 役割: フロントエンドの配信、Socket.IOによるリアルタイム通信、APIエンドポイントの提供

require('dotenv').config(); // PM2 起動時も .env を読み込む（AI_BOARD_URL, AI_BOARD_INSECURE_SSL 等）

const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const next = require('next');
const fs = require('fs');
const path = require('path');

// AI-Board 連携先（本番: .env に AI_BOARD_URL を設定。HTTPS の場合は https://172.16.1.251:5000）
const AI_BOARD_BASE = (process.env.AI_BOARD_URL || 'http://127.0.0.1:5000').replace(/\/$/, '');
// Board System API（付箋削除連携: 付箋ボードで削除したら Task/Personal からも削除）
const BOARD_SYSTEM_API_BASE = (process.env.BOARD_SYSTEM_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
// 付箋追加時に AI-Board へ通知するボードID（カンマ区切り。本番連携先: wl）
const AI_BOARD_LINK_BOARD_IDS = (process.env.AI_BOARD_LINK_BOARD_IDS || 'wl').split(',').map(s => s.trim()).filter(Boolean);
// AI-Board が自己証明書（HTTPS）のときは付箋ボードから fetch が失敗するため、明示的に許可する
if (process.env.NODE_ENV !== 'production' || process.env.AI_BOARD_INSECURE_SSL === '1') {
    process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
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
    let boards = {};
    if (fs.existsSync(DATA_FILE)) {
        try {
            boards = JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
            // 既存ボードに name が無い場合は空文字を補完（ボード名保存対応）
            for (const id of Object.keys(boards)) {
                if (boards[id].name === undefined) boards[id].name = '';
            }
        } catch (e) {
            console.error('Error loading boards:', e);
        }
    }

    // データ保存処理（デバウンス付き）
    // 頻繁なディスク書き込みを防ぐため、最後の更新から500ms待ってから保存する
    let saveTimeout = null;
    const saveBoards = () => {
        if (saveTimeout) {
            clearTimeout(saveTimeout);
        }

        saveTimeout = setTimeout(() => {
            fs.writeFile(DATA_FILE, JSON.stringify(boards, null, 2), (err) => {
                if (err) console.error('Error saving boards:', err);
                else console.log('Boards saved to disk');
            });
        }, 500);
    };

    // ボードごとのユーザー管理
    const boardUsers = {}; // { boardId: { socketId: { username, joinedAt } } }

    io.on('connection', (socket) => {
        console.log('Client connected:', socket.id);

        // ボードに参加
        socket.on('join-board', (boardId) => {
            socket.join(boardId);
            console.log(`Socket ${socket.id} joined board ${boardId}`);

            if (!boards[boardId]) {
                boards[boardId] = { notes: [], lines: [], name: '' };
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

            // ボードユーザー情報の初期化
            if (!boardUsers[boardId]) {
                boardUsers[boardId] = {};
            }

            // ユーザー追加
            boardUsers[boardId][socket.id] = {
                socketId: socket.id,
                username,
                joinedAt: Date.now()
            };

            // 参加者リストを全員に送信
            const usersList = Object.values(boardUsers[boardId]);
            io.to(boardId).emit('users-list', usersList);

            // 他のユーザーに参加を通知
            socket.to(boardId).emit('user-joined', {
                socketId: socket.id,
                username
            });
        });

        // 付箋追加
        socket.on('add-note', ({ boardId, note }) => {
            if (boards[boardId]) {
                boards[boardId].notes.push(note);
                io.to(boardId).emit('note-added', note);
                saveBoards();

                // 連携ボード（例: wl）で追加された付箋を AI-Board に通知（Web で追加→AI表示・AIコメント）
                if (AI_BOARD_LINK_BOARD_IDS.includes(boardId) && note.author && note.author !== 'Real Cam') {
                    try {
                        fetch(`${AI_BOARD_BASE}/api/receive_note`, {
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
                    boards[boardId].notes[index] = note;
                    socket.to(boardId).emit('note-updated', note);
                    saveBoards();

                    // AI-Board (Python) に通知（位置だけの更新・AI自身の付箋のときは通知しない）
                    if (note.author !== 'Real Cam' && note.author !== 'AI') {
                        try {
                            // Pythonサーバーへ通知（HTTPS対応）
                            fetch(`${AI_BOARD_BASE}/api/receive_note`, {
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
                fetch(url, { method: 'DELETE' }).catch((err) => console.error('Board System delete by_postit:', err.message));
            }
        });

        // 線追加（付箋間の接続）
        socket.on('add-line', ({ boardId, line }) => {
            if (boards[boardId]) {
                boards[boardId].lines.push(line);
                io.to(boardId).emit('line-added', line);
                saveBoards();
            }
        });

        // ボード全体をクリア（付箋と線を全削除）
        // クライアントからの「clear-board」イベントでトリガーされる
        socket.on('clear-board', (boardId) => {
            if (boards[boardId]) {
                boards[boardId].notes = [];
                boards[boardId].lines = [];
                saveBoards();

                // 同じボードに参加している全クライアントへ通知
                io.to(boardId).emit('board-cleared');
                console.log(`Board ${boardId} cleared by socket event.`);

                // AI-Board 側にもクリアを通知（AI-Board が HTTPS の場合は https で呼ぶ）
                try {
                    fetch(`${AI_BOARD_BASE}/api/clear_board`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ boardId })
                    }).catch(err => console.error('Failed to notify AI-Board clear:', err.message));
                } catch (e) {
                    console.error('Error notifying AI-Board clear:', e);
                }
            }
        });

        // 切断処理
        socket.on('disconnect', () => {
            console.log('Client disconnected:', socket.id);

            // 全ボードからユーザーを削除し、他ユーザーに通知
            Object.keys(boardUsers).forEach((boardId) => {
                if (boardUsers[boardId][socket.id]) {
                    const username = boardUsers[boardId][socket.id].username;
                    delete boardUsers[boardId][socket.id];

                    // 更新された参加者リストを送信
                    const usersList = Object.values(boardUsers[boardId]);
                    io.to(boardId).emit('users-list', usersList);

                    // 他ユーザーに退出を通知
                    socket.to(boardId).emit('user-left', {
                        socketId: socket.id,
                        username
                    });
                }
            });
        });
    });

    // REST API: 死活確認（本番で /api/boards/wl/summary が 404 のとき、server.js が動いているか切り分け用）
    server.get('/api/health', (req, res) => {
        res.json({ ok: true, message: 'Express API is running' });
    });

    // REST API: ボードのサマリー取得（デスクトップアプリのポーリング用・新付箋お知らせ連携）
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

    // REST API: ボードの付箋全件取得（Board System 取り込み用。gray=true は完了済みで取り込まない）
    server.get('/api/boards/:id/notes', (req, res) => {
        try {
            const boardId = req.params.id;
            if (!boards[boardId]) {
                return res.status(404).json({ error: `Board ${boardId} not found` });
            }
            const notes = (boards[boardId].notes || []).map((n) => ({
                id: n.id,
                text: n.text || '',
                author: n.author || '',
                createdAt: n.createdAt || 0,
                gray: !!n.gray,
            }));
            return res.json({ boardId, notes });
        } catch (error) {
            console.error('Error getting board notes:', error);
            return res.status(500).json({ error: 'Internal server error' });
        }
    });

    // REST API: 付箋をグレー化（Board System のゴミ箱用。削除せず表示だけグレーにする）
    server.patch('/api/boards/:id/notes/:noteId', (req, res) => {
        try {
            const boardId = req.params.id;
            const noteId = req.params.noteId;
            const { gray } = req.body || {};
            if (!boards[boardId]) {
                return res.status(404).json({ error: `Board ${boardId} not found` });
            }
            const note = (boards[boardId].notes || []).find((n) => String(n.id) === String(noteId));
            if (!note) {
                return res.status(404).json({ error: 'Note not found' });
            }
            note.gray = gray === true;
            io.to(boardId).emit('note-updated', note);
            saveBoards();
            return res.json({ success: true, note });
        } catch (error) {
            console.error('Error patching board note:', error);
            return res.status(500).json({ error: 'Internal server error' });
        }
    });

    // REST API: 付箋1件削除（付箋ボード上の削除ボタン用。Board System ゴミ箱では PATCH でグレー化を使う）
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

    // REST API: 外部から付箋を追加するエンドポイント（Python側から呼び出し）
    // AI-Board (sticky_note_detector.py) が検知した付箋を受け取る
    server.post('/api/sticky_notes', (req, res) => {
        try {
            const { boardId, note } = req.body;

            if (!boardId || !note) {
                return res.status(400).json({ error: 'boardId and note are required' });
            }

            // ボードが存在しない場合は作成
            if (!boards[boardId]) {
                boards[boardId] = { notes: [], lines: [] };
            }

            // 同一IDの付箋が既にあれば更新、なければ追加（無限増殖防止）
            const existingIndex = boards[boardId].notes.findIndex((n) => n.id === note.id);
            if (existingIndex >= 0) {
                boards[boardId].notes[existingIndex] = note;
                io.to(boardId).emit('note-updated', note);
            } else {
                boards[boardId].notes.push(note);
                io.to(boardId).emit('note-added', note);
            }
            saveBoards();

            // AI-Board (Python) に通知してリン子のコメントを生成（新規追加時のみ。AI自身の付箋は除く）
            if (existingIndex < 0 && note.author !== 'AI') {
                 try {
                     fetch(`${AI_BOARD_BASE}/api/receive_note`, {
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

    // REST API: 特定のボードの全付箋（付箋＋線）を削除するエンドポイント
    // Webクライアントや他システム（AI-Boardなど）から呼び出し可能
    server.post('/api/boards/:id/clear', (req, res) => {
        try {
            const boardId = req.params.id;

            if (!boards[boardId]) {
                return res.status(404).json({ error: `Board ${boardId} not found` });
            }

            // メモリ上のデータをクリア
            boards[boardId].notes = [];
            boards[boardId].lines = [];
            saveBoards();

            // Socket.IO でボード参加者に通知
            io.to(boardId).emit('board-cleared');
            console.log(`Board ${boardId} cleared via REST API.`);

            // AI-Board 側にもクリアを通知（AI-Board が HTTPS の場合は https で呼ぶ）
            try {
                fetch(`${AI_BOARD_BASE}/api/clear_board`, {
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
