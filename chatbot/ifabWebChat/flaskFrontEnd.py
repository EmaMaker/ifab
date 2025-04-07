import os
import threading
import time

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO

# Importa la classe IfabChatWebSocket dal ifabChatWebSocket.py
from ifabChatWebSocket import IfabChatWebSocket
from util import *

# Dizionario per tenere traccia delle connessioni socket attive
active_connections = {}

"""
Flask WebSocket server per la comunicazione con il bot 
@param url:                 URL del bot
@param auth:                Token di autenticazione per il bot
@param button_list_dx/sx:   Lista di tuple contenenti il testo e il percorso dell'immagine per i pulsanti statici
                            [(text, image_path), ...]
"""


def create_app(url: str, auth: str, button_list_sx: tuple[str, str], button_list_dx: tuple[str, str]) -> tuple[Flask, SocketIO, IfabChatWebSocket]:
    """Crea e restituisce l'istanza dell'app Flask, socketio e client WebSocket, con tutti i callback"""

    chat_client = IfabChatWebSocket(url, auth)  # Inizializza il client WebSocket verso il bot
    app = Flask(__name__, static_folder='.')  # Creo l'istanza dell'app Flask e imposto la cartella statica
    CORS(app)  # Abilita CORS per tutte le route
    socketio = SocketIO(app, cors_allowed_origins="*")  # Inizializza SocketIO con CORS abilitato tra il backend python ed il frontend Flask
    button_list = button_list_dx + button_list_sx  # Unisco le liste di pulsanti

    # Aggiungi una route per servire le immagini statiche
    @app.route('/images/<path:filename>')
    def serve_image(filename):
        return send_from_directory('images', filename)

    # Aggiungi una route per servire il file CSS
    @app.route('/styles.css')
    def serve_css():
        return send_from_directory('.', 'styles.css')

    # Aggiungi una route per servire il file JavaScript
    @app.route('/script.js')
    def serve_js():
        return send_from_directory('.', 'script.js')

    # Aggiungi una route per servire il file HTML e generare la pagina
    @app.route('/')
    def index():
        """Serve the main HTML page"""

        # Verifica l'esistenza dei file immagine
        def verify_buttons(button_list):
            verified_buttons = []
            for text, img_path in button_list:
                # Se l'immagine esiste, usa il percorso, altrimenti imposta a None
                full_path = os.path.join(os.path.dirname(__file__), img_path)
                if os.path.exists(full_path):
                    verified_buttons.append((text, img_path))
                else:
                    verified_buttons.append((text, None))
            return verified_buttons

        right_buttons = verify_buttons(button_list_dx)
        left_buttons = verify_buttons(button_list_sx)

        # Crea HTML per i pulsanti di sinistra
        # Leggi il contenuto del file HTML
        with open(os.path.join(os.path.dirname(__file__), 'index.html'), 'r') as file:
            html_content = file.read()

        def mkHTMLbutton(buttons):
            html = ''
            for text, img_path in buttons:
                if img_path:
                    # Assicurati che il percorso dell'immagine inizi con '/'
                    if not img_path.startswith('/'):
                        img_path = '/' + img_path
                    html += f'<button class="static-btn" style="background-image: url(\'{img_path}\')">' + '<span>' + f'{text}' + '</span>' + '</button>\n'
                else:
                    html += f'<button class="static-btn"><span>{text}</span></button>\n'
            return html

        # Sostituisci i placeholder nel template
        html_content = html_content.replace('<!-- STATIC_BUTTONS_LEFT -->', mkHTMLbutton(left_buttons))
        html_content = html_content.replace('<!-- STATIC_BUTTONS_RIGHT -->', mkHTMLbutton(right_buttons))

        return html_content

    # Aggiungi una route per gestire la richiesta di invio del messaggio testuale
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

        # Invia il messaggio al bot in un thread separato per non bloccare la risposta HTTP
        def send_message_thread():
            chat_client.send_message(text)

        threading.Thread(target=send_message_thread).start()

        return jsonify({'success': True})

    # Aggiungi una route per gestire l'invio di un comando a schermo
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
        # TODO: Gestione del comando da inviare alla camera in base al bottone
        # TODO: magari aggiungere una callback esterna
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

    # Aggiungi una route per gestire l'invio di un messaggio audio
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
        
        # Crea un URL relativo per il file audio
        audio_url = f"/temp/audio_{timestamp}.wav"

        # Assicurati che la conversazione sia attiva
        if not chat_client.running and not chat_client.start_conversation():
            return jsonify({'success': False, 'error': 'Failed to start conversation'}), 500

        # Crea un ID messaggio basato sul timestamp
        message_id = f"audio_{timestamp}"
        
        # Invia il messaggio audio al bot in un thread separato
        def send_audio_thread():
            chat_client.send_audio_message(audio_path=temp_path, message_id=message_id)
            # TODO: Rimettere la cancellazione una volta terminato lo sviluppo
            # Rimuovi il file temporaneo dopo l'invio
            # if os.path.exists(temp_path):
            #     os.remove(temp_path)
            #     print(f"File audio temporaneo rimosso: {temp_path}")

        threading.Thread(target=send_audio_thread).start()

        return jsonify({'success': True, 'file_path': audio_url, 'message_id': message_id})

    # Aggiungi una route per servire i file audio temporanei
    @app.route('/temp/<path:filename>')
    def serve_audio(filename):
        """Serve temporary audio files"""
        temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
        return send_from_directory(temp_dir, filename)
        
    # Aggiungi una route per gestire la connessione WebSocket tra backend e frontend
    @socketio.on('connect')
    def handle_connect():
        """Handle new WebSocket connections"""
        client_id = request.sid
        active_connections[client_id] = True
        print(f"Client connected: {client_id}")

        # Avvia la conversazione se non è già attiva
        if not chat_client.running:
            chat_client.start_conversation()

    # Aggiungi una route per gestire la disconnessione WebSocket
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle WebSocket disconnections"""
        client_id = request.sid
        if client_id in active_connections:
            del active_connections[client_id]
        print(f"Client disconnected: {client_id}")

    def message_callback(text, message_id=None):
        """Callback function for when a message is received from the bot"""
        messageBox("Send to client", text, StyleBox.Dash_Light)
        # Includi l'ID del messaggio se disponibile
        message_data = {'type': 'message', 'text': text}
        if message_id:
            message_data['messageId'] = message_id
        socketio.emit('message', message_data)
        # Assicurati che il messaggio venga inviato immediatamente
        socketio.sleep(0)

    def error_callback(error_text):
        """Callback function for when an error occurs"""
        socketio.emit('message', {'type': 'error', 'text': error_text})

    # Registra i callback per gestire l'inoltro dei messaggi dal bot al frontend
    chat_client.add_message_callback(message_callback)
    chat_client.add_error_callback(error_callback)

    return app, socketio, chat_client


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Avvia il server Flask con SocketIO')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host del server')
    parser.add_argument('--port', type=int, default=8000, help='Porta del server')
    args = parser.parse_args()

    # Inizializza il client WebSocket per la comunicazione con il bot
    url = "https://europe.directline.botframework.com/v3/directline/conversations"
    auth = "Bearer Ec99xFUkF1i7cR8m5TLtPokIlKXvLNdCxIYyDsraweBmf2zltwUZJQQJ99BCACi5YpzAArohAAABAZBSECEz.IpVjYOfmWMOQOHYGdH4G16pGKUArN1pEpAGJebfBjSrKI71E6ZhDJQQJ99BCACi5YpzAArohAAABAZBSMCrh"

    # Lista di pulsanti statici (testo, percorso_immagine)
    button_sx = [
        ("Zona saldatura", "images/The_Help_Logo.svg.png"),
        ("Zona debug", "images/weather.jpg"),
        ("Zona prototipazione", "images/news.jpg"),
    ]
    button_dx = [
        ("Tagliatrice Laser", "images/info.jpg"),
        ("Stampante 3D", "images/commands.jpg"),
        ("CNC", "images/music.jpg"),
        ("Stampante Plotter", "images/info.jpg"),
    ]
    app, socketio, chat_client = create_app(url, auth, button_sx, button_dx)  # Crea l'app Flask e SocketIO

    # Avvia il server Flask con SocketIO
    socketio.run(app, host=args.host, port=args.port, debug=True, allow_unsafe_werkzeug=True)  # Avvia il server Flask con SocketIO
