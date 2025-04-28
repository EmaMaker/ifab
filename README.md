# IFAB Chatbot

Questo progetto implementa un sistema di chatbot interattivo per IFAB, progettato per fornire informazioni e interagire con un robot tramite un'interfaccia web, riconoscimento e sintesi vocale, e un sistema di visione.

## Installazione e Avvio Rapido

Per iniziare rapidamente, segui questi passaggi:

1.  **Setup Iniziale**: Esegui lo script `setup.sh` per installare tutte le dipendenze necessarie e configurare l'ambiente. Questo script rileva il sistema operativo, installa pacchetti di sistema, crea un ambiente virtuale Python 3.10.11 e installa le librerie Python richieste.

    ```bash
    # Esegui questo comando UNA SOLA VOLTA o quando le dipendenze cambiano
    ./setup.sh
    ```

2.  **Attivazione Ambiente e Avvio**: Prima di ogni utilizzo, attiva l'ambiente virtuale e avvia l'applicazione principale usando `start-chatbot.sh`. Questo script attiva l'ambiente virtuale (necessario per usare le dipendenze installate) e lancia `ifab.py`.

    ```bash
    # Esegui questo comando OGNI VOLTA che vuoi avviare il chatbot
    ./start-chatbot.sh
    ```

    Lo script `start-chatbot.sh` avvierà il server web backend e, una volta pronto, tenterà di aprire automaticamente l'interfaccia web nel browser predefinito all'indirizzo `http://localhost:8000`.

    **Uso Avanzato di `setup.sh`**:
    -   Lo script `setup.sh` non solo installa le dipendenze, ma attiva anche tutte le feature necessarie per l'ambiente di sviluppo.
    -   Se è necessario forzare una reinstallazione completa (ad esempio, se le librerie o le dipendenze sono cambiate), è possibile eseguire lo script con l'opzione `-f` o `--force`:
        ```bash
        ./setup.sh --force
        ```

> **NOTA**: È fondamentale eseguire `./setup.sh` la prima volta (o con `--force` se necessario). Per gli avvii successivi, usare sempre `./start-chatbot.sh` che si occupa anche di attivare l'ambiente corretto tramite `source ./setup.sh` al suo interno.

> **Icona Desktop (Linux)**: Su sistemi Linux compatibili, lo script `setup.sh` tenta di creare un collegamento `.desktop` sul desktop dell'utente. Questo collegamento permette di avviare l'applicazione IFAB Chatbot con un doppio clic, eseguendo automaticamente lo script `start-chatbot.sh`.

## Architettura del Sistema

Il sistema è composto dai seguenti sottosistemi principali, orchestrati dallo script `ifab.py`:

1.  **Chatbot Web (`chatbot/`)**: Fornisce l'interfaccia utente principale.
    *   **Frontend Web (`chatbot/web-client/`)**: Interfaccia HTML/CSS/JS con cui l'utente interagisce.
    *   **Backend Flask (`chatbot/flaskFrontEnd.py`)**: Server web basato su Flask che gestisce le richieste HTTP e la comunicazione WebSocket (`chatbot/ifabChatWebSocket.py`) per l'interazione in tempo reale.
    *   **Sintesi Vocale (TTS - Text-to-Speech) (`chatbot/chatLib/AudioPlayer.py`, `chatbot/tts-model/`)**: Utilizza `piper-tts` per convertire il testo delle risposte del chatbot in audio parlato.
    *   **Riconoscimento Vocale (STT - Speech-to-Text) (`chatbot/chatLib/WhisperListener.py`)**: Utilizza `WhisperX` per trascrivere l'audio catturato dal microfono dell'utente in testo, permettendo l'input vocale.

2.  **Sistema di Visione (`vision/`)**: Responsabile dell'analisi dell'ambiente tramite telecamere.
    *   **Gestione Telecamere e Rilevamento Marker (`vision/vision.py`)**: Utilizza OpenCV per acquisire immagini dalle telecamere collegate.
    *   **Test script per Rilevamento Aruco (`vision/Camera-test/arucoRead.py`)**: Identifica specifici marker Aruco nell'ambiente. Questi marker sono usati per localizzare posizioni di interesse (es. macchinari) e potenzialmente il robot stesso.
    *   **Calibrazione (`vision/Camera-test/generateIntrinsic.py`)**: Script e dati per calibrare le telecamere e ottenere matrici intrinseche, necessarie per una stima accurata della posizione 3D dei marker.
    *   **Generazione Marker (`vision/Camera-test/arucoMake.py`)**: Utilizza la libreria `aruco` di OpenCV per generare e salvare i marker Aruco in file PNG.

