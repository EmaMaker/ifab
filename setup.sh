#!/bin/bash

# Script di setup per IFAB Chatbot
# Compatibile con bash e zsh

# Funzione per rilevare il sistema operativo
detect_os() {
    if [[ "$(uname)" == "Darwin" ]]; then
        echo "macos"
    elif [[ -f /etc/arch-release ]]; then
        echo "arch"
    elif [[ -f /etc/lsb-release ]]; then
        echo "ubuntu"
    else
        echo "unknown"
    fi
}

# Funzione per verificare la presenza di GPU NVIDIA
check_nvidia_gpu() {
    echo "Verificando la presenza di GPU NVIDIA..."
    
    if command -v nvidia-smi &> /dev/null; then
        echo "GPU NVIDIA rilevata tramite nvidia-smi."
        return 0
    elif command -v lspci &> /dev/null && lspci | grep -i nvidia &> /dev/null; then
        echo "GPU NVIDIA rilevata tramite lspci."
        return 0
    else
        echo "Nessuna GPU NVIDIA rilevata."
        return 1
    fi
}

# Funzione per verificare se l'ambiente virtuale esiste
check_venv() {
    if [[ -d ".venv" ]]; then
        return 0
    else
        return 1
    fi
}

# Funzione per creare l'ambiente virtuale
create_venv() {
    echo "Creazione dell'ambiente virtuale Python..."
    
    # Verifica se python3.10 è disponibile
    if command -v python3.10 &> /dev/null; then
        python3.10 -m venv .venv
    else
        # Fallback a python3 con specifica della versione
        python3 -m venv .venv --python=python3.10
    fi
    
    if [[ $? -ne 0 ]]; then
        echo "ERRORE: Impossibile creare l'ambiente virtuale. Assicurati di avere Python 3.10 installato."
        exit 1
    fi
}

# Funzione per attivare l'ambiente virtuale
activate_venv() {
    echo "Attivazione dell'ambiente virtuale..."
    source .venv/bin/activate
    
    if [[ $? -ne 0 ]]; then
        echo "ERRORE: Impossibile attivare l'ambiente virtuale."
        exit 1
    fi
}

# Funzione per installare Python 3.10
install_python() {
    echo "Verificando l'installazione di Python 3.10..."
    
    OS=$(detect_os)
    
    if ! command -v python3.10 &> /dev/null; then
        echo "Installazione di Python 3.10..."
        if [[ "$OS" == "macos" ]]; then
            brew install python@3.10
        elif [[ "$OS" == "arch" ]]; then
            sudo pacman -S python310
        elif [[ "$OS" == "ubuntu" ]]; then
            sudo apt update
            sudo apt install software-properties-common -y
            sudo add-apt-repository ppa:deadsnakes/ppa -y
            sudo apt update
            sudo apt install python3.10 python3.10-venv python3.10-dev -y
        else
            echo "AVVISO: Sistema operativo non riconosciuto. Installare Python 3.10 manualmente."
            exit 1
        fi
    else
        echo "Python 3.10 è già installato."
    fi
}

# Funzione per installare le dipendenze di sistema
install_system_dependencies() {
    echo "Installazione delle dipendenze di sistema..."
    
    OS=$(detect_os)
    HAS_NVIDIA=$(check_nvidia_gpu && echo "true" || echo "false")
    
    if [[ "$OS" == "macos" ]]; then
        # Su macOS, verifica se Homebrew è installato
        if ! command -v brew &> /dev/null; then
            echo "Homebrew non è installato."
            echo "Per installare le dipendenze di sistema su macOS, si consiglia di installare Homebrew:"
            echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            exit 1
        fi
        echo "Installazione di ffmpeg tramite Homebrew..."
        brew install ffmpeg
    elif [[ "$OS" == "arch" ]]; then
        # Su Arch Linux
        echo "Installazione delle dipendenze di sistema su Arch Linux..."
        sudo pacman -S ffmpeg --noconfirm
        
        if [[ "$HAS_NVIDIA" == "true" ]]; then
            echo "Installazione delle dipendenze NVIDIA su Arch Linux..."
            sudo pacman -S cuda cudnn nvtop nvidia-drivers --noconfirm
        fi
    elif [[ "$OS" == "ubuntu" ]]; then
        # Su Ubuntu
        echo "Installazione delle dipendenze di sistema su Ubuntu..."
        sudo apt update
        sudo apt install ffmpeg -y
        
        if [[ "$HAS_NVIDIA" == "true" ]]; then
            echo "Installazione delle dipendenze NVIDIA su Ubuntu..."
            sudo apt install nvidia-cuda-toolkit nvidia-cudnn -y
        fi
    else
        echo "AVVISO: Sistema operativo non riconosciuto. Installare le dipendenze manualmente."
        echo "        ffmpeg, nvidia-cuda-toolkit, nvidia-cudnn, nvtop nvidia-drivers"
    fi
}

# Funzione per installare le dipendenze Python
install_dependencies() {
    echo "Installazione delle dipendenze Python..."
    
    # Installa le dipendenze Python (indipendente dal sistema operativo)
    pip install -r requirements.txt
    
    # Configura LD_LIBRARY_PATH per le librerie NVIDIA se necessario
    if check_nvidia_gpu; then
        CUDNN_PATH="$VIRTUAL_ENV/lib/python3.10/site-packages/nvidia/cudnn/lib"
        if [[ -d "$CUDNN_PATH" ]]; then
            export LD_LIBRARY_PATH="$CUDNN_PATH"
            echo "export LD_LIBRARY_PATH=\"$CUDNN_PATH\"" >> "$VIRTUAL_ENV/bin/activate"
            echo "Configurato LD_LIBRARY_PATH per le librerie NVIDIA"
        fi
    fi
    
    if [[ $? -ne 0 ]]; then
        echo "ERRORE: Impossibile installare le dipendenze."
        exit 1
    fi
    
    if [[ $? -ne 0 ]]; then
        echo "ERRORE: Impossibile installare le dipendenze."
        exit 1
    fi
}

# Funzione principale
main() {
    echo "=== Setup IFAB Chatbot ==="
    
    # Installa Python 3.10 se necessario
    install_python
    
    # Installa le dipendenze di sistema
    install_system_dependencies
    
    # Verifica se l'ambiente virtuale esiste
    if check_venv; then
        echo "Ambiente virtuale esistente trovato."
        activate_venv
    else
        echo "Ambiente virtuale non trovato."
        create_venv
        activate_venv
        install_dependencies
    fi
    
    echo "Setup completato. L'ambiente virtuale è attivo."
    echo "Per avviare il chatbot, esegui: python chatbot/flaskFrontEnd.py"
}

# Esegui la funzione principale
main