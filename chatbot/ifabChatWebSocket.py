import json
# Add these imports at the top of your file
import os
import random
import threading
import time

import certifi
import requests
import websocket

from pyLib.util import *

# Add this line near the beginning of your code, before any network requests
os.environ['SSL_CERT_FILE'] = certifi.where()


class IfabChatWebSocket:
    """ Class to manage WebSocket connection to the Ifab Chatbot API and the backend"""

    def __init__(self, url, auth_token, user_id="user1"):
        # Connection parameters
        self.url = url
        self.headers = {
            "Authorization": auth_token,
            "Content-Type": "application/json"
        }
        self.user_id = user_id
        # State variables
        self.conversation_id = None
        self.ws = None
        self.ws_thread = None
        self.running = False
        self.watermark = None
        self.waiting_for_response = False
        self.message_callbacks = []
        self.error_callbacks = []
        # Reconnection parameters
        self.max_retries = 5
        self.base_delay = 1  # Base delay in seconds
        self.max_delay = 30  # Maximum delay in seconds
        self.retry_count = 0
        self.reconnecting = False

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
                    if activity.get('from', {}).get('id') != self.user_id and activity.get('type') == 'message' and activity.get('text') is not None:
                        # Stampa il messaggio ricevuto per debug
                        messageBox("Copilot", activity.get('text', 'no-text'))

                        # Notify all callbacks
                        for callback in self.message_callbacks:
                            callback(activity.get('text', ''))

                        # Imposta waiting_for_response a False per fermare l'animazione
                        self.waiting_for_response = False

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
        messageBox("WebSocket", f"Connessione chiusa: codice {close_status_code}, messaggio: {close_msg}", StyleBox.Light)
        self.running = False
        self.waiting_for_response = False

        # Non tentiamo di riconnetterci per chiusure normali (codice 1000 o 1001)
        if close_status_code is not None and close_status_code not in [1000, 1001]:
            # Notifica l'utente del problema
            for callback in self.error_callbacks:
                callback(f"Connessione interrotta: {close_msg if close_msg else 'Motivo sconosciuto'}")

            # Avvia un tentativo di riconnessione in un thread separato
            if not self.reconnecting:
                self.reconnecting = True
                threading.Thread(target=self._reconnect).start()

    def _reconnect(self):
        """Attempt to reconnect to the WebSocket after a connection failure"""
        messageBox("WebSocket", "Tentativo di riconnessione automatica...", StyleBox.Light)
        # Breve pausa prima di tentare la riconnessione
        time.sleep(1)
        self.start_conversation()

    def on_open(self, ws):
        print("WebSocket connection established")
        self.running = True

    def start_conversation(self):
        """Initialize a new conversation and connect to WebSocket with retry mechanism"""
        # Reset retry count if this is not a reconnection attempt
        if not self.reconnecting:
            self.retry_count = 0

        while self.retry_count < self.max_retries:
            try:
                # If we're retrying, add a delay with exponential backoff
                if self.retry_count > 0:
                    # Calculate delay with jitter to prevent thundering herd problem
                    delay = min(self.base_delay * (2 ** (self.retry_count - 1)) + random.uniform(0, 1), self.max_delay)
                    messageBox("Riconnessione", f"Tentativo {self.retry_count}/{self.max_retries} - Attesa di {delay:.1f} secondi", StyleBox.Light)
                    time.sleep(delay)

                # Start a new conversation
                messageBox("Connessione", f"Tentativo di connessione a {self.url}", StyleBox.Light)
                response = requests.post(self.url, headers=self.headers, timeout=30)  # Add explicit timeout

                if response.status_code != 201:
                    error_msg = f"Error starting conversation: HTTP {response.status_code}"
                    print(error_msg)
                    # Increment retry count and try again
                    self.retry_count += 1
                    continue

                conv_data = response.json()
                self.conversation_id = conv_data['conversationId']
                stream_url = conv_data.get('streamUrl')

                if not stream_url:
                    error_msg = "No stream URL provided in the response"
                    print(error_msg)
                    self.retry_count += 1
                    continue

                messageBox("Connessione", f"Conversazione avviata con ID: {self.conversation_id}", StyleBox.Light)

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

                if self.running:
                    # Reset retry count on successful connection
                    self.retry_count = 0
                    self.reconnecting = False
                    return True
                else:
                    # Connection didn't establish within timeout
                    error_msg = "WebSocket connection timed out"
                    print(error_msg)
                    self.retry_count += 1
                    continue

            except requests.exceptions.ConnectTimeout as e:
                error_msg = f"Timeout durante la connessione: {e}"
                messageBox("Errore Connessione", error_msg, StyleBox.Dash_Bold)
                self.retry_count += 1
                continue

            except requests.exceptions.ConnectionError as e:
                error_msg = f"Errore di connessione: {e}"
                messageBox("Errore Connessione", error_msg, StyleBox.Dash_Bold)
                self.retry_count += 1
                continue

            except Exception as e:
                error_msg = f"Errore durante l'avvio della conversazione: {e}"
                messageBox("Errore", error_msg, StyleBox.Dash_Bold)
                self.retry_count += 1
                continue

        # If we've exhausted all retries
        self.reconnecting = False
        error_msg = f"Impossibile connettersi dopo {self.max_retries} tentativi"
        messageBox("Errore Connessione", error_msg, StyleBox.Error)
        for callback in self.error_callbacks:
            callback(error_msg)
        return False

    def send_message(self, text):
        """Send a message to the bot using REST API with retry mechanism"""
        if not self.conversation_id:
            error_msg = "Nessuna conversazione attiva"
            messageBox("Errore", error_msg, StyleBox.Dash_Bold)

            # Tenta di riavviare la conversazione
            messageBox("Riconnessione", "Tentativo di riavvio della conversazione...", StyleBox.Light)
            if not self.start_conversation():
                for callback in self.error_callbacks:
                    callback(error_msg)
                return False

            # Se la riconnessione ha avuto successo, continua con l'invio del messaggio
            messageBox("Riconnessione", "Riconnessione riuscita, invio messaggio...", StyleBox.Light)

        activity_url = f"{self.url}/{self.conversation_id}/activities"
        body = {
            "locale": "it-IT",
            "type": "message",
            "from": {
                "id": self.user_id
            },
            "text": text
        }

        # Imposta un contatore di tentativi per l'invio del messaggio
        send_retries = 0
        max_send_retries = 3

        while send_retries < max_send_retries:
            try:
                # Set waiting flag
                self.waiting_for_response = True

                # Send the message with timeout
                messageBox("Invio", f"Invio messaggio (tentativo {send_retries + 1}/{max_send_retries})...", StyleBox.Light)
                response = requests.post(activity_url, headers=self.headers, json=body, timeout=30)

                if response.status_code != 200:
                    error_msg = f"Errore nell'invio del messaggio: HTTP {response.status_code}"
                    messageBox("Errore", error_msg, StyleBox.Dash_Bold)
                    send_retries += 1

                    # Se è un errore di autenticazione o autorizzazione, tenta di riavviare la conversazione
                    if response.status_code in [401, 403]:
                        messageBox("Riconnessione", "Tentativo di riavvio della conversazione per errore di autenticazione...", StyleBox.Light)
                        if self.start_conversation():
                            # Aggiorna l'URL dell'attività con il nuovo ID conversazione
                            activity_url = f"{self.url}/{self.conversation_id}/activities"
                            continue

                    # Attendi prima di riprovare
                    if send_retries < max_send_retries:
                        time.sleep(2 * send_retries)  # Backoff lineare
                    continue

                # Messaggio inviato con successo
                return True

            except requests.exceptions.Timeout:
                error_msg = "Timeout durante l'invio del messaggio"
                messageBox("Errore", error_msg, StyleBox.Dash_Bold)
                send_retries += 1
                if send_retries < max_send_retries:
                    time.sleep(2 * send_retries)
                continue

            except requests.exceptions.ConnectionError as e:
                error_msg = f"Errore di connessione durante l'invio: {e}"
                messageBox("Errore", error_msg, StyleBox.Dash_Bold)

                # Tenta di riavviare la conversazione
                if self.start_conversation():
                    # Aggiorna l'URL dell'attività con il nuovo ID conversazione
                    activity_url = f"{self.url}/{self.conversation_id}/activities"
                    send_retries += 1
                    if send_retries < max_send_retries:
                        time.sleep(2 * send_retries)
                    continue
                else:
                    # Se la riconnessione fallisce, interrompi i tentativi
                    break

            except Exception as e:
                error_msg = f"Errore durante l'invio del messaggio: {e}"
                messageBox("Errore", error_msg, StyleBox.Dash_Bold)
                send_retries += 1
                if send_retries < max_send_retries:
                    time.sleep(2 * send_retries)
                continue

        # Se arriviamo qui, tutti i tentativi sono falliti
        self.waiting_for_response = False
        error_msg = f"Impossibile inviare il messaggio dopo {max_send_retries} tentativi"
        messageBox("Errore", error_msg, StyleBox.Dash_Bold)
        for callback in self.error_callbacks:
            callback(error_msg)
        return False

    def stop_conversation(self):
        """Terminate the current conversation with the bot and reset all variables"""
        # Close the WebSocket connection
        if self.ws:
            self.ws.close()
            self.running = False
            if self.ws_thread and self.ws_thread.is_alive():
                self.ws_thread.join(timeout=1)

        # Reset all state variables
        self.conversation_id = None
        self.ws = None
        self.ws_thread = None
        self.watermark = None
        self.waiting_for_response = False

        print("Conversation stopped and variables reset")
        return True

    def close(self):
        """Close the WebSocket connection"""
        if self.ws:
            self.ws.close()
            self.running = False
            if self.ws_thread and self.ws_thread.is_alive():
                self.ws_thread.join(timeout=1)


