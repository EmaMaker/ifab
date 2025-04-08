# IFAB Chatbot

Questo progetto implementa un sistema di chatbot interattivo per IFAB, composto da diversi sottosistemi tra cui un'interfaccia web, un sistema di gestione delle telecamere e componenti robotici.

## Struttura del Progetto

Il progetto è organizzato nelle seguenti directory principali:

- `chatbot/`: Contiene l'implementazione del chatbot web e relativi script
  - `ifabWebChat/`: Interfaccia web del chatbot
  - `pyLib/`: Librerie Python di supporto
  - `test-scripts/`: Script di test per il chatbot
  - `tts-model/`: Modelli per la sintesi vocale (Text-to-Speech)
- `Camera-SubSystem/`: Sistema di gestione delle telecamere
- `robot/`: Componenti per il controllo robotico

## Requisiti

### Ambiente Python

**Nota importante**: Questo progetto è progettato per funzionare con **Python 3.10.11**. Si consiglia di utilizzare questa versione specifica per evitare problemi di compatibilità.

#### Creazione dell'ambiente virtuale

Si consiglia di utilizzare un ambiente virtuale Python per evitare conflitti tra dipendenze:

```bash
# Assicurarsi di avere Python 3.10.11 installato
# Creazione dell'ambiente virtuale
python3.10 -m venv .venv
# In alternativa, se python3.10 non è disponibile come comando
python3 -m venv .venv --python=python3.10

# Attivazione dell'ambiente virtuale
# Su macOS/Linux
source .venv/bin/activate
# Su Windows
# .venv\Scripts\activate
```

#### Installazione delle dipendenze Python

Il progetto richiede diverse librerie Python che possono essere installate utilizzando il file `requirements.txt`:

```bash
pip install -r requirements.txt
# macOS
pip install -r requirements.txt --no-deps
```

**Nota**: Su macOS potrebbero verificarsi problemi di dipendenza con alcune librerie. L'opzione `--no-deps` è consigliata poiché il file `requirements.txt` contiene già tutte le dipendenze necessarie.

**Importante**: Le dipendenze nel file `requirements.txt` sono ottimizzate per Python 3.10.11. L'utilizzo di altre versioni di Python potrebbe causare incompatibilità con alcune librerie.

### Principali dipendenze Python

Il progetto utilizza le seguenti librerie Python principali:

- **Flask, Flask-Cors, Flask-SocketIO**: Framework web per l'interfaccia del chatbot
- **Requests, Websocket-client**: Gestione delle richieste HTTP e WebSocket
- **Piper-tts**: Sintesi vocale (Text-to-Speech)
- **OpenCV (opencv-python)**: Elaborazione delle immagini e gestione delle telecamere
- **NumPy, Matplotlib**: Elaborazione numerica e visualizzazione
- **SoundDevice**: Riproduzione audio

### Dipendenze NPM

Il progetto utilizza anche alcune librerie JavaScript installate tramite npm:

- **marked**: Libreria per il parsing e la conversione di Markdown in HTML, utilizzata probabilmente per formattare i messaggi del chatbot.

Per installare le dipendenze npm:

```bash
npm install
```

## Avvio del Chatbot Web

Per avviare l'interfaccia web del chatbot:

```bash
cd chatbot/ifabWebChat
python flaskFrontEnd.py
```

## Contribuire al Progetto

Per contribuire al progetto, si prega di seguire le convenzioni di codice esistenti e di testare accuratamente le modifiche prima di inviarle.

## Licenza

Consultare il file di licenza per informazioni sui diritti d'uso e distribuzione.