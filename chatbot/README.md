# IFAB Web Chat

Un'interfaccia web locale che permette di scrivere o registrare messaggi vocali da inviare al bot IFAB, sfruttando le sue capacità di Speech to Text.

## Caratteristiche

- Interfaccia web responsive e moderna (pensata per 1 solo client)
- Supporto per l'invio di messaggi testuali
- Registrazione di messaggi audio tramite microfono
- Comunicazione in tempo reale tramite WebSocket
- Integrazione con il bot IFAB tramite Direct Line API
- Logica STT (Speech-to-Text) modulare e personalizzabile
- Caching locale delle librerie JavaScript per funzionamento offline
- Logica STT (Speech-to-Text) modulare e personalizzabile
- Caching locale delle librerie JavaScript per funzionamento offline

## Struttura del Progetto

- `flaskFrontEnd.py`: Server Flask che gestisce le richieste con il backend attraverso WebSocket
- `ifabChatWebSocket.py`: Implementazione della comunicazione con il bot tramite WebSocket
- `index.html`: Interfaccia utente web
- `script.js`: Logica JavaScript per la gestione dell'interfaccia e delle funzionalità audio
- `util.py`: Utility per la formattazione dei messaggi e altre funzioni di supporto
- `libs/`: Directory contenente le librerie JavaScript locali per il funzionamento offline

## Requisiti

```
flask
flask-cors
flask-socketio
requests
websocket-client
```

## Installazione

1. Assicurati di avere Python 3.6+ installato
2. Installa le dipendenze:

```bash
pip install flask flask-cors flask-socketio requests websocket-client
```

## Utilizzo

1. Avvia il server Flask:

```bash
python flaskFrontEnd.py
```

2. Apri un browser e vai all'indirizzo: http://localhost:8000

3. Ora puoi:
    - Digitare un messaggio e premere invio o il pulsante di invio
    - Cliccare sul pulsante del microfono per registrare un messaggio vocale

## Note sull'implementazione

- La comunicazione con il bot avviene tramite Direct Line API di Microsoft Bot Framework
- I messaggi audio vengono registrati in formato WAV
- Implementazione modulare dell'STT che permette di sostituire facilmente il sistema di trascrizione
- Caching locale delle librerie JavaScript (socket.io.min.js, marked.min.js) per garantire il funzionamento anche in assenza di connessione internet
- Sistema di fallback automatico per le librerie JavaScript: prima tenta di caricare da CDN, poi utilizza le versioni locali se necessario

## Sviluppi futuri

- Migliorare ulteriormente la conversione speech-to-text
- Aggiungere supporto per la sintesi vocale delle risposte del bot
- Migliorare la gestione degli errori e la resilienza della connessione
- Implementare un sistema di cache per le risposte del bot

## Funzionamento dei blocchi `if __name__ == "__main__"`

### In `flaskFrontEnd.py`

Quando eseguito direttamente (`python flaskFrontEnd.py`), questo blocco:

- Configura e avvia il server Flask con SocketIO
- Accetta parametri da linea di comando per host e porta
- Inizializza la connessione con il bot IFAB
- Configura i pulsanti statici dell'interfaccia

```python
if __name__ == '__main__':
    # Parsing degli argomenti da linea di comando
    # Inizializzazione della connessione al bot
    # Configurazione dei pulsanti dell'interfaccia
    # Avvio del server Flask con SocketIO
```

### In `ifabChatWebSocket.py`

Quando eseguito direttamente, questo blocco:

- Crea un'istanza della classe IfabChatWebSocket
- Avvia una sessione di chat testuale in modalità console
- Utile per testare la connessione con il bot senza l'interfaccia web

```python
if __name__ == '__main__':
    # Inizializzazione della connessione al bot
    # Avvio di una sessione di chat testuale in console
```

Questi blocchi permettono ai file di funzionare sia come moduli importabili che come script eseguibili direttamente, facilitando lo sviluppo e il testing dei componenti in modo
indipendente.
