# VDS Local No-Website Prospects

Pipeline separata per attività commerciali locali in Italia e Spagna individuate tramite ricerche locali/directory/mappe e verificate come prive di un sito web aziendale funzionale.

## Regole di ingresso

Un'attività entra in questa lista solo se:
- è un'attività reale e verificabile;
- opera in un settore dove un sito web può avere valore commerciale concreto;
- non risulta avere un sito web aziendale funzionante dopo verifica incrociata;
- sono disponibili informazioni sufficienti per capire attività, posizionamento, località e reputazione;
- non è già presente nel CRM VDS e non è mai stata contattata con una prima email;
- il potenziale economico e la probabilità di conversione superano la soglia qualitativa.

## Dati minimi

Ogni prospect deve includere: nome, paese, regione/comunidad, città, categoria, indirizzo, telefono, email se pubblica e verificata, profili social, rating/review count quando disponibili, fonti, prova dell'assenza di sito, analisi dell'attività, proposta web suggerita, score e stato outreach.

## Outreach

La personalizzazione viene preparata solo dopo l'analisi dell'attività. Nessun primo contatto può essere duplicato. Dove il canale non autorizza chiaramente proposte commerciali, il sistema conserva una bozza `APPROVAL_REQUIRED` invece di inviarla automaticamente.

## Struttura

```text
local-no-website/
├── README.md
├── master-index.json
├── italy/<region>/<city>/*.json
├── spain/<comunidad>/<city>/*.json
└── outreach/YYYY-MM-DD-*.json
```
