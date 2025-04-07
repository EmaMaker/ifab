document.addEventListener('DOMContentLoaded', function () {
    const chatContainer = document.getElementById('chatContainer');
    const messageContainer = document.getElementById('messageContainer');
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const recordButton = document.getElementById('recordButton');
    const statusElement = document.getElementById('status');

    let isRecording = false;
    let mediaRecorder = null;
    let audioChunks = [];
    let isWaitingForResponse = false;
    let audioContext = null;
    let analyser = null;
    let microphone = null;
    let animationFrame = null;
    let volumeIndicator = null;
    let recordingMode = 'toggle'; // Nuova variabile per la modalità di registrazione: 'toggle' o 'push'
    let lastAudioPath = null; // Variabile per tenere traccia dell'ultimo file audio registrato
    let audioMessages = {}; // Oggetto per memorizzare i percorsi audio associati a ciascun messaggio

    // Inizializza la connessione Socket.IO
    const socket = io();

    socket.on('message', function (data) {
        if (data.type === 'message') {
            addBotMessage(data.text);
        } else if (data.type === 'error') {
            addBotMessage('Errore: ' + data.text);
        }
        hideLoading();

    });

    socket.on('stt', function (data) {
        // Aggiorna il messaggio specifico usando l'ID fornito dal backend
        updateAudioMessage(data.messageId, data.text);
        hideLoading();
    });

    // Gestisci gli errori di connessione
    socket.on('connect_error', function (error) {
        console.error('Connection error:', error);
        addBotMessage('Errore di connessione al server. Riprova più tardi.');
        hideLoading();
    });

    // Initialize the chat
    function initChat() {
        addBotMessage('Benvenuto! Puoi scrivere un messaggio o registrare un messaggio vocale.');
    }

    // Add a user message to the chat
    function addUserMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message';
        messageDiv.textContent = text;
        messageContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // Add a bot message to the chat
    function addBotMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot-message';
        messageDiv.textContent = text;
        messageContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // Add a user audio message to the chat
    function addUserAudioMessage(text, audioPath, customMessageId = null) {
        // Usa l'ID fornito o genera un ID univoco per questo messaggio audio
        const messageId = customMessageId || ('audio_' + Date.now());

        // Memorizza il percorso audio associato a questo ID
        if (audioPath) {
            audioMessages[messageId] = audioPath;
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message';
        messageDiv.dataset.messageId = messageId;

        // Crea un contenitore per il messaggio audio
        const audioContainer = document.createElement('div');
        audioContainer.className = 'audio-message';

        // Crea il pulsante di riproduzione con sfondo visibile
        const playButton = document.createElement('button');
        playButton.className = 'audio-play-btn';
        playButton.innerHTML = `
            <svg viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z"/>
            </svg>
        `;

        // Crea l'elemento per il testo con stile per andare a capo
        const textSpan = document.createElement('span');
        textSpan.className = 'audio-transcription';

        // Aggiungi un'animazione di caricamento iniziale
        const loadingAnimation = document.createElement('div');
        loadingAnimation.className = 'loading-animation';
        loadingAnimation.innerHTML = '<div></div><div></div><div></div><div></div>';
        textSpan.appendChild(loadingAnimation);
        textSpan.appendChild(document.createTextNode('Trascrizione in corso'));
        textSpan.appendChild(loadingAnimation);

        // Aggiungi gli elementi al contenitore
        audioContainer.appendChild(playButton);
        audioContainer.appendChild(textSpan);

        // Aggiungi il contenitore al messaggio
        messageDiv.appendChild(audioContainer);

        // Implementa la riproduzione dell'audio quando si preme il pulsante play
        playButton.addEventListener('click', function () {
            // Ottieni l'ID del messaggio dal genitore più vicino con l'attributo data-message-id
            const parentMessage = this.closest('.message');
            const currentMessageId = parentMessage ? parentMessage.dataset.messageId : null;

            // Usa l'ID del messaggio per trovare il percorso audio corrispondente
            const audioPath = currentMessageId ? audioMessages[currentMessageId] : null;

            console.log('ID messaggio corrente:', currentMessageId);
            console.log('Audio disponibili:', audioMessages);
            console.log('Percorso audio trovato:', audioPath);

            if (audioPath) {
                // Crea un elemento audio e riproduci il file
                const audio = new Audio(audioPath);
                audio.play()
                    .then(() => {
                        console.log('Audio riprodotto con successo');
                    })
                    .catch(error => {
                        console.error('Errore durante la riproduzione audio:', error);
                        // Prova con un percorso relativo se il percorso assoluto non funziona
                        const relativeAudioPath = audioPath.startsWith('/') ? audioPath : '/' + audioPath;
                        const fallbackAudio = new Audio(relativeAudioPath);
                        fallbackAudio.play()
                            .catch(err => {
                                console.error('Anche il fallback ha fallito:', err);
                            });
                    });
            } else {
                console.log('Nessun file audio disponibile per la riproduzione');
            }
        });

        messageContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;

        return messageId;
    }

    // Update an existing audio message with transcription
    function updateAudioMessage(messageId, text) {
        const messageDiv = document.querySelector(`.message[data-message-id="${messageId}"]`);
        if (messageDiv) {
            const textSpan = messageDiv.querySelector('.audio-transcription');
            if (textSpan) {
                textSpan.firstChild.textContent = 'Audio Transcritto: 🎤🎤';
                // Trova e rimuovi solo l'animazione di caricamento e il testo "Trascrizione in corso..."
                const animationContainer = textSpan.querySelector('div');
                if (animationContainer) {
                    animationContainer.innerHTML = text;
                }
            } else {
                console.warn("L'elemento ',audio-transcription' non trovato per l'ID messaggio:", messageId);
            }

            chatContainer.scrollTop = chatContainer.scrollHeight;
        } else {
            console.warn("Messaggio non trovato per l'ID:", messageId);
        }
    }

// Show loading animation
    function showLoading(msg = 'In attesa di risposta') {
        isWaitingForResponse = true;
        statusElement.innerHTML = `<div class="loading-animation"><div></div><div></div><div></div><div></div></div>${msg}<div class="loading-animation"><div></div><div></div><div></div><div></div></div>`;
        sendButton.disabled = true;
        recordButton.disabled = true;

        // Disabilita i pulsanti statici
        setStaticButtonsState(true);
    }

// Hide loading animation
    function hideLoading() {
        isWaitingForResponse = false;
        statusElement.innerHTML = '';
        sendButton.disabled = false;
        recordButton.disabled = false;

        // Riabilita i pulsanti statici
        setStaticButtonsState(false);
    }

// Send a text message
    function sendTextMessage(text) {
        if (text === '') return;

        addUserMessage(text);
        messageInput.value = '';
        showLoading();

        // Send the message to the server
        fetch('/send-message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({text: text})
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // The response will be handled by the WebSocket connection
            })
            .catch(error => {
                console.error('Error:', error);
                addBotMessage('Si è verificato un errore durante l\'invio del messaggio.');
                hideLoading();
            });
    }

// Check microphone permissions
    async function checkMicrophonePermission() {
        try {
            // Verifica se l'API permissions è supportata
            if (navigator.permissions && navigator.permissions.query) {
                const permissionStatus = await navigator.permissions.query({name: 'microphone'});

                // Aggiungi un listener per i cambiamenti di stato dei permessi
                permissionStatus.onchange = function () {
                    console.log('Microphone permission state changed to:', this.state);
                    // Se il permesso è stato concesso dopo un rifiuto, aggiorna l'interfaccia
                    if (this.state === 'granted') {
                        statusElement.textContent = 'Permesso microfono concesso. Puoi registrare ora.';
                        setTimeout(() => {
                            if (statusElement.textContent === 'Permesso microfono concesso. Puoi registrare ora.') {
                                statusElement.textContent = '';
                            }
                        }, 3000);
                    }
                };

                return permissionStatus.state;
            } else {
                // Fallback per browser che non supportano l'API permissions
                console.log('Permissions API not supported, using fallback method');
                return 'prompt'; // Assume che il browser chiederà il permesso
            }
        } catch (error) {
            console.error('Error checking microphone permission:', error);
            return 'unknown';
        }
    }

// Start recording audio
    async function startRecording() {
        if (isRecording || isWaitingForResponse) return;

        // Check if the browser supports MediaRecorder
        if (!navigator.mediaDevices || !window.MediaRecorder) {
            addBotMessage('Il tuo browser non supporta la registrazione audio.');
            return;
        }

        try {
            // Verifica più accurata dei permessi del microfono
            const permissionState = await checkMicrophonePermission();
            if (permissionState === 'denied') {
                addBotMessage('L\'accesso al microfono è stato negato. Per abilitarlo:\n1. Clicca sull\'icona del lucchetto nella barra degli indirizzi\n2. Trova "Microfono" nelle impostazioni\n3. Seleziona "Consenti"');
                return;
            }

            // Pulisci eventuali risorse audio precedenti
            cleanupAudioResources();

            // Richiedi l'accesso al microfono
            const stream = await navigator.mediaDevices.getUserMedia({audio: true});

            isRecording = true;
            recordButton.classList.add('recording');
            statusElement.textContent = 'Registrazione in corso... Clicca di nuovo per terminare';

            // Crea l'indicatore del volume
            volumeIndicator = document.createElement('div');
            volumeIndicator.className = 'volume-indicator';
            recordButton.appendChild(volumeIndicator);

            // Inizializza l'analisi del volume
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            analyser = audioContext.createAnalyser();
            microphone = audioContext.createMediaStreamSource(stream);
            microphone.connect(analyser);
            analyser.fftSize = 256;

            // Funzione per analizzare il volume
            function analyzeVolume() {
                if (!isRecording) return;

                const dataArray = new Uint8Array(analyser.frequencyBinCount);
                analyser.getByteFrequencyData(dataArray);

                // Calcola il volume medio
                const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
                const volume = Math.min(average / 128, 2); // Normalizza tra 0 e 2

                // Aggiorna l'indicatore visivo
                if (volumeIndicator) {
                    volumeIndicator.style.transform = `translate(-50%, -50%) scale(${1 + volume * 0.5})`;
                    volumeIndicator.style.opacity = volume * 0.5;
                }

                animationFrame = requestAnimationFrame(analyzeVolume);
            }

            analyzeVolume();

            // Inizializza il MediaRecorder
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, {type: 'audio/wav'});
                const formData = new FormData();
                formData.append('audio', audioBlob, 'recording.wav');

                // Crea immediatamente un messaggio audio utente con animazione di caricamento
                const tempMessageId = 'audio_' + Date.now();
                const messageId = addUserAudioMessage('🎤', null, tempMessageId);

                showLoading();

                fetch('/upload-audio', {
                    method: 'POST',
                    body: formData
                })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        return response.json();
                    })
                    .then(data => {
                        // Salva il percorso del file audio per la riproduzione
                        if (data.success && data.file_path) {
                            lastAudioPath = data.file_path;

                            // Se il server ha restituito un ID messaggio, aggiornalo nel DOM
                            if (data.message_id && data.message_id !== tempMessageId) {
                                const messageDiv = document.querySelector(`.message[data-message-id="${tempMessageId}"]`);
                                if (messageDiv) {
                                    messageDiv.dataset.messageId = data.message_id;
                                    // Aggiorna anche la mappa degli audio
                                    audioMessages[data.message_id] = data.file_path;
                                    delete audioMessages[tempMessageId];
                                } else {
                                    // Fallback se non troviamo l'elemento
                                    audioMessages[tempMessageId] = data.file_path;
                                }
                            } else {
                                // Associa il percorso audio a questo messaggio specifico
                                audioMessages[messageId] = data.file_path;
                            }

                            // Mostra un messaggio temporaneo con l'animazione di caricamento
                            const messageElement = document.querySelector(`.message[data-message-id="${data.message_id || messageId}"]`);
                            if (messageElement) {
                                const textSpan = messageElement.querySelector('.audio-transcription');
                                if (textSpan) {
                                    // Rimuovi il contenuto precedente
                                    textSpan.innerHTML = '';

                                    // Aggiungi il testo del messaggio audio
                                    textSpan.appendChild(document.createTextNode('🎤 Messaggio audio registrato'));

                                    // Aggiungi l'animazione di caricamento sotto il testo
                                    const loadingAnimation = document.createElement('div');
                                    loadingAnimation.className = 'loading-animation';
                                    loadingAnimation.innerHTML = '<div></div><div></div><div></div><div></div>';

                                    // Crea un contenitore per l'animazione
                                    const animationContainer = document.createElement('div');
                                    animationContainer.style.display = 'block';
                                    animationContainer.style.marginTop = '5px';
                                    animationContainer.appendChild(loadingAnimation);
                                    animationContainer.appendChild(document.createTextNode(' Trascrizione in corso...'));

                                    textSpan.appendChild(document.createElement('br'));
                                    textSpan.appendChild(animationContainer);
                                }
                            }
                        }
                        // The response will be handled by the WebSocket connection
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        updateAudioMessage(messageId, '🎤 Errore durante l\'elaborazione dell\'audio');
                        hideLoading();
                    });
            };

            mediaRecorder.start();

        } catch (error) {
            console.error('Error starting recording:', error);
            addBotMessage('Si è verificato un errore durante l\'avvio della registrazione.');
            cleanupAudioResources();
        }
    }

