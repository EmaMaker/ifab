import time

import requests


url = "https://europe.directline.botframework.com/v3/directline/conversations"
headers = {
    "Authorization": "Bearer Ec99xFUkF1i7cR8m5TLtPokIlKXvLNdCxIYyDsraweBmf2zltwUZJQQJ99BCACi5YpzAArohAAABAZBSECEz.IpVjYOfmWMOQOHYGdH4G16pGKUArN1pEpAGJebfBjSrKI71E6ZhDJQQJ99BCACi5YpzAArohAAABAZBSMCrh",
    "Content-Type": "application/json"
}

if __name__ == '__main__':

    # Inizio del test di creazione della conversazione
    startConv = requests.post(url, headers=headers)
    conv_data = startConv.json()

    activityUrl = f"{url}/{conv_data['conversationId']}/activities"
    while True:
        user_input = input("Tu: ")
        body = {
            "locale": "it-IT",
            "type": "message",
            "from": {
                "id": "user1"
            },
            "text": user_input
        }

        send = requests.post(activityUrl, headers=headers, json=body)
        send_data = send.json()
        if send.status_code != 200:
            print("Error: ", send_data)
            break

        param = {"watermark": send_data['id'].split('|')[1]}
        response = requests.get(activityUrl, headers=headers, params=param)
        response_data = response.json()
        while not response_data['activities']:
            time.sleep(1)
            response = requests.get(activityUrl, headers=headers, params=param)
            response_data = response.json()
        print("Copilot: ", response_data['activities'][0]['text'])
        #
        # if user_input.lower() in ["exit", "quit", "esci"]:
        #     break
