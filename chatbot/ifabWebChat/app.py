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

# Aggiungi una route per servire le immagini statiche
@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('images', filename)

@app.route('/styles.css')
def serve_css():
    return send_from_directory('.', 'styles.css')

@app.route('/script.js')
def serve_js():
    return send_from_directory('.', 'script.js')

# Inizializza il client WebSocket per la comunicazione con il bot
chat_client = IfabChatWebSocket()

# Dizionario per tenere traccia delle connessioni socket attive
active_connections = {}


# Lista di pulsanti statici (testo, percorso_immagine)
button_list = [
    ("Aiuto", "images/The_Help_Logo.svg.png"),
    ("Informazioni", "images/info.jpg"),
    ("Comandi", "images/commands.jpg"),
    ("Meteo", "images/weather.jpg"),
    ("Notizie", "images/news.jpg"),
    ("Musica", "images/music.jpg")
]

@app.route('/')
def index():
    """Serve the main HTML page"""
    # Verifica l'esistenza dei file immagine
    verified_buttons = []
    for text, img_path in button_list:
        # Se l'immagine esiste, usa il percorso, altrimenti imposta a None
        full_path = os.path.join(os.path.dirname(__file__), img_path)
        if os.path.exists(full_path):
            verified_buttons.append((text, img_path))
        else:
            verified_buttons.append((text, None))
    
    # Leggi il contenuto del file HTML
    with open(os.path.join(os.path.dirname(__file__), 'index.html'), 'r') as file:
        html_content = file.read()
    
    # Dividi i pulsanti tra sinistra e destra
    left_buttons = verified_buttons[:len(verified_buttons)//2]
    right_buttons = verified_buttons[len(verified_buttons)//2:]
    
    # Crea HTML per i pulsanti di sinistra
    left_html = ''
    for text, img_path in left_buttons:
        if img_path:
            # Assicurati che il percorso dell'immagine inizi con '/'
            if not img_path.startswith('/'):
                img_path = '/' + img_path
            left_html += f'<button class="static-btn" style="background-image: url(\'{img_path}\')">'+'<span>'+f'{text}'+'</span>'+'</button>\n'
        else:
            left_html += f'<button class="static-btn"><span>{text}</span></button>\n'
    
    # Crea HTML per i pulsanti di destra
    right_html = ''
    for text, img_path in right_buttons:
        if img_path:
            # Assicurati che il percorso dell'immagine inizi con '/'
            if not img_path.startswith('/'):
                img_path = '/' + img_path
            right_html += f'<button class="static-btn" style="background-image: url(\'{img_path}\')">'+'<span>'+f'{text}'+'</span>'+'</button>\n'
        else:
            right_html += f'<button class="static-btn"><span>{text}</span></button>\n'
    
    # Sostituisci i placeholder nel template
    html_content = html_content.replace('<!-- STATIC_BUTTONS_LEFT -->', left_html)
    html_content = html_content.replace('<!-- STATIC_BUTTONS_RIGHT -->', right_html)
    
    return html_content


@app.route('/send-message', methods=['POST'])
def send_message():
    """Handle text message submission"""
    data = request.json
    if not data or 'text' not in data:
        return jsonify({'success': False, 'error': 'No text provided'}), 400
    
    text = data['text']
    
    # Controlla se il messaggio proviene da un pulsante statico
    is_button = False
    for button_text, _ in button_list:
        if text.strip() == button_text.strip():
            is_button = True
            # Stampa il testo del pulsante per debug
            print(f"Pulsante premuto: {text}")
            break
    
    # Assicurati che la conversazione sia attiva
    if not chat_client.running and not chat_client.start_conversation():
        return jsonify({'success': False, 'error': 'Failed to start conversation'}), 500
    
    # Invia il messaggio al bot in un thread separato per non bloccare la risposta HTTP
    def send_message_thread():
        chat_client.send_message(text)
    
    threading.Thread(target=send_message_thread).start()
    
    return jsonify({'success': True})


@app.route('/button-click', methods=['POST'])
def button_click():
    """Handle button click events without sending to chatbot"""
    data = request.json
    if not data or 'text' not in data:
        return jsonify({'success': False, 'error': 'No text provided'}), 400
    
    button_text = data['text']
    
    # Verifica se il testo corrisponde a uno dei pulsanti statici
    is_valid_button = False
    for text, _ in button_list:
        if button_text.strip() == text.strip():
            is_valid_button = True
            break
    
    if not is_valid_button:
        return jsonify({'success': False, 'error': 'Invalid button text'}), 400
    
    # Stampa il testo del pulsante nel server per debug
    print(f"Comando ricevuto: {button_text}")
    
    # Qui puoi aggiungere la logica per gestire il comando
    # Invece di inviare il messaggio al chatbot, registra solo il comando
    # che verrà poi utilizzato per chiamare altre funzioni
    
    # Esempio di come potresti gestire diversi comandi:
    # if button_text == "Aiuto":
    #     # Chiama una funzione specifica per l'aiuto
    #     pass
    # elif button_text == "Informazioni":
    #     # Chiama una funzione specifica per le informazioni
    #     pass
    
    return jsonify({'success': True, 'command': button_text})


# Aggiungi il percorso dei file temporanei nei log
@app.route('/upload-audio', methods=['POST'])
def send_audio():
    """Handle audio message submission"""
    if 'audio' not in request.files:
        return jsonify({'success': False, 'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    
    # Crea una directory temporanea se non esiste
    temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    # Genera un nome file univoco con timestamp
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    temp_path = os.path.join(temp_dir, f'audio_{timestamp}.wav')
    
    # Salva il file audio e logga il percorso
    audio_file.save(temp_path)
    print(f"File audio temporaneo salvato in: {temp_path}")
    
    # Assicurati che la conversazione sia attiva
    if not chat_client.running and not chat_client.start_conversation():
        return jsonify({'success': False, 'error': 'Failed to start conversation'}), 500
    
    # Invia il messaggio audio al bot in un thread separato
    def send_audio_thread():
        chat_client.send_message(f"[Messaggio audio ricevuto - File: {temp_path}]")
        # TODO: Rimettere la cancellazione una volta terminato lo sviluppo
        # Rimuovi il file temporaneo dopo l'invio
        # if os.path.exists(temp_path):
        #     os.remove(temp_path)
        #     print(f"File audio temporaneo rimosso: {temp_path}")
    
    threading.Thread(target=send_audio_thread).start()
    
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
    print(f"Sending message to clients: {text}")
    socketio.emit('message', {'type': 'message', 'text': text})
    # Assicurati che il messaggio venga inviato immediatamente
    socketio.sleep(0)


def error_callback(error_text):
    """Callback function for when an error occurs"""
    socketio.emit('message', {'type': 'error', 'text': error_text})


# Registra i callback per gestire i messaggi e gli errori
chat_client.add_message_callback(message_callback)
chat_client.add_error_callback(error_callback)

if __name__ == '__main__':
    # Avvia il server Flask con SocketIO
    socketio.run(app, host='0.0.0.0', port=8000, debug=True, allow_unsafe_werkzeug=True)