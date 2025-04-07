import json
import os
import socketserver
import sys
import threading
import time

import requests
import websocket

from util import *

class IfabChatWebSocket:
    """ Class to manage WebSocket connection to the Ifab Chatbot API and the backend"""
    def __init__(self, url, auth_token, user_id="user1", port=8000):
        # Connection parameters
        self.url = url
        self.headers = {
            "Authorization": auth_token,
            "Content-Type": "application/json"
        }
        self.user_id = user_id
        self.port = port
        # State variables
        self.conversation_id = None
        self.ws = None
        self.ws_thread = None
        self.running = False
        self.watermark = None
        self.waiting_for_response = False
        self.message_callbacks = []
        self.error_callbacks = []

    def add_message_callback(self, callback):
        """Add a callback function to be called when a message is received"""
        self.message_callbacks.append(callback)

    def add_error_callback(self, callback):
        """Add a callback function to be called when an error occurs"""
        self.error_callbacks.append(callback)

    def on_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        # Skip empty messages
        if not message or message.isspace():
            return

        try:
            data = json.loads(message)
            if 'activities' in data and data['activities']:
                for activity in data['activities']:
                    # Only process messages from the bot
                    if activity.get('from', {}).get('id') != self.user_id and activity.get('type') == 'message':
                        # Stampa il messaggio ricevuto per debug
                        messageBox("Copilot", activity.get('text', ''))

                        # Notify all callbacks
                        for callback in self.message_callbacks:
                            callback(activity.get('text', ''))

                        # Imposta waiting_for_response a False per fermare l'animazione
                        self.waiting_for_response = False
                        print("Set waiting_for_response to False")

                    # Update watermark
                    if 'id' in activity:
                        self.watermark = activity['id'].split('|')[1]
        except json.JSONDecodeError:
            # Only log the error if it's not a heartbeat or empty message
            if message and len(message) > 2:  # Ignore likely heartbeat messages
                print("Error decoding message: ", message[:100] + "..." if len(message) > 100 else message)
        except Exception as e:
            print(f"Error processing message: {e}")
            for callback in self.error_callbacks:
                callback(str(e))

    def on_error(self, ws, error):
        print(f"WebSocket error: {error}")
        self.waiting_for_response = False
        for callback in self.error_callbacks:
            callback(str(error))

    def on_close(self, ws, close_status_code, close_msg):
        print("WebSocket connection closed")
        self.running = False
        self.waiting_for_response = False
        for callback in self.error_callbacks:
            callback("Connection closed")

    def on_open(self, ws):
        print("WebSocket connection established")
        self.running = True

    def start_conversation(self):
        """Initialize a new conversation and connect to WebSocket"""
        try:
            # Start a new conversation
            response = requests.post(self.url, headers=self.headers)
            if response.status_code != 201:
                error_msg = f"Error starting conversation: {response.status_code}"
                print(error_msg)
                for callback in self.error_callbacks:
                    callback(error_msg)
                return False

            conv_data = response.json()
            self.conversation_id = conv_data['conversationId']
            stream_url = conv_data.get('streamUrl')

            if not stream_url:
                error_msg = "No stream URL provided in the response"
                print(error_msg)
                for callback in self.error_callbacks:
                    callback(error_msg)
                return False

            print(f"Conversation started with ID: {self.conversation_id}")

            # Connect to WebSocket with ping interval to keep connection alive
            websocket.enableTrace(False)  # Disable verbose logging
            self.ws = websocket.WebSocketApp(
                stream_url,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                on_open=self.on_open
            )

            # Start WebSocket connection in a separate thread with ping interval
            self.ws_thread = threading.Thread(
                target=lambda: self.ws.run_forever(ping_interval=30, ping_timeout=10)
            )
            self.ws_thread.daemon = True
            self.ws_thread.start()

            # Wait for connection to establish
            timeout = 5
            start_time = time.time()
            while not self.running and time.time() - start_time < timeout:
                time.sleep(0.1)

            return self.running
        except Exception as e:
            error_msg = f"Error starting conversation: {e}"
            print(error_msg)
            for callback in self.error_callbacks:
                callback(error_msg)
            return False

    def send_message(self, text):
        """Send a message to the bot using REST API"""
        if not self.conversation_id:
            error_msg = "No active conversation"
            print(error_msg)
            for callback in self.error_callbacks:
                callback(error_msg)
            return False

        activity_url = f"{self.url}/{self.conversation_id}/activities"
        body = {
            "locale": "it-IT",
            "type": "message",
            "from": {
                "id": self.user_id
            },
            "text": text
        }

        try:
            # Set waiting flag
            self.waiting_for_response = True

            # Send the message
            response = requests.post(activity_url, headers=self.headers, json=body)
            if response.status_code != 200:
                error_msg = f"Error sending message: {response.status_code}"
                print(error_msg)
                for callback in self.error_callbacks:
                    callback(error_msg)
                self.waiting_for_response = False
                return False
            return True
        except Exception as e:
            error_msg = f"Error sending message: {e}"
            print(error_msg)
            for callback in self.error_callbacks:
                callback(error_msg)
            self.waiting_for_response = False
            return False

    def send_audio_message(self, audio_path=None, audio_data=None, message_id=None):
        """Send an audio message to the bot for speech-to-text processing"""
        # This would typically involve sending the audio file to a speech-to-text service
        # and then sending the resulting text to the bot
        # For now, we'll just send a placeholder message
        if not audio_path and not audio_data:
            print("No audio data provided")
            return False
        print("Audio data received")
        
        # Estrai l'ID del messaggio dal percorso del file se non fornito
        if not message_id and audio_path:
            # Prova a estrarre un ID dal nome del file audio
            filename = os.path.basename(audio_path)
            if filename.startswith('audio_'):
                message_id = 'audio_' + filename.split('_')[1].split('.')[0]
        
        # Avvia un thread separato per simulare l'elaborazione della trascrizione
        def transcription_thread(audio_path, message_id):
            # Attendi 3 secondi come richiesto
            time.sleep(3)
            
            # Qui in futuro si implementerà l'analisi STT reale
            # Per ora restituiamo un messaggio fisso come richiesto
            stt_text = "analisi audio STT completata"
            
            # Invia la trascrizione con l'ID del messaggio
            for callback in self.message_callbacks:
                callback(f"Trascrizione: {stt_text}", message_id)
        
        # Avvia il thread di trascrizione
        if audio_path:
            threading.Thread(target=transcription_thread, args=(audio_path, message_id)).start()
            return True
        
        if audio_data:
            # Here you would process the audio data in a similar thread
            # For now, we'll just send a placeholder message after delay
            def audio_data_thread(message_id):
                time.sleep(3)
                stt_text = "analisi audio STT completata"
                for callback in self.message_callbacks:
                    callback(f"Trascrizione: {stt_text}", message_id)
            
            threading.Thread(target=audio_data_thread, args=(message_id,)).start()
            return True

    def close(self):
        """Close the WebSocket connection"""
        if self.ws:
            self.ws.close()
            self.running = False
            if self.ws_thread and self.ws_thread.is_alive():
                self.ws_thread.join(timeout=1)


if __name__ == '__main__':
    from http.server import SimpleHTTPRequestHandler


    class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, directory=None, **kwargs):
            if directory is None:
                directory = os.getcwd()
            self.directory = directory
            super().__init__(*args, **kwargs)

        def end_headers(self):
            # Add CORS headers to allow requests from any origin
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            super().end_headers()

        def do_OPTIONS(self):
            # Handle preflight requests
            self.send_response(200)
            self.end_headers()


    def run_http_server(HTTP_PORT):
        """Run the HTTP server to serve the web interface"""
        # Change to the directory containing the HTML files
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        # Create and start the HTTP server
        httpd = socketserver.TCPServer(("localhost", HTTP_PORT), CustomHTTPRequestHandler)
        print(f"Serving HTTP on localhost port {HTTP_PORT} (http://localhost:{HTTP_PORT}/)")
        httpd.serve_forever()


    # Start the HTTP server in a separate thread
    http_thread = threading.Thread(target=run_http_server, args=(8000,))
    http_thread.daemon = True
    http_thread.start()

    print(f"Web interface available at http://localhost:{8000}/")
    print("Press Ctrl+C to exit")

    try:
        # Keep the main thread running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nServer terminated by user")
        sys.exit(0)