// Stop recording audio
    function stopRecording() {
        if (!isRecording) return;

        isRecording = false;
        recordButton.classList.remove('recording');
        statusElement.textContent = '';

        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
        }

        cleanupAudioResources();
    }

// Cleanup audio resources
    function cleanupAudioResources() {
        if (animationFrame) {
            cancelAnimationFrame(animationFrame);
            animationFrame = null;
        }

        if (audioContext) {
            audioContext.close();
            audioContext = null;
        }

        if (volumeIndicator) {
            volumeIndicator.remove();
            volumeIndicator = null;
        }

        if (microphone) {
            microphone.disconnect();
            microphone = null;
        }

        analyser = null;
    }

// Event listeners
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendTextMessage(messageInput.value.trim());
        }
    });

    sendButton.addEventListener('click', () => {
        sendTextMessage(messageInput.value.trim());
    });

// Modifica gli event listener per il pulsante di registrazione
    if (recordingMode === 'push') {
        // Modalità push-to-talk (registra solo mentre è premuto)
        recordButton.addEventListener('mousedown', startRecording);
        recordButton.addEventListener('mouseup', stopRecording);
        recordButton.addEventListener('mouseleave', stopRecording);
        recordButton.addEventListener('touchstart', (e) => {
            e.preventDefault();
            startRecording();
        });
        recordButton.addEventListener('touchend', (e) => {
            e.preventDefault();
            stopRecording();
        });
    } else {
        // Modalità toggle (clicca una volta per iniziare, clicca di nuovo per fermare)
        recordButton.addEventListener('click', () => {
            if (isRecording) {
                stopRecording();
            } else {
                startRecording();
            }
        });

        // Per dispositivi touch
        recordButton.addEventListener('touchend', (e) => {
            e.preventDefault();
            if (isRecording) {
                stopRecording();
            } else {
                startRecording();
            }
        });
    }

