#!/bin/bash

# Ottieni il percorso assoluto della directory dello script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$SCRIPT_DIR/setup.sh"

# Avvia il browser dopo 5 secondi per dare tempo al backend di avviarsi
{
  sleep 10 # Attendi che il server sia pronto
  # Apri il browser
  xdg-open http://localhost:8000
} &

python "$SCRIPT_DIR/chatbot/flaskFrontEnd.py"
