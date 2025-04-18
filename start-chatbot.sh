#!/bin/bash

# Ottieni il percorso assoluto della directory dello script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$SCRIPT_DIR/setup.sh"

# Avvia il browser dopo 5 secondi per dare tempo al backend di avviarsi
{
  sleep 5 # Attendi che il server sia pronto
  # Rileva il sistema operativo e apri il browser appropriatamente
  if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open http://localhost:8000
  else
    # Linux e altri sistemi
    xdg-open http://localhost:8000
  fi
} &

python "$SCRIPT_DIR/chatbot/flaskFrontEnd.py"