// Funzione per abilitare/disabilitare tutti i pulsanti statici
    function setStaticButtonsState(disabled) {
        document.querySelectorAll('.static-btn').forEach(button => {
            button.disabled = disabled;
            if (disabled) {
                button.classList.add('disabled');
            } else {
                button.classList.remove('disabled');
            }
        });
    }

// Initialize the chat
    initChat();

// Aggiungi event listener per i pulsanti statici
    document.querySelectorAll('.static-btn').forEach(button => {
        button.addEventListener('click', function () {
            const buttonText = this.querySelector('span').textContent;

            // Invia il testo del pulsante al server
            showLoading(`Dirigiti alla ${buttonText}`);             // Mostra l'animazione di caricamento temporanea per i pulsanti
            fetch('/button-click', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({text: buttonText})
            })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        // Mostra un feedback visivo che il pulsante è stato premuto
                        this.classList.add('button-pressed');
                        setTimeout(() => {
                            this.classList.remove('button-pressed');
                        }, 300);

                        console.log('Comando inviato:', data.command);
                        // Imposta un timer per nascondere automaticamente il loading dopo 1 secondi dalla conferma di ricezione
                        setTimeout(() => {
                            hideLoading();
                        }, 1000); // 1 secondi
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    addBotMessage('Si è verificato un errore durante l\'invio del comando.');
                });
        });
    });
})
;