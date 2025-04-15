# IFAB Chatbot

> **IMPORTANTE**: Prima di utilizzare questo progetto, è necessario eseguire lo script `setup.sh` per installare o attivare tutte le dipendenze necessarie. Lo script si occupa automaticamente di rilevare il sistema operativo, installare le dipendenze di sistema, creare l'ambiente virtuale Python e configurare correttamente le librerie. Solo dopo aver eseguito questo passaggio è possibile avviare con tranquillità gli script del totem.
>
> ```bash
> # Eseguire questo comando prima di ogni utilizzo
> source ./setup.sh
> ```
>
> **NOTA**: È fondamentale utilizzare il comando `source` per eseguire lo script, in modo che l'ambiente virtuale venga attivato nella sessione corrente del terminale. Utilizzando `./setup.sh` l'ambiente virtuale verrebbe attivato solo all'interno dello script, senza effetto sul terminale corrente.

Questo progetto implementa un sistema di chatbot interattivo per IFAB, composto da diversi sottosistemi tra cui un'interfaccia web con supporto per sintesi vocale (TTS) e riconoscimento vocale (STT), un sistema di gestione delle telecamere e componenti robotici.

## Struttura del Progetto

Il progetto è organizzato nelle seguenti directory principali:

- `chatbot/`: Contiene l'implementazione del chatbot web e relativi script
  - `ifabWebChat/`: Interfaccia web del chatbot
  - `chatLib/`: Librerie Python di supporto
  - `test-scripts/`: Script di test per il chatbot
  - `tts-model/`: Modelli per la sintesi vocale (Text-to-Speech)
- `Camera-SubSystem/`: Sistema di gestione delle telecamere
- `robot/`: Componenti per il controllo robotico

## Requisiti da installare a mano (se setup.sh non viene eseguito)

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
- **WhisperX**: Riconoscimento vocale (Speech-to-Text)
- **OpenCV (opencv-python)**: Elaborazione delle immagini e gestione delle telecamere
- **NumPy, Matplotlib**: Elaborazione numerica e visualizzazione
- **SoundDevice**: Riproduzione audio

### Configurazione per il riconoscimento vocale (WhisperX)

Il sistema di riconoscimento vocale (STT) utilizza WhisperX, che richiede alcune configurazioni specifiche in base al sistema operativo:

#### Arch Linux (KDE)

Su Arch Linux, è necessario installare le seguenti dipendenze:

```bash
# Installazione delle dipendenze necessarie
sudo pacman -S ffmpeg cuda cudnn nvtop nvidia-drivers
```

Esempio di utilizzo:

```bash
whisperx --model large-v3 --compute_type float32 --language it chatbot/demo-wav/audio_20250411-143626.wav
```

#### Ubuntu

Su Ubuntu, l'installazione è ancora in fase di sviluppo (work in progress). Sono stati riscontrati alcuni problemi specifici che stiamo cercando di risolvere. È necessario configurare correttamente le librerie NVIDIA:

```bash
# Installazione delle dipendenze
sudo apt install ffmpeg

# Configurazione delle librerie NVIDIA (potrebbe richiedere adattamenti)
export LD_LIBRARY_PATH="$VIRTUAL_ENV/lib/python3.10/site-packages/nvidia/cudnn/lib"
```

#### macOS

Su macOS, il sistema funziona correttamente utilizzando Homebrew per installare le dipendenze, ma senza supporto NVIDIA. In questo caso, WhisperX utilizzerà automaticamente la CPU:

```bash
# Installazione delle dipendenze con Homebrew
brew install ffmpeg
```

Il modulo `WhisperListener.py` è in grado di rilevare automaticamente se la GPU non è disponibile e passare alla CPU.


## Avvio della demo Chatbot Web

Per avviare l'interfaccia web del chatbot:

```bash
python chatbot/flaskFrontEnd.py [opzioni]
```

### Opzioni disponibili

- `--host HOST`: Host del server (default: '0.0.0.0')
- `--port PORT`: Porta del server (default: '8000')
- `--tts_model TTS_MODEL`: Path al modello Piper-TTS (default: 'chatbot/tts-model/it_IT-paola-medium.onnx')
- `--stt_model STT_MODEL`: Nome del modello Whisper (default: 'large-v3')
- `--device DEVICE`: Dispositivo per eseguire il modello (cpu o cuda, default: 'cuda')
- `--language LANGUAGE`: Lingua dell'audio (default: 'it')
- `--batch_size BATCH_SIZE`: Dimensione del batch per l'elaborazione (default: '16')
- `--compute_type COMPUTE_TYPE`: Tipo di calcolo (float32 o int8, default: 'float32')

## Contribuire al Progetto

Per contribuire al progetto, si prega di seguire le convenzioni di codice esistenti e di testare accuratamente le modifiche prima di inviarle.

## Licenza

Consultare il file di licenza per informazioni sui diritti d'uso e distribuzione.