3.  **Controllo Robot (`ifab.py`, `robot/`)**: Gestisce la comunicazione e l'invio di comandi al robot fisico.
    *   **`RobotController` (classe in `ifab.py`)**: Mantiene lo stato più recente della posizione del robot e dei marker rilevati dal sistema di visione. Quando viene impostato un target (una macchina specifica identificata da un marker Aruco), `RobotController` invia periodicamente la posizione corrente del robot e la posizione del target al robot fisico tramite pacchetti UDP sulla rete locale (configurabile in `config.json`).
    *   **Firmware Robot (`robot/`)**: Contiene il codice sorgente (PlatformIO/C++) che gira sulla scheda di controllo del robot (probabilmente un ESP32 o simile). Questo codice riceve i pacchetti UDP da `ifab.py` e implementa la logica di navigazione per raggiungere il target specificato, controllando i motori.

4.  **Configurazione (`config.json`)**: File JSON che definisce parametri chiave come indirizzi IP, porte, configurazioni delle telecamere, e i target (macchine) riconosciuti con i loro ID marker Aruco associati.

## Configurazione (`config.json`)

Il file `config.json` contiene tutte le impostazioni specifiche dell'installazione e del comportamento del chatbot. Ecco una spiegazione delle sezioni principali:

-   **`url`**: L'endpoint del servizio Bot Framework Direct Line a cui connettersi.
-   **`auth`**: Il token di autenticazione (Bearer token) per il servizio Direct Line.
-   **`cameraIndex`**: L'indice della webcam da utilizzare per il sistema di visione (es. 0 per la prima webcam rilevata).
-   **`table`**: Definisce le proprietà del tavolo di lavoro.
    -   `width`, `height`: Dimensioni fisiche del tavolo in metri.
    -   `aruco`: Mappa gli ID dei marker ArUco agli angoli del tavolo (`top-left`, `top-right`, `bottom-left`, `bottom-right`). Questi marker sono usati per definire il sistema di coordinate del tavolo.
-   **`robot`**: Configurazione specifica del robot.
    -   `client_addr`, `client_port`: Indirizzo IP e porta per comunicare con il controller del robot.
    -   `aruco`: L'ID del marker ArUco posizionato sul robot stesso, usato per tracciarne la posizione e l'orientamento.
    -   `x_offset`, `y_offset`, `theta_offset`: Offset (in metri e gradi) tra il centro del marker ArUco del robot e il suo punto operativo effettivo (es. la punta di un attuatore).
-   **`workZone`** e **`macchinari`**: Definiscono le aree di lavoro e i macchinari presenti nell'ambiente. La struttura interna di ogni elemento in queste due sezioni è identica:
    -   `aruco`: L'ID del marker ArUco associato a quella zona o macchinario.
    -   `x_offset`, `y_offset`, `theta_offset`: Offset (in metri e gradi) rispetto al centro del marker ArUco per definire il punto di interesse specifico (es. il centro dell'area di lavoro o il punto di interazione con il macchinario).
    -   `text`: Il nome visualizzato nell'interfaccia utente.
    -   `img_path`: Il percorso dell'immagine associata, visualizzata nell'interfaccia. **Importante**: Questo percorso deve essere relativo alla directory principale del progetto (`ifab-chatbot`), poiché il server Flask serve i file statici da lì (es. `web-client/images/nome_immagine.jpg`).
    -   `say`: La frase che il robot pronuncerà quando gli viene chiesto di andare in quella zona o da quel macchinario.

    *Nota*: `workZone` e `macchinari` sono separati in due dizionari distinti principalmente per facilitare l'organizzazione e la visualizzazione nel front-end, permettendo di raggruppare logicamente le destinazioni.

## Script Principali

-   **`setup.sh`**: Script di installazione e configurazione dell'ambiente.
-   **`start-chatbot.sh`**: Script per attivare l'ambiente virtuale e avviare `ifab.py`.
-   **`ifab.py`**: Punto di ingresso principale dell'applicazione. Inizializza e coordina tutti i sottosistemi (Flask, Visione, RobotController).

## Dipendenze Chiave (Gestite da `setup.sh`)

-   **Python 3.10.11**: Versione specifica richiesta.
-   **Flask, Flask-SocketIO**: Per il backend web e WebSocket.
-   **WhisperX**: Per STT (richiede `ffmpeg` e potenzialmente CUDA/cuDNN su Linux per accelerazione GPU).
-   **piper-tts**: Per TTS.
-   **OpenCV (opencv-python)**: Per il sistema di visione.
-   **NumPy**: Per calcoli numerici (usato da OpenCV e altri).
-   **SoundDevice**: Per la riproduzione audio (TTS).

Per dettagli specifici sulla configurazione manuale (sconsigliata) o sui requisiti per sistemi operativi specifici (es. dipendenze NVIDIA per WhisperX su Linux), fare riferimento alle sezioni pertinenti nel file `README.md` originale o nel codice di `setup.sh`.