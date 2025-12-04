const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const next = require('next');
const fs = require('fs');
const path = require('path');

const dev = process.env.NODE_ENV !== 'production';
const app = next({ dev });
const handle = app.getRequestHandler();

const port = process.env.PORT || 3000;
const DATA_FILE = path.join(__dirname, 'boards.json');

app.prepare().then(() => {
    const server = express();
    const httpServer = http.createServer(server);
    const io = new Server(httpServer);

    // Load boards from file or initialize empty
    let boards = {};
    if (fs.existsSync(DATA_FILE)) {
        try {
            boards = JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
        } catch (e) {
            console.error('Error loading boards:', e);
        }
    }

    let saveTimeout = null;
    const saveBoards = () => {
        // Debounce: only save to disk after 500ms of no updates
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

    // Store users by board
    const boardUsers = {}; // { boardId: { socketId: { username, joinedAt } } }

    io.on('connection', (socket) => {
        console.log('Client connected:', socket.id);

        socket.on('join-board', (boardId) => {
            socket.join(boardId);
            console.log(`Socket ${socket.id} joined board ${boardId}`);

            if (!boards[boardId]) {
                boards[boardId] = { notes: [], lines: [] };
                saveBoards();
            }

            socket.emit('init-board', boards[boardId]);
        });

        socket.on('user-join', ({ boardId, username }) => {
            console.log(`User ${username} (${socket.id}) joined board ${boardId}`);

            // Initialize board users if needed
            if (!boardUsers[boardId]) {
                boardUsers[boardId] = {};
            }

            // Add user
            boardUsers[boardId][socket.id] = {
                socketId: socket.id,
                username,
                joinedAt: Date.now()
            };

            // Notify all users in the board
            const usersList = Object.values(boardUsers[boardId]);
            io.to(boardId).emit('users-list', usersList);

            // Broadcast to others that someone joined
            socket.to(boardId).emit('user-joined', {
                socketId: socket.id,
                username
            });
        });

        socket.on('add-note', ({ boardId, note }) => {
            if (boards[boardId]) {
                boards[boardId].notes.push(note);
                io.to(boardId).emit('note-added', note);
                saveBoards();
            }
        });

        socket.on('update-note', ({ boardId, note }) => {
            if (boards[boardId]) {
                const index = boards[boardId].notes.findIndex((n) => n.id === note.id);
                if (index !== -1) {
                    boards[boardId].notes[index] = note;
                    socket.to(boardId).emit('note-updated', note);
                    saveBoards();
                }
            }
        });

        socket.on('add-line', ({ boardId, line }) => {
            if (boards[boardId]) {
                boards[boardId].lines.push(line);
                io.to(boardId).emit('line-added', line);
                saveBoards();
            }
        });

        socket.on('disconnect', () => {
            console.log('Client disconnected:', socket.id);

            // Remove user from all boards and notify others
            Object.keys(boardUsers).forEach((boardId) => {
                if (boardUsers[boardId][socket.id]) {
                    const username = boardUsers[boardId][socket.id].username;
                    delete boardUsers[boardId][socket.id];

                    // Send updated users list
                    const usersList = Object.values(boardUsers[boardId]);
                    io.to(boardId).emit('users-list', usersList);

                    // Notify others that user left
                    socket.to(boardId).emit('user-left', {
                        socketId: socket.id,
                        username
                    });
                }
            });
        });
    });

    server.use((req, res) => {
        return handle(req, res);
    });

    httpServer.listen(port, (err) => {
        if (err) throw err;
        console.log(`> Ready on http://localhost:${port}`);
    });
});
