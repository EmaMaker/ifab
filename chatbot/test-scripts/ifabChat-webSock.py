import websocket
import json

def on_message(ws, message):
    print("Copilot: ", message)

def on_error(ws, error):
    print("Errore: ", error)

def on_close(ws):
    print("Connessione chiusa")

def on_open(ws):
    print("Connessione aperta")
    # Invia il primo messaggio
    query = {
        "query": "Il tuo messaggio qui",
        "session_id": session_id  # Includi l'identificatore di sessione
    }
    ws.send(json.dumps(query))

session_id = str(uuid.uuid4())
ws = websocket.WebSocketApp("wss://api.copilotstudio.com/agent",
                            on_message=on_message,
                            on_error=on_error,
                            on_close=on_close)
ws.on_open = on_open
ws.run_forever()