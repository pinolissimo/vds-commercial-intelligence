# VDS Public Procurement Intelligence

Filone separato per gare, piani di acquisto, consultazioni e opportunità di partnership nel settore pubblico. La fonte operativa è il motore locale; questo repository conserva documentazione, configurazioni non sensibili e viste GitHub.

## Regola fondamentale

Una gara non entra mai nella coda commerciale ordinaria e non viene inviata tramite Batch Dispatcher. Il sistema può analizzare, ordinare, preparare un pacchetto di revisione e identificare un possibile partner privato; la presentazione formale resta un’azione esplicita del titolare.

## Stati

`PUBLIC_RAW`, `PUBLIC_NORMALIZED`, `PUBLIC_VERIFIED`, `DOCUMENTS_PENDING`, `ELIGIBILITY_PENDING`, `BID_READY`, `PARTNER_REQUIRED`, `SUBCONTRACT_OPPORTUNITY`, `EARLY_SIGNAL`, `MANUAL_ROUTE_REQUIRED`, `WATCH`, `REJECTED`, `EXPIRED`, `AWARDED_OTHER`, `WON`.

`UNKNOWN` non è mai un requisito superato. Una procedura tecnicamente interessante ma non candidabile direttamente diventa `PARTNER_REQUIRED` o `SUBCONTRACT_OPPORTUNITY`, non un falso `BID_READY`.

## Dashboard locale

Aprire `http://127.0.0.1:7777/procurement` per consultare scadenze, ente, CPV, fit VDS, eleggibilità, route, salute fonti e pacchetti di revisione.

## Fonti

- TED: avvisi UE ufficiali.
- PLACSP: Spagna, feed open-data/ATOM e profili del committente.
- ANAC/BDNCP: Italia, dati pubblici e avvisi/piattaforme ufficiali.
- Profili del committente, trasparenza, piani e consultazioni: segnali precoci e documenti ufficiali.

Le fonti PLACSP e ANAC sono predisposte per l’integrazione a feed/dataset ufficiali; non sono dichiarate produttive finché non ricevono benchmark live misurati.
