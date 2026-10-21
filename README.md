# Cato Outbound Engine

**Demo:** https://micuccivincenzo02.github.io/cato-outbound-engine/

Il prototipo l'ho costruito per candidarmi come GTM Engineer in Cato. È un progetto indipendente.

## Il problema
Un SDR che vende a chi partecipa alle gare pubbliche nella sanità deve capire due cose: **chi chiamare** e **quando**.
Le liste comprate dicono poco su entrambe. Le gare pubbliche invece sono dati aperti, e ogni lotto dice chi ha partecipato, chi ha vinto e quando finisce il contratto.

## Le scelte
- **Fonte: open data ANAC.** Uso i lotti 2025 per dispositivi medici (CPV 331) incrociati con partecipanti e aggiudicatari. Ne escono 2.024 aziende con almeno 5 lotti. Uso il 2025 perché i partecipanti vengono registrati dopo l'aggiudicazione, quindi il 2026 è ancora incompleto.
- **Punteggio calibrato sui clienti.** Fra quelle aziende ci sono 8 dei clienti che Cato mostra sul sito. Le regole del punteggio (volume, ampiezza, margine di vittoria, PMI italiana) sono tarate perché i clienti risultino in alto, e poi i clienti sono tolti dai prospect. È una calibrazione, non una validazione.
- **Partita IVA per correggere Clay.** Il dominio che Google trova per nome a volte è sbagliato (per esempio un ente pubblico al posto dell'azienda). Una formula controlla il nome; quando il controllo fallisce, Claygent ricerca usando nome, settore e P.IVA. Così i dati verificati passano da 27 a 39 su 50.
- **Scadenze come motivo per chiamare.** Dal dataset ANAC "avvio contratto" prendo i contratti vinti che finiscono tra novembre 2026 e luglio 2027: sono 23.874 contratti di 1.198 aziende. La gara di rinnovo è il momento giusto per farsi trovare.

## Pipeline
Si esegue con Python 3 e pandas, lanciando `py -I <script>`. I dati grezzi ANAC vanno in `data/raw/` e non sono nel repository.

| Passo | Script | Output |
|---|---|---|
| 1 | `build_accounts.py` | aziende con 5+ lotti nel 2025 |
| 2 | `score_accounts.py` | punteggio ICP, top 50 per Clay |
| 3 | Clay (`CLAY_GUIDE.md`) | domini, dati aziendali, controllo nome, prima riga AI |
| 4 | `finalize.py` | CSV pronto per l'import in HubSpot |
| 5a | `expiring_contracts.py` | contratti in scadenza nov 2026 – lug 2027 |
| 5b | `fetch_cig_details.py 2022 2023 2024 2025` | oggetto, valore e stazione appaltante dei contratti |
| 5c | `build_explorer_data.py` | dati dell'esploratore (2.024 aziende) |
| 6 | `make_page.py` | `index.html` |

## Limiti
- ANAC conta i lotti (CIG), non le gare.
- Le scadenze sono quelle dichiarate all'avvio del contratto, quindi proroghe e rinnovi non sono inclusi.
- Gli opener sono esempi scritti con la voce di un BDR: non sono materiale di Cato.
- I CSV con i dati Clay non sono pubblicati.

## Strumenti
Python e pandas, Clay (piano gratuito, circa 55 crediti), Claude Code come assistente di sviluppo. Le scelte su fonte, punteggio e segnale sono mie.

Dati: ANAC, dati.anticorruzione.it, licenza CC BY 4.0.

Vincenzo Micucci · [LinkedIn](https://www.linkedin.com/in/vincenzo-micucci-7919802b0)
