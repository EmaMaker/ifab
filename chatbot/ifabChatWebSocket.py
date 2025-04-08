import json
import threading
import time

import requests
import websocket
from pyLib.util import *

# Add these imports at the top of your file
import os
import certifi

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
        print(f"WebSocket connection closed: code {close_status_code}, message: {close_msg}")
        self.running = False
        self.waiting_for_response = False
        # Non inviamo il messaggio di errore per chiusure normali (codice 1000 o 1001)
        if close_status_code is not None and close_status_code not in [1000, 1001]:
            for callback in self.error_callbacks:
                callback(f"Connection closed: {close_msg if close_msg else 'Unknown reason'}")

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
