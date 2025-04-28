#!/bin/bash

# Ottieni il percorso assoluto della directory dello script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$SCRIPT_DIR/setup.sh"

# Avvia il browser quando il backend è pronto
{
  echo "Attendo che la welcome-page del server sia pronta..."
  TIMEOUT=30
  ELAPSED=0
  while ! curl -s http://localhost:8000 -o /dev/null -w "%{http_code}" | grep -q "200\|30[0-9]"; do
    sleep 1
    ELAPSED=$((ELAPSED+1))
    if [ $ELAPSED -ge $TIMEOUT ]; then
      echo "Timeout: il server non risponde dopo $TIMEOUT secondi"
      exit 1
    fi
    echo -n "."
  done
  echo -e "\nServer pronto! Apro il browser..."

  # Rileva il sistema operativo e apri il browser appropriatamente
  if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open http://localhost:8000
  else
    # Linux e altri sistemi
    xdg-open http://localhost:8000
  fi
} &

python "$SCRIPT_DIR/ifab.py"
