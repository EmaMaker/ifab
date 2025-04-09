import shutil
import threading
import time
from typing import Callable

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO

# Importa la classe IfabChatWebSocket dal ifabChatWebSocket.py
from ifabChatWebSocket import IfabChatWebSocket
from pyLib import AudioPlayer as ap
from pyLib.text_utils import clean_markdown_for_tts
from pyLib.util import *

"""
Flask WebSocket server per la comunicazione con il bot 
@param url:                 URL del bot
@param auth:                Token di autenticazione per il bot
@param button_list_dx/sx:   Lista di tuple contenenti il testo e il percorso dell'immagine per i pulsanti statici
                            [(text, image_path), ...]
@param sttFun:              Funzione di callback per la trascrizione audio (opzionale)
                            @param sttFun(pathToAudio) -> Transcription | None
@param ttsFun:              Funzione di callback per la sintesi vocale (opzionale)
                            @param ttsFun(text) -> None
"""


def create_app(url: str, auth: str, button_list_sx: tuple[str, str], button_list_dx: tuple[str, str],
               sttFun: Callable[[str], str | None] = None,
               ttsFun: Callable[[str], None] = None) -> tuple[
    Flask, SocketIO, IfabChatWebSocket]:
    """Crea e restituisce l'istanza dell'app Flask, socketio e client WebSocket, con tutti i callback"""

    # Callback per gestire l'inoltro dei messaggi dal backend (bot o stt) al frontend
    # se ho un messaggio ID, allora devo aggiornare quel baloon
    def backEnd_msg2UI(text, message_id=None):
        """Callback function for when a message is received from the bot"""
        if not message_id:  # Nessuno ID messaggio, quindi è un messaggio normale
            messageBox("Send new message to frontEnd", text, StyleBox.Dash_Light)
            message_data = {'type': 'message', 'text': text}
            if ttsFun:
                # Pulisci il testo da elementi Markdown prima di inviarlo al TTS
                clean_text = clean_markdown_for_tts(text)
                messageBox("Send to TTS", clean_text, StyleBox.Dash_Light)
                ttsFun(clean_text)
            socketio.emit('message', message_data)
        else:  #
            messageBox("Send to frontEnd audio transcription to append", text, StyleBox.Dash_Light)
            message_data = {'type': 'message', 'text': text, 'messageId': message_id}
            socketio.emit('stt', message_data)
        socketio.sleep(0)  # Assicurati che il messaggio venga inviato immediatamente

    def bot_err2UI(error_text):
        """Callback function for when an error occurs"""
        socketio.emit('message', {'type': 'error', 'text': error_text})

    # Mock function for STT (Speech-to-Text) processing
    def stt_mock(audio_path=None) -> str | None:
        """Elaborate the audio message with speech-to-text processing"""
        # This would typically involve sending the audio file to a speech-to-text service
        # and then sending the resulting text to the bot
        # For now, we'll just send a placeholder message
        if not audio_path:
            print("No audio data provided")
            return None
        print("Audio data received")
        time.sleep(1)  # Simulate processing time
        return f"Trascrizione del messaggio, Mock per {os.path.basename(audio_path)}"

    # Inizializzo gli oggetti e li configuro per l'interfaccia grafica
    chat_client = IfabChatWebSocket(url, auth)  # Inizializza il client WebSocket verso il bot
    app = Flask(__name__, static_folder='web-client')  # Creo l'istanza dell'app Flask e imposto la cartella statica
    CORS(app)  # Abilita CORS per tutte le route
    socketio = SocketIO(app, cors_allowed_origins="*")  # Inizializza SocketIO con CORS abilitato tra il backend python ed il frontend Flask

    # Configurazione delle callback esterne
    stt_funx = sttFun if sttFun else stt_mock  # Se non viene fornita una funzione STT, usa la funzione di mock
    # TODO: Callback a piper per gestire la creazione degli audio

    # Registra i callback per gestire l'inoltro dei messaggi dal bot al frontend
    chat_client.add_message_callback(backEnd_msg2UI)
    chat_client.add_error_callback(bot_err2UI)

    # Gestione dell'evento di connessione Socket.IO
    @socketio.on('connect')
    def handle_connect():
        """Gestisce l'evento di connessione di un client Socket.IO"""
        messageBox("Nuova connessione frontend", "Avvio nuova conversazione con il bot", StyleBox.Dash_Bold)

        # Invia un messaggio di benvenuto all'utente
        socketio.emit('message', {'type': 'message', 'text': 'Benvenuto! Puoi scrivere un messaggio o registrare un messaggio vocale.'})

        # Gestione più robusta della connessione
        try:
            if chat_client.running:
                messageBox("Chiusura conversazione", "Chiudo la conversazione precedente con il bot", StyleBox.Light)
                chat_client.stop_conversation()
                # Breve pausa per assicurarsi che la connessione precedente sia completamente chiusa
                time.sleep(0.5)

            # Tenta di avviare una nuova conversazione
            if not chat_client.start_conversation():
                messageBox("Errore connessione", "Impossibile avviare la conversazione con il bot", StyleBox.Error)
                socketio.emit('message', {'type': 'error', 'text': 'Impossibile avviare la conversazione con il bot'})
        except Exception as e:
            messageBox("Errore connessione", f"Errore durante l'avvio della conversazione: {str(e)}", StyleBox.Error)
            socketio.emit('message', {'type': 'error', 'text': f'Errore durante la connessione: {str(e)}'})

    # Crea una directory temporanea vuota all'avvio del server
    temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)  # Rimuovi la directory temporanea esistente
    os.makedirs(temp_dir, exist_ok=True)

    # Aggiungi una route per servire le immagini statiche
    @app.route('/images/<path:filename>')
    def serve_image(filename):
        return send_from_directory('web-client/images', filename)

    # Aggiungi una route per servire il file CSS
    @app.route('/css/<path:filename>')
    def serve_css(filename):
        return send_from_directory('web-client/css', filename)

    # Aggiungi una route per servire il file JavaScript
    @app.route('/js/<path:filename>')
    def serve_js(filename):
        return send_from_directory('web-client/js', filename)

    # Aggiungi route per servire le librerie JavaScript locali
    @app.route('/libs/<path:filename>')
    def serve_libs(filename):
        return send_from_directory('web-client/libs', filename)

    @app.route('/favicon.ico')
    def serve_favicon():
        return send_from_directory('web-client', 'favicon.ico')

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
        with open(os.path.join(os.path.dirname(__file__), 'web-client/index.html'), 'r') as file:
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

        # Gestione più robusta della connessione
        try:
            # Se la connessione non è attiva, tenta di riavviarla
            if not chat_client.running:
                messageBox("Riconnessione", "Tentativo di riavvio della conversazione", StyleBox.Light)
                if not chat_client.start_conversation():
                    return jsonify({'success': False, 'error': 'Impossibile avviare la conversazione'}), 500
                # Breve pausa per assicurarsi che la connessione sia stabilita
                time.sleep(0.5)

            # Invia il messaggio al bot in un thread separato per non bloccare la risposta HTTP
            def send_message_thread():
                chat_client.send_message(text)

            threading.Thread(target=send_message_thread).start()
            messageBox("Frontend Messaggio di testo", text, StyleBox.Light)
            return jsonify({'success': True})
        except Exception as e:
            messageBox("Errore invio", f"Errore durante l'invio del messaggio: {str(e)}", StyleBox.Error)
            return jsonify({'success': False, 'error': f'Errore durante l\'invio: {str(e)}'}), 500

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
        for text, _ in button_list_sx + button_list_dx:
            if button_text.strip() == text.strip():
                is_valid_button = True
                break

        if not is_valid_button:
            return jsonify({'success': False, 'error': 'Invalid button text'}), 400

        # Stampa il testo del pulsante nel server per debug
        messageBox("Frontend comando", button_text, StyleBox.Light)
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

        # Genera un nome file univoco con timestamp
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        temp_path = os.path.join(temp_dir, f'audio_{timestamp}.wav')

        # Salva il file audio e logga il percorso
        audio_file.save(temp_path)
        messageBox("Frontend audio", f"File audio temporaneo salvato in: {temp_path}", StyleBox.Light)

        # Crea un URL relativo per il file audio
        audio_url = f"/temp/audio_{timestamp}.wav"

        # Gestione più robusta della connessione
        try:
            # Se la connessione non è attiva, tenta di riavviarla
            if not chat_client.running:
                messageBox("Riconnessione", "Tentativo di riavvio della conversazione per audio", StyleBox.Light)
                if not chat_client.start_conversation():
                    return jsonify({'success': False, 'error': 'Impossibile avviare la conversazione'}), 500
                # Breve pausa per assicurarsi che la connessione sia stabilita
                time.sleep(0.5)

            # Crea un ID messaggio basato sul timestamp
            message_id = f"audio_{timestamp}"

            # Invia il messaggio audio al bot in un thread separato per non bloccare la risposta HTTP
            def send_audio_thread(audio_path, message_id):
                stt_audio_text = stt_funx(audio_path=audio_path)
                if stt_audio_text:
                    messageBox("Backend audio STT", f"Trascrizione audio: {stt_audio_text}", StyleBox.Light)
                    backEnd_msg2UI(stt_audio_text, message_id=message_id)  # Invia messaggio trascritto al frontend
                    if stt_funx is not stt_mock:  # Invia messaggio trascritto al bot solo se veramente trascritto
                        messageBox("Backend audio STT to Bot", "Trascrizione audio inviata al bot", StyleBox.Light)
                        chat_client.send_message(stt_audio_text)
                    else:
                        time.sleep(1)  # Simula un breve ritardo per il mock
                        messageBox("Backend audio STT to Bot", "Trascrizione audio non inviata al bot, Mock STT", StyleBox.Light)
                        backEnd_msg2UI("Trascrizione audio non inviata al bot, Mock STT")  # Invia messaggio mock al frontend

                else:
                    messageBox("Backend audio STT", "Errore durante la trascrizione audio", StyleBox.Light)
                    backEnd_msg2UI("Impossibile trascrivere il messaggio audio", message_id=message_id)

            threading.Thread(target=send_audio_thread, args=(temp_path, message_id,)).start()
            return jsonify({'success': True, 'file_path': audio_url, 'message_id': message_id})

        except Exception as e:
            messageBox("Errore audio", f"Errore durante l'elaborazione dell'audio: {str(e)}", StyleBox.Error)
            return jsonify({'success': False, 'error': f'Errore durante l\'elaborazione: {str(e)}'}), 500

    # Aggiungi una route per servire i file audio temporanei
    @app.route('/temp/<path:filename>')
    def serve_audio(filename):
        """Serve temporary audio files"""
        temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
        return send_from_directory(temp_dir, filename)

    # Aggiungi una route per verificare lo stato della connessione
    @app.route('/check-connection', methods=['GET'])
    def check_connection():
        """Check if the connection to the bot is active"""
        is_connected = chat_client.running
        if not is_connected:
            # Tenta di riavviare la connessione se non è attiva
            is_connected = chat_client.start_conversation()

        return jsonify({
            'connected': is_connected,
            'status': 'active' if is_connected else 'disconnected'
        })

    # Aggiungi una route per la pagina "Chi siamo"
    @app.route('/about')
    def about():
        """Serve the about page"""
        with open(os.path.join(os.path.dirname(__file__), 'web-client/about.html'), 'r') as file:
            html_content = file.read()
        return html_content

    # Gestione dell'evento di disconnessione Socket.IO
    @socketio.on('disconnect')
    def handle_disconnect():
        """Gestisce l'evento di disconnessione di un client Socket.IO"""
        messageBox("Disconnessione frontend", "Client disconnesso", StyleBox.Light)
        # Non chiudiamo la conversazione qui, poiché potrebbe essere un refresh della pagina
        # e vogliamo mantenere la conversazione attiva per quando l'utente si riconnette

    return app, socketio, chat_client


