document.addEventListener('DOMContentLoaded', function () {
    // Funzionalità JavaScript per la pagina "Chi siamo"
    console.log('Pagina Chi siamo caricata');

    // Genera QR codes
    generateQRCode('qr-code-1', 'https://ifab.example.com/docs', 'Documentazione Tecnica');
    generateQRCode('qr-code-2', 'https://ifab.example.com/tutorials', 'Tutorial Video');
    generateQRCode('qr-code-3', 'https://ifab.example.com/forum', 'Community Forum');
    
    // Funzione per generare QR code
    function generateQRCode(elementId, url, label) {
        const qrContainer = document.getElementById(elementId);
        if (!qrContainer) return;
        
        // Pulisci il contenitore
        qrContainer.innerHTML = '';
        
        // Crea il QR code usando l'API di QRServer.com
        const qrImg = document.createElement('img');
        qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(url)}`;
        qrImg.alt = `QR Code per ${label}`;
        qrImg.className = 'qr-code-image';
        
        // Aggiungi l'immagine al contenitore
        qrContainer.appendChild(qrImg);
        
        // Aggiorna il testo sotto il QR code
        const labelElement = qrContainer.nextElementSibling;
        if (labelElement && labelElement.tagName === 'P') {
            labelElement.textContent = label;
        }
    }
});