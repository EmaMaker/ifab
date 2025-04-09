Il nostro sito redbauble.dev non è indicizzato su motori di ricerca -> non posso usare il sito come knoledge base perché fa le ricerche su Bing e poi filtra per sito

Soluzione: `datasets-to-kb.sh` prende i file markdown del dataset di wikidocs e li trasforma in file markdown con nome directory.md, da caricare su Copilot Studio come knowledge
base.
Lo script richiede accedere al volume docker (quindi root). Wikidocs dà problemi quando il volume fa rifarimento a utente non root per qualche motivo.

# Usare bot con API python (Direct Line 3.0)

Il bot deve essere stato pubblicato https://learn.microsoft.com/en-us/microsoft-copilot-studio/publication-connect-bot-to-custom-application

https://learn.microsoft.com/en-us/microsoft-copilot-studio/publication-connect-bot-to-web-channels?tabs=preview

https://learn.microsoft.com/en-us/azure/bot-service/rest-api/bot-framework-rest-direct-line-3-0-api-reference?view=azure-bot-service-4.0

Il bot è regionale europe e non ho capito perché

## Aprire conversazione

POST https://directline.botframework.com/v3/directline/conversations

```
import requests

url_convopen = "https://europe.directline.botframework.com/v3/directline/conversations"

header = {"Authorization": 'Bearer Ec99xFUkF1i7cR8m5TLtPokIlKXvLNdCxIYyDsraweBmf2zltwUZJQQJ99BCACi5YpzAArohAAABAZBSECEz.IpVjYOfmWMOQOHYGdH4G16pGKUArN1pEpAGJebfBjSrKI71E6ZhDJQQJ99BCACi5YpzAArohAAABAZBSMCrh'}

r = requests.post(url_convopen, headers=header)
```

The part after Bearer is the SECRET from Agent>Settings>Security>Secret

## Mandare attività

```
body = """{
    "locale": "en-EN",
    "type": "message",
    "from": {
        "id": "user1"
    },
    "text": "hello"
}"""


header = {"Authorization": 'Bearer Ec99xFUkF1i7cR8m5TLtPokIlKXvLNdCxIYyDsraweBmf2zltwUZJQQJ99BCACi5YpzAArohAAABAZBSECEz.IpVjYOfmWMOQOHYGdH4G16pGKUArN1pEpAGJebfBjSrKI71E6ZhDJQQJ99BCACi5YpzAArohAAABAZBSMCrh', 'Content-Type': 'application/json'}

url_act = 'https://europe.directline.botframework.com/v3/directline/conversations/CONV-ID-FROM-CONVERSATION-OPEN/activities'
"

r = requests.post(url_act, headers=header, data=body)
```

The important part is data, instead of params

## Ricevere attività

Facilmente, via websockets con lo stream url contenuto nella risposta dell'apertura della conversazione

```python3 -m websockets URL```

## TTS Alfano

`python test-scripts/tts-compare.py --model ./tts-model/it_IT-paola-medium.onnx
`

