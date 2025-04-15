#!/bin/bash

# Script di setup per IFAB Chatbot
# Compatibile con bash e zsh

# Opzioni di default
FORCE_SETUP=false

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
        echo "Setup interrotto nella fase di creazione dell'ambiente virtuale. Assicurati di avere Python 3.10 installato"
        return 1
    fi
}

# Funzione per attivare l'ambiente virtuale
activate_venv() {
    echo "Attivazione dell'ambiente virtuale..."
    source .venv/bin/activate
    
    if [[ $? -ne 0 ]]; then
        echo "ERRORE: Impossibile attivare l'ambiente virtuale."
        echo "Setup interrotto nella fase di attivazione dell'ambiente virtuale."
        return 1
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
            echo "Setup interrotto nella fase di installazione di Python 3.10."
            return 1
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
            echo "Setup interrotto nella fase di installazione delle dipendenze di sistema."
            return 1
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
install_pip_dependencies() {
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
        echo "Setup interrotto nella fase di installazione delle dipendenze Python."
        return 1
    fi
}

# Funzione per verificare gli errori e interrompere l'esecuzione se necessario
check_error() {
    local exit_code=$1
    local error_message=$2
    
    if [[ $exit_code -ne 0 ]]; then
        echo "ERRORE: $error_message"
        echo "Setup interrotto."
        return 1
    fi
    return 0
}

# Funzione per mostrare l'help
show_help() {
    echo "Utilizzo: $0 [opzioni]"
    echo ""
    echo "Opzioni:"
    echo "  -f, --force    Forza la riesecuzione di tutti gli step di setup, anche se l'ambiente virtuale esiste già"
    echo "  -h, --help     Mostra questo messaggio di aiuto"
}

# Funzione principale
main() {
    # Parsing dei parametri
    while [[ $# -gt 0 ]]; do
        case $1 in
            -f|--force)
                FORCE_SETUP=true
                shift
                ;;
            -h|--help)
                show_help
                return 0
                ;;
            *)
                echo "Opzione non riconosciuta: $1"
                show_help
                return 1
                ;;
        esac
    done

    echo "=== Setup IFAB Chatbot ==="
    
    # Verifica se l'ambiente virtuale esiste
    if check_venv && [[ "$FORCE_SETUP" == "false" ]]; then
        echo "Ambiente virtuale esistente trovato."
        activate_venv
        check_error $? "Impossibile attivare l'ambiente virtuale esistente." || return 1
    else
        if [[ "$FORCE_SETUP" == "false" ]]; then
            echo "Ambiente virtuale non trovato."
        else
            echo "Ambiente virtuale esistente trovato, ma l'opzione --force è attiva."
            echo "Procedendo con la reinstallazione completa..."
        fi
        # Installa Python 3.10 se necessario
        install_python
        check_error $? "Installazione di Python 3.10 fallita." || return 1
        
        # Installa le dipendenze di sistema
        install_system_dependencies
        check_error $? "Installazione delle dipendenze di sistema fallita." || return 1
        
        create_venv
        check_error $? "Creazione dell'ambiente virtuale fallita." || return 1
        
        activate_venv
        check_error $? "Attivazione dell'ambiente virtuale fallita." || return 1
        
        install_pip_dependencies
        check_error $? "Installazione delle dipendenze Python fallita." || return 1

        echo "Setup completato. Si suggeriesce di attivare anche l'argcomplete globale (avrà effetto dal prossimo riavvio):"
        echo "└─▶ $ activate-global-python-argcomplete"
    fi
    
    echo "Setup completato. L'ambiente virtuale è attivo."
    echo ""
    echo "Per avviare il chatbot, esegui:"
    echo "└─▶ $ python chatbot/flaskFrontEnd.py"
    return 0
}

# Esegui la funzione principale con tutti i parametri passati allo script
main "$@"