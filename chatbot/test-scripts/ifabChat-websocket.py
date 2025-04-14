import json
import sys
import threading
import time
from enum import Enum, auto
from textwrap import TextWrapper

import requests
import websocket

# Configuration
url = "https://europe.directline.botframework.com/v3/directline/conversations"
headers = {
    "Authorization": "Bearer Ec99xFUkF1i7cR8m5TLtPokIlKXvLNdCxIYyDsraweBmf2zltwUZJQQJ99BCACi5YpzAArohAAABAZBSECEz.IpVjYOfmWMOQOHYGdH4G16pGKUArN1pEpAGJebfBjSrKI71E6ZhDJQQJ99BCACi5YpzAArohAAABAZBSMCrh",
    "Content-Type": "application/json"
}

wrapper = TextWrapper(width=150)
USER_ID = "user1"  # User ID for the conversation


class StyleBox(Enum):
    Double = auto()  # ══════════
    Light = auto()  # ─────────
    Bold = auto()  # ━━━━━━━━━━━
    Dash_Bold = auto()  # ┅┅┅┅┅┅┅┅┅┅
    Dash_Light = auto()  # ┄┄┄┄┄┄┄┄┄┄


"""
@:param string: String, with multiple line, to wrap inside a box
@:param style: List with 6 element with the style block, if not chosen, use the default 
"""


def create_box(string, styleName: StyleBox = StyleBox.Double) -> str:
    match styleName:
        case StyleBox.Double:
            corner = ("╔", "╗", "╚", "╝", "═", "║")
        case StyleBox.Bold:
            corner = ("┏", "┓", "┗", "┛", "━", "┃")
        case StyleBox.Light:
            corner = ("┌", "┐", "└", "┘", "─", "│")
        case StyleBox.Dash_Bold:
            corner = ("┏", "┓", "┗", "┛", "┅", "┇")
        case StyleBox.Dash_Light:
            corner = ("╭", "╮", "╰", "╯", "┄", "┆")
        case _:
            corner = ("╔", "╗", "╚", "╝", "═", "║")
    lines = string.replace("\t", "  ").splitlines()
    max_length = max(map(len, lines))
    box_width = max_length + 4
    # Draw box
    box = corner[0] + corner[4] * (box_width - 2) + corner[1] + "\n"
    box += "\n".join([f"{corner[5]} {line.ljust(max_length)} {corner[5]}" for line in lines])
    box += "\n" + corner[2] + corner[4] * (box_width - 2) + corner[3]
    return box


class IfabChatWebSocket:
    def __init__(self):
        self.conversation_id = None
        self.ws = None
        self.ws_thread = None
        self.running = False
        self.watermark = None
        self.waiting_for_response = False
        self.animation_thread = None
        self.stop_animation = False

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
                    if activity.get('from', {}).get('id') != USER_ID and activity.get('type') == 'message':
                        # Stop the animation before printing the response
                        self.stop_animation = True
                        if self.animation_thread and self.animation_thread.is_alive():
                            self.animation_thread.join()

                        # Clear the current line and print the bot's response
                        sys.stdout.write('\r' + ' ' * 50 + '\r')
                        messageBox("Copilot response:", activity.get('text', ''))
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

    def on_error(self, ws, error):
        print(f"WebSocket error: {error}")
        self.waiting_for_response = False

    def on_close(self, ws, close_status_code, close_msg):
        print("WebSocket connection closed")
        self.running = False
        self.waiting_for_response = False

    def on_open(self, ws):
        print("WebSocket connection established")
        self.running = True

    def start_conversation(self):
        """Initialize a new conversation and connect to WebSocket"""
        try:
            # Start a new conversation
            response = requests.post(url, headers=headers)
            if response.status_code != 201:
                print(f"Error starting conversation: {response.status_code}")
                return False

            conv_data = response.json()
            self.conversation_id = conv_data['conversationId']
            stream_url = conv_data.get('streamUrl')

            if not stream_url:
                print("No stream URL provided in the response")
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
            print(f"Error starting conversation: {e}")
            return False

    def send_message(self, text):
        """Send a message to the bot using REST API"""
        if not self.conversation_id:
            print("No active conversation")
            return False

        activity_url = f"{url}/{self.conversation_id}/activities"
        body = {
            "locale": "it-IT",
            "type": "message",
            "from": {
                "id": USER_ID
            },
            "text": text
        }

        try:
            # Set waiting flag and start animation
            self.waiting_for_response = True
            self.stop_animation = False
            self.animation_thread = threading.Thread(target=self.show_loading_animation)
            self.animation_thread.daemon = True
            self.animation_thread.start()

            # Send the message
            response = requests.post(activity_url, headers=headers, json=body)
            if response.status_code != 200:
                self.stop_animation = True
                print(f"\nError sending message: {response.status_code}")
                self.waiting_for_response = False
                return False
            return True
        except Exception as e:
            self.stop_animation = True
            print(f"Error sending message: {e}")
            self.waiting_for_response = False
            return False

    def show_loading_animation(self):
        """Display a simple loading animation while waiting for a response"""
        animation = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        i = 0
        while not self.stop_animation and self.waiting_for_response:
            sys.stdout.write('\r' + animation[i % len(animation)] + ' In attesa di risposta...')
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1

    def close(self):
        """Close the WebSocket connection"""
        self.stop_animation = True
        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join(timeout=1)

        if self.ws:
            self.ws.close()
            self.running = False
            if self.ws_thread and self.ws_thread.is_alive():
                self.ws_thread.join(timeout=1)


if __name__ == '__main__':
    chat = IfabChatWebSocket()

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
