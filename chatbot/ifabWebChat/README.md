# IFAB Web Chat

Un'interfaccia web locale che permette di scrivere o registrare messaggi vocali da inviare al bot IFAB, sfruttando le sue capacità di Speech to Text.

## Caratteristiche

- Interfaccia web responsive e moderna
- Supporto per l'invio di messaggi testuali
- Registrazione di messaggi audio tramite microfono
- Comunicazione in tempo reale tramite WebSocket
- Integrazione con il bot IFAB tramite Direct Line API

## Struttura del Progetto

- `app.py`: Server Flask che gestisce le richieste HTTP e WebSocket
- `server.py`: Implementazione della comunicazione con il bot tramite WebSocket
- `index.html`: Interfaccia utente web

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
- In questa versione, la conversione speech-to-text non è ancora completamente implementata

## Sviluppi futuri

- Implementare la conversione speech-to-text completa
- Aggiungere supporto per la sintesi vocale delle risposte del bot
- Migliorare la gestione degli errori e la resilienza della connessione
- Aggiungere supporto per l'invio di immagini e altri tipi di media