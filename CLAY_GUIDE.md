# Guida Clay — Cato Outbound Engine (step 3)

Obiettivo: importare i 50 account in Clay, arricchirli, ricostruire il punteggio come **colonna formula** e generare la **prima riga del messaggio con una colonna AI**. Poi export → CSV per HubSpot e registrazione del Loom.

> I nomi dei menu di Clay cambiano spesso: se un'etichetta non coincide, cerca la funzione equivalente. **Prova ogni arricchimento su 5 righe prima di lanciarlo su 50** (i crediti del piano gratuito sono pochi; controlla quanti ne hai appena ti iscrivi).

## 0. Account
- Iscriviti su clay.com (piano gratuito) con la tua email personale.
- Crea un workbook "Cato Outbound Engine".

## 1. Import
- New table → Import CSV → `data/clay_import.csv` (50 righe, già ordinate e senza i clienti attuali di Cato).
- Controlla che `Lots bid`, `Lots won`, `Contracting authorities`, `Value bid EUR` siano di tipo **Number**.

## 2. Arricchimento (su 5 righe, poi tutte se i crediti bastano)
1. **Dominio aziendale:** Add enrichment → "Find company domain/website" dal nome (colonna `Company`). Rinominala `Domain`.
2. **Dati aziendali:** Add enrichment → "Enrich company" dal `Domain` → tieni `Employee count`, `HQ country`, `LinkedIn URL`.
3. *(Facoltativo, solo con crediti avanzati)* Claygent: "Trova il nome del responsabile gare/ufficio tender di {{Company}} su LinkedIn". Se lo usi, nel Loom dì che lo faresti con Lusha in produzione.

Se i crediti finiscono: tieni l'arricchimento solo sulle prime 10–20 righe e dillo apertamente nel Loom ("in produzione girerebbe su tutta la lista").

## 3. Colonna formula `ICP score`
Add column → Formula. Inserisci le colonne con `/` (compaiono come `{{...}}`). Stessa logica di `score_accounts.py`, ma con il **numero di dipendenti** al posto del filtro sul nome:

```
({{Lots bid}} >= 15 && {{Lots bid}} <= 1000 ? 40 : ({{Lots bid}} < 15 ? 20 : 10))
+ Math.min({{Contracting authorities}}, 20)
+ ({{Lots won}} / {{Lots bid}} < 0.6 ? 15 : 8)
+ ({{HQ country}} == "Italy" && {{Employee count}} < 1000 ? 25 : 0)
```

Cosa significa (da saper spiegare a colloquio):
- **Volume (40):** 15–1.000 lotti l'anno = carico di gare reale ma senza un ufficio gare enorme. I clienti visibili di Cato stanno tra 16 e 995.
- **Ampiezza (20):** più stazioni appaltanti = più portali, più documenti diversi = più dolore.
- **Margine (15):** chi vince meno del 60% di quello a cui partecipa ha margine per migliorare.
- **PMI italiana (25):** le filiali delle multinazionali hanno team gare interni; i clienti di Cato sono aziende italiane medie.

Poi ordina la tabella per `ICP score` decrescente.

## 4. Colonna AI `Opener`
Add column → Use AI (modello più economico disponibile). Prompt:

```
Sei un BDR di Cato, piattaforma AI che aiuta le aziende a trovare, analizzare e preparare gare d'appalto pubbliche.
Scrivi UNA frase di apertura in italiano (max 30 parole), dando del Lei, per un'email a {{Company}}.
Usa solo questi dati, senza inventare nulla:
- lotti di gara a cui hanno partecipato nel 2025: {{Lots bid}}
- stazioni appaltanti diverse: {{Contracting authorities}}
- esempio di lotto: {{Example lot}} ({{Example authority}})
Tono concreto, niente complimenti generici, niente punti esclamativi.
```

Confronta 3–4 risultati con la colonna `Opener draft` dello script Python e tieni il migliore.

## 5. Export
- Export → CSV → salva come `cato_top50_clay.csv` nella cartella del progetto.
- Fammi sapere: aggiorno il CSV per HubSpot e la pagina demo con i dati arricchiti.

## 6. Per il Loom (2 min)
Tieni aperte in schede diverse: la pagina demo, la tabella Clay ordinata per punteggio, il CSV. Lo script del Loom te lo preparo dopo l'export.