if __name__ == '__main__':
    import argparse

    herePath = os.path.join(os.path.dirname(__file__))
    parser = argparse.ArgumentParser(description='Avvia il server Flask con SocketIO')
    parser.add_argument('--host', type=str, default='0.0.0.0', help="Host del server [default '%(default)s']")
    parser.add_argument('--port', type=int, default=8000, help="Porta del server [default '%(default)s']")
    parser.add_argument("--model", type=str, help="Path to the Piper-TTS model [default '%(default)s']",
                        default=os.path.relpath(os.path.join(herePath, "tts-model", "it_IT-paola-medium.onnx")))
    args = parser.parse_args()

    # Inizializza TTS
    print(f"Caricamento del modello TTS da: {args.model}")
    player = ap.AudioPlayer(args.model)
    print("Modello TTS caricato con successo")
    # Inizializza il client WebSocket per la comunicazione con il bot
    # Token Bot Ema:
    # url = "https://europe.directline.botframework.com/v3/directline/conversations"
    # auth = "Bearer Ec99xFUkF1i7cR8m5TLtPokIlKXvLNdCxIYyDsraweBmf2zltwUZJQQJ99BCACi5YpzAArohAAABAZBSECEz.IpVjYOfmWMOQOHYGdH4G16pGKUArN1pEpAGJebfBjSrKI71E6ZhDJQQJ99BCACi5YpzAArohAAABAZBSMCrh"
    # Token Bot Fondazione:
    url = "https://europe.directline.botframework.com/v3/directline/conversations"
    auth = "Bearer BI91xBzzXppQiRxyBjniBLPFctD8IGqIR0BCmQCyODxSZrZjLX7QJQQJ99BDACi5YpzAArohAAABAZBS4vKQ.DEsKhbDDeYsTi7cHcOgSMV4HrdEnNrJAPp8hTnCv55nxFqtKRfonJQQJ99BDACi5YpzAArohAAABAZBS4AHw"

    # Lista di pulsanti statici (testo, percorso_immagine)
    button_sx = [
        ("Zona saldatura", "web-client/images/The_Help_Logo.svg.png"),
        ("Zona debug", "images/weather.jpg"),
        ("Zona prototipazione", "images/news.jpg"),
    ]
    button_dx = [
        ("Tagliatrice Laser", "images/info.jpg"),
        ("Stampante 3D", "images/commands.jpg"),
        ("CNC", "images/music.jpg"),
        ("Stampante Plotter", "images/info.jpg"),
    ]
    app, socketio, chat_client = create_app(url, auth, button_sx, button_dx, ttsFun=player.play_text)  # Crea l'app Flask e SocketIO

    # Avvia il server Flask con SocketIO
    socketio.run(app, host=args.host, port=args.port, debug=True, allow_unsafe_werkzeug=True)  # Avvia il server Flask con SocketIO
