// サーバー設定
// Next.js + Express + Socket.IO を組み合わせたWebアプリケーションサーバー
// 役割: フロントエンドの配信、Socket.IOによるリアルタイム通信、APIエンドポイントの提供

const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const next = require('next');
const fs = require('fs');
const path = require('path');

// 開発環境かどうかの判定
const dev = process.env.NODE_ENV !== 'production';
const app = next({ dev });
const handle = app.getRequestHandler();

// ポート設定
const port = process.env.PORT || 3000;
// データ保存用ファイルパス
const DATA_FILE = path.join(__dirname, 'boards.json');

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
        res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
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
                boards[boardId] = { notes: [], lines: [] };
                saveBoards();
            }

            socket.emit('init-board', boards[boardId]);
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

                    // AI-Board (Python) に通知 (Real Cam以外の場合)
                    // これにより、Webアプリで作成・編集した付箋にもAIがコメントする
                    if (note.author !== 'Real Cam') {
                        try {
                            // Pythonサーバーへ通知
                            fetch('http://localhost:5000/api/receive_note', {
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

        // 付箋削除
        socket.on('delete-note', ({ boardId, noteId }) => {
            if (boards[boardId]) {
                boards[boardId].notes = boards[boardId].notes.filter((n) => n.id !== noteId);
                io.to(boardId).emit('note-deleted', noteId);
                saveBoards();
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

                // AI-Board 側にもクリアを通知（AI-Board が起動している場合）
                try {
                    fetch('http://127.0.0.1:5000/api/clear_board', {
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

            // AI-Board (Python) に通知してAIコメントを生成させる（新規追加時のみ。更新時はコメント重複を防ぐ）
            if (note.author === 'Real Cam' && existingIndex < 0) {
                 try {
                     fetch('http://localhost:5000/api/receive_note', {
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

            // AI-Board 側にもクリアを通知（AI-Board が起動している場合）
            try {
                fetch('http://127.0.0.1:5000/api/clear_board', {
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
