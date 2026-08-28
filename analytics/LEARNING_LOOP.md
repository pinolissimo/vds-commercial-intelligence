# VDS Commercial Intelligence — Learning Loop

## Obiettivo

Migliorare decisioni commerciali sulla base di outcome reali, non sul volume di attività.

## Frequenza

Il daily engine aggiorna metriche operative. Il QA verifica coerenza. Una review periodica usa gli snapshot per proporre modifiche solo quando esiste evidenza sufficiente.

## Domande obbligatorie

1. Quali segmenti generano più positive reply?
2. Quali fonti producono meeting/proposal/win?
3. Qual è il tempo medio first-contact → reply → meeting → proposal → won?
4. Quali campagne producono attività ma nessun segnale commerciale?
5. Quali reason code dominano le loss?
6. Quali quality gate falliscono più spesso?
7. Quanti lead HOT decadono senza segnali?
8. Quali territori producono lead di qualità superiore?
9. Il local-no-website channel genera reply/proposte o solo ricerca?
10. Quali decision-maker role convertono meglio?

## Regole anti-overfitting

- Non cambiare strategia per uno o due casi isolati.
- Separare segnali qualitativi da conversion rate statisticamente credibili.
- Mantenere `UNCALIBRATED` finché i campioni minimi non sono raggiunti.
- Conservare sempre la regola precedente e la ragione del cambiamento.
- Un aumento di email inviate non è un miglioramento se non aumenta i segnali a valle.

## Output

Ogni revisione utile deve produrre:
- finding;
- evidence/sample;
- proposed rule change;
- expected impact;
- regression risk;
- decision: ADOPT / TEST / REJECT;
- review date.

## North Star

`€ won` è la metrica finale. `positive replies`, `meetings` e `proposals` sono leading indicators. `leads found` e `emails sent` sono solo activity metrics.