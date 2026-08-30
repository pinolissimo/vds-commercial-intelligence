# VDS Local SME 999 — Website-Gap Pipeline

Pipeline commerciale separata per PMI e attività locali con presenza reale ma senza sito web aziendale funzionale, individuate tramite mappe/local search, directory, fonti primarie e verifica incrociata.

## Offerta

**VDS Business Web Presence — €999**

Posizionamento: presenza web professionale completa. L'offerta base può includere struttura one-page premium, responsive, servizi, contatti, gallery, map, SEO locale base, integrazione Google Business, privacy/cookie essentials e pubblicazione. Hosting, manutenzione, SEO continuativa, booking, e-commerce, multilingua e integrazioni sono upsell separati.

Il beneficio fiscale può essere citato nel marketing solo quando verificato con fonte fiscale ufficiale del paese e sempre in forma condizionata rispetto al regime fiscale applicabile e alla corretta documentazione della spesa.

## Pipeline

`RAW_DISCOVERY → RESEARCH → QUALIFIED → READY_FOR_CONTACT_REVIEW → READY_TO_CONTACT → CONTACTED → REPLIED → WON/LOST`

La pipeline resta separata da collaborazioni, progetti UE e procurement.

## Regole di ingresso

Un'attività entra come QUALIFIED solo se identità e attività sono verificabili, il settore ha valore web concreto, l'assenza di sito è verificata con più segnali, località/categoria/reputazione sono documentate, non esiste precedente FIRST_CONTACT per la stessa identità commerciale, il Website Gap Score supera la soglia, il canale è pubblico e appropriato e ogni claim fiscale è supportato da fonte ufficiale.

## Territorial indexing

`country → region → province/canton/county → district/comarca → municipality → neighborhood → activity_type`

JSON è il database canonico. Gli elenchi Markdown sono viste sintetiche per consultazione rapida.

```text
local-no-website/
├── README.md
├── master-index.json
├── config/offer-999.json
├── config/tax-policy.json
├── views/qualified-index.md
├── spain/<region>/<province>/<municipality>/<activity>/*.json
├── italy/<region>/<province>/<municipality>/<activity>/*.json
├── europe/<country>/...
└── outreach/YYYY-MM-DD-*.json
```

Ricerca e filtraggio funzionano 24/7. Il contatto resta soggetto ai normali gate VDS: dedup globale, suppression, Sent history, verifica del canale, personalizzazione e orario lavorativo.

Cartella email ufficiale dedicata: `INBOX.LOCAL-SME-999` su `info@visualdesignstudio.es`.
