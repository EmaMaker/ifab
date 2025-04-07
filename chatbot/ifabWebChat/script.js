document.addEventListener('DOMContentLoaded', function() {
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
    
    // Inizializza la connessione Socket.IO
    const socket = io();
    
    // Gestisci i messaggi in arrivo dal server
    socket.on('message', function(data) {
        if (data.type === 'message') {
            addBotMessage(data.text);
            hideLoading();
        } else if (data.type === 'error') {
            addBotMessage('Errore: ' + data.text);
            hideLoading();
        }
    });
    
    // Gestisci gli errori di connessione
    socket.on('connect_error', function(error) {
        console.error('Connection error:', error);
        addBotMessage('Errore di connessione al server. Riprova più tardi.');
        hideLoading();
    });
    
    // Gestisci gli errori di connessione
    socket.on('connect_error', function(error) {
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
    
    // Show loading animation
    function showLoading() {
        isWaitingForResponse = true;
        statusElement.innerHTML = '<div class="loading-animation"><div></div><div></div><div></div><div></div></div> In attesa di risposta...';
        sendButton.disabled = true;
        recordButton.disabled = true;
    }
    
    // Hide loading animation
    function hideLoading() {
        isWaitingForResponse = false;
        statusElement.innerHTML = '';
        sendButton.disabled = false;
        recordButton.disabled = false;
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
            body: JSON.stringify({ text: text })
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
                const permissionStatus = await navigator.permissions.query({ name: 'microphone' });
                
                // Aggiungi un listener per i cambiamenti di stato dei permessi
                permissionStatus.onchange = function() {
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
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            isRecording = true;
            recordButton.classList.add('recording');
            statusElement.textContent = 'Registrazione in corso...';
            
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
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                const formData = new FormData();
                formData.append('audio', audioBlob, 'recording.wav');
                
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
                    // The response will be handled by the WebSocket connection
                })
                .catch(error => {
                    console.error('Error:', error);
                    addBotMessage('Si è verificato un errore durante l\'invio della registrazione.');
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
    
    // Initialize the chat
    initChat();

});