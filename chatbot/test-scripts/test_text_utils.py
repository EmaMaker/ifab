# -*- coding: utf-8 -*-

import sys
import os
chatbotDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
sys.path.append(chatbotDir)
from pyLib.text_utils import clean_markdown_for_tts
from pyLib.AudioPlayer import AudioPlayer

# Testo di esempio simile a quello fornito dall'utente
test_text = '''Non posso formattare il testo in **grassetto** o *corsivo*. Tuttavia, posso elencare le parti della Roland: 
- Cavo di alimentazione
- Lama
- Portalama
- Perno
- Coltello di separazione
- Materiale per prove di taglio
- Adattatore di corrente
- Base del rullo
lista:
1. CD-ROM
2. Nastro per applicazione
3. Manuale Utente
4. Cavo USB
5. Pinzette

# Codice 1
## codice 2
codice bash:
```bash
asd
ads
asd
```
---

ecco il link: [ciao](url)

[1]
[1]: cite:1 "Citation-1"'''

print('\nTesto originale:\n', test_text)
print('\nTesto pulito per TTS:\n', clean_markdown_for_tts(test_text))
player = AudioPlayer(os.path.join(chatbotDir, "tts-model", "it_IT-paola-medium.onnx"))
player.play_text(clean_markdown_for_tts(test_text))
player.waitEndBuffer()
