import os
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import eventlet
import ai_avatar

# Initialize Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'captures')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    x = request.form.get('x', 0)
    y = request.form.get('y', 0)
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        
        # Notify clients about the note first
        socketio.emit('new_note', {
            'filename': file.filename,
            'x': x,
            'y': y
        })
        
        # Async generation of comment (using eventlet spawn)
        def generate_and_notify():
            comment = ai_avatar.generate_comment(filepath)
            print(f"AI Comment: {comment}")
            socketio.emit('ai_comment', {'comment': comment})
            
        eventlet.spawn(generate_and_notify)
        
        return jsonify({'message': 'File uploaded successfully', 'filename': file.filename}), 200

if __name__ == '__main__':
    print("Starting Flask Server...")
    # Listen on all interfaces
    socketio.run(app, host='0.0.0.0', port=5000)
