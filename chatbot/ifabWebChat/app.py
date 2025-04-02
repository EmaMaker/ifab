import json
import os
import threading
import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO

# Importa la classe IfabChatWebSocket dal server.py
from server import IfabChatWebSocket

app = Flask(__name__, static_folder='.')
CORS(app)  # Abilita CORS per tutte le route
socketio = SocketIO(app, cors_allowed_origins="*")

# Inizializza il client WebSocket per la comunicazione con il bot
chat_client = IfabChatWebSocket()

# Dizionario per tenere traccia delle connessioni socket attive
active_connections = {}


@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('.', 'index.html')


@app.route('/send-message', methods=['POST'])
def send_message():
    """Handle text message submission"""
    data = request.json
    if not data or 'text' not in data:
        return jsonify({'success': False, 'error': 'No text provided'}), 400
    
    text = data['text']
    
    # Assicurati che la conversazione sia attiva
    if not chat_client.running and not chat_client.start_conversation():
        return jsonify({'success': False, 'error': 'Failed to start conversation'}), 500
    
    # Invia il messaggio al bot
    if not chat_client.send_message(text):
        return jsonify({'success': False, 'error': 'Failed to send message'}), 500
    
    return jsonify({'success': True})


@app.route('/send-audio', methods=['POST'])
def send_audio():
    """Handle audio message submission"""
    if 'audio' not in request.files:
        return jsonify({'success': False, 'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    
    # Salva temporaneamente il file audio
    temp_path = os.path.join(os.path.dirname(__file__), 'temp_audio.wav')
    audio_file.save(temp_path)
    
    # Assicurati che la conversazione sia attiva
    if not chat_client.running and not chat_client.start_conversation():
        return jsonify({'success': False, 'error': 'Failed to start conversation'}), 500
    
    # Invia il messaggio audio al bot
    # Nota: in una implementazione reale, qui dovresti convertire l'audio in testo
    # e poi inviare il testo al bot
    if not chat_client.send_message("[Messaggio audio ricevuto - Conversione speech-to-text non ancora implementata]"):
        return jsonify({'success': False, 'error': 'Failed to send audio message'}), 500
    
    # Rimuovi il file temporaneo
    if os.path.exists(temp_path):
        os.remove(temp_path)
    
    return jsonify({'success': True})


@socketio.on('connect')
def handle_connect():
    """Handle new WebSocket connections"""
    client_id = request.sid
    active_connections[client_id] = True
    print(f"Client connected: {client_id}")
    
    # Avvia la conversazione se non è già attiva
    if not chat_client.running:
        chat_client.start_conversation()


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnections"""
    client_id = request.sid
    if client_id in active_connections:
        del active_connections[client_id]
    print(f"Client disconnected: {client_id}")


def message_callback(text):
    """Callback function for when a message is received from the bot"""
    socketio.emit('message', {'type': 'message', 'text': text})


def error_callback(error_text):
    """Callback function for when an error occurs"""
    socketio.emit('message', {'type': 'error', 'text': error_text})


if __name__ == '__main__':
    # Aggiungi i callback per gestire i messaggi e gli errori
    chat_client.add_message_callback(message_callback)
    chat_client.add_error_callback(error_callback)
    
    # Avvia il server Flask con SocketIO
    socketio.run(app, host='0.0.0.0', port=8000, debug=True, allow_unsafe_werkzeug=True)