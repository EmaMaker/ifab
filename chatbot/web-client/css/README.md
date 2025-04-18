# CSS

Questa cartella contiene i file di stile per l'interfaccia web del chatbot IFAB.

## Struttura dei file

I file CSS sono stati organizzati in componenti tematici per facilitare la manutenzione e lo sviluppo:

- **variables.css**: Contiene le variabili CSS e gli stili di base generali
- **layout.css**: Stili per il layout della pagina, contenitori e struttura
- **header.css**: Stili per l'header e la navigazione
- **buttons.css**: Stili per tutti i tipi di pulsanti (standard, registrazione, statici)
- **messages.css**: Stili per i messaggi della chat (bot, utente, errore)
- **animations-audio.css**: Animazioni e stili per i componenti audio
- **info-box.css**: Stili per il box informativo
- **about.css**: Stili specifici per la pagina "Chi siamo"

## Utilizzo

I file CSS sono inclusi nelle pagine HTML nell'ordine corretto per garantire la corretta applicazione degli stili. Assicurarsi di mantenere questo ordine quando si modificano le pagine HTML:

1. variables.css (deve essere caricato per primo)
2. layout.css
3. header.css
4. buttons.css
5. messages.css
6. animations-audio.css
7. Altri file CSS specifici (info-box.css, about.css, ecc.)