if __name__ == '__main__':

    # Inizializza il client WebSocket per la comunicazione con il bot
    # Token Bot Ema:
    # url = "https://europe.directline.botframework.com/v3/directline/conversations"
    # auth = "Bearer Ec99xFUkF1i7cR8m5TLtPokIlKXvLNdCxIYyDsraweBmf2zltwUZJQQJ99BCACi5YpzAArohAAABAZBSECEz.IpVjYOfmWMOQOHYGdH4G16pGKUArN1pEpAGJebfBjSrKI71E6ZhDJQQJ99BCACi5YpzAArohAAABAZBSMCrh"
    # Token Bot Fondazione:
    url = "https://europe.directline.botframework.com/v3/directline/conversations"
    auth = "Bearer BI91xBzzXppQiRxyBjniBLPFctD8IGqIR0BCmQCyODxSZrZjLX7QJQQJ99BDACi5YpzAArohAAABAZBS4vKQ.DEsKhbDDeYsTi7cHcOgSMV4HrdEnNrJAPp8hTnCv55nxFqtKRfonJQQJ99BDACi5YpzAArohAAABAZBS4AHw"

    chat = IfabChatWebSocket(url, auth, user_id="user1")

    if not chat.start_conversation():
        print("Failed to start conversation")
        exit(1)

    try:
        print("Chat started. Type 'exit', 'quit', or 'esci' to end the conversation.")
        while True:
            if not chat.running:
                print("WebSocket connection lost. Attempting to reconnect...")
                if not chat.start_conversation():
                    print("Failed to reconnect")
                    break
            # Only show the input prompt when not waiting for a response
            if not chat.waiting_for_response:
                user_input = input("Tu: ")

                if user_input.lower() in ["exit", "quit", "esci"]:
                    break

                if not chat.send_message(user_input):
                    print("Failed to send message")
                    break
            else:
                # Small sleep to prevent CPU hogging in the loop
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nChat terminated by user")
    finally:
        chat.close()
        print("Chat session ended")
