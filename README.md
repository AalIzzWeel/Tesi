# Ottimizzazione budget-constrained della sicurezza in deployment Cloud-Edge

Implementazione e confronto sperimentale di algoritmi (Greedy, Brute Force, MILP) per la selezione ottimale di azioni di miglioramento della sicurezza, sotto vincolo di budget, su deployment valutati con SecFog (Forti et al., 2020).

---

## Problema

Dato un deployment `D` con uno score di sicurezza SecFog e un budget `B`, trovare il sottoinsieme di azioni di miglioramento che massimizza l'aumento di score rispettando `B`. 
OSS: Formalizzato come variante di knapsack con vincoli di precedenza (NP-hard), per la presenza di catene di prerequisiti tra azioni.

---

## Architettura del progetto (aggiornato a: 21 luglio 2026)

```
tesi/
├── SecFog/ # repo Forti et al. (secfog.pl, regole logiche)
└── src/
    ├── requirements.pl # requisiti dell'applicazione
    ├── action_catalog.py # catalogo azioni, baseline, helper prerequisiti
    ├── score_wrapper.py # oracolo: interfaccia Python ↔ ProbLog
    └── greedy.py # algoritmo greedy
    ├── debug_A5.py # test per erificare se la sicurezza scala in modo non lineare
    └── debug_chain.py # test per le catene di dipendenza multi-livello
```

---

### `SecFog/secfog.pl`

Il file contiene il motore di regole logiche di base per il calcolo della sicurezza del deployment:

* **`secFog(OpA, App, Deployment)`**: Predicato principale che valuta se l'applicazione `App` dell'operatore `OpA` può essere distribuita correttamente.
* **Regola di deployment**: Regola ricorsiva che associa ogni componente dell'applicazione a un nodo di elaborazione, assicurandosi che:
  1. Il nodo rispetti i **requisiti di sicurezza** del componente (`securityRequirements`).
  2. Esista una **catena di fiducia** valida tra l'operatore dell'applicazione e l'operatore del nodo (`trusts2`).
* **`trusts2/2` (Chiusura Transitiva del Trust)**: Calcola la fiducia sia in forma diretta (`trusts(A, B)`) che in forma transitiva/delegata attraverso nodi intermedi (`trusts(A, C) ∧ trusts2(C, B)`).

---

## `src/requirements.pl`

Definisce le regole logiche specifiche dell'applicazione target (in questo caso `weatherApp`) e le relazioni di fiducia iniziale tra l'operatore e i nodi.

> Nota: La scelta di utilizzare il trust diretto invece della chiusura transitiva trusts2/2 è stata intenzionale per limitare il dominio delle variabili di input. Questo approccio ha evitato la necessità di caratterizzare manualmente tutte le relazioni di fiducia nel catalogo completo delle azioni (11 azioni, 4 categorie) e ha permesso di isolare l'impatto diretto del trust sul bilanciamento tra sicurezza e budget.

---

## `src/action_catalogue.py`

Questo modulo definisce la **baseline di sicurezza iniziale** e il **catalogo delle azioni di miglioramento** applicabili ai nodi Cloud ed Edge, seguendo la tassonomia definita nel paper di *SecFog*.

**Componenti Principali:**

* **`BASELINE`**:
  * Definisce le probabilità iniziali delle capacità di sicurezza sui nodi `cloud` ed `edge`. Le capacità assenti sono inizializzate esplicitamente a 0.0.
  * Attualmente (21/07/26) la baseline scelta per i test è quella mostrata nel `weatherExample.pl` ma abbassata di circa 10% 
  * Per il momento è hard-coded ma in futuro prevedo di metterlo in un file separato

* **`ACTIONS`**:
  * Un catalogo di azioni disponibili (da **A1** ad **A11**, per il momento) create ad hoc per l'esempio scelto.
  * Attualmente sono previsti due tipologie: improve (incremento prestazionale di una capacità esistente) e buy (acquisto di una capacità non ancora presente sul nodo).
  * Per modellare la realtà operativa, alcune azioni (livello 2) richiedono il completamento di un'azione propedeutica (livello 1). Ad esempio, l'azione A2 (anti-tampering livello 2) richiede obbligatoriamente il completamento di A1.
  *  Ogni azione specifica:

| Campo | Descrizione |
| :--- | :--- |
| **ID** | Identificatore univoco dell'azione |
| **Type** | Tipo di azione ('improve' o 'buy') |
| **Node** | Nodo a cui si applica l'azione ('edge' o 'cloud') |
| **Capability** | Capacità che l'azione migliora o acquista |
| **Category** | Categoria della capacità ('Fisico', 'Comunicazione', 'Dati', 'Virtualizzazione', 'Other') |
| **p_before** | Probabilità prima dell'azione |
| **p_after** | Probabilità dopo l'azione |
| **Cost** | Costo dell'azione |
| **Level** | Livello dell'azione (1 o 2) |
| **Requires** | Azione prerequisito (se presente) |
| **Description** | Descrizione dell'azione |

> Nota: Rimane ancora da valutare se conviene definire azioni specifiche per ogni nodo e capacità (come in questo caso) o definire azioni più generali che richiedono controlli aggiuntivi in futuro (ad esempio controlli sull'ordine o sul tipo di capability).


* **Funzioni di Utilità**:
  * **`print_catalog()`**: Stampa a schermo il catalogo formattato e suddiviso per categorie.
  * **`get_action(aid)`**: Recupera i dettagli di un'azione specifica tramite il suo ID.
  * **`get_prerequisites(aid)`**: Restituisce l'intera catena di dipendenze/prerequisiti necessari per abilitare un'azione selezionata.


---

## `src/score_wrapper.py`

Questo modulo funge da **Oracolo/Interfaccia tra Python e ProbLog**. Il suo compito è prendere una combinazione di contromisure scelte dall'ottimizzatore, aggiornare lo stato del sistema, generare dinamicamente il file di regole ProbLog corrispondente ed invocare il motore d'inferenza probabilistico per restituire lo score di sicurezza.

> Nota: Al momento (21/07/26) ho deciso di usare lo score scalare di default di SecFog: `score()` restituisce un `float` puro estratto via regex dall'output di ProbLog (`max()` sui match, non gestione di coppie). Tutta la pipeline (`delta_score`, `gain_table`, `greedy_search`) lavora coerentemente su questo tipo.

### Funzionalità e Architettura

1. **Ponte Python ↔ ProbLog (`build_pl` & `score`)**:
   * **`build_pl(state)`**: Unisce le regole core di SecFog (`secfog.pl`), i requisiti applicativi (`requirements.pl`) e trasforma lo stato del sistema aggiornato in fatti probabilistici Problog (es. `0.95::anti_tampering(edge).`). Infine aggiunge la query `query(secFog(appOp, weatherApp, D)).`.
   * **`score(action_ids)`**: Crea un file `.pl` temporaneo tramite `tempfile`, esegue il processo ProbLog via `subprocess`, ed estrae lo score numerico dall'output usando un'espressione regolare (`SCORE_REGEX`).

2. **Gestione dello Stato e Validazione (`apply_actions`)**:
   * Riceve la baseline e una lista di ID azione.
   * Controlla che tutti i prerequisiti (es: livello 1 prima di livello 2) siano soddisfatti.
   * Verifica con una tolleranza float (`1e-6`) che la probabilità corrente del nodo (`p_before`) coincida con quanto atteso dall'azione, prevenendo inconsistenze nello stato.

3. **Caching su `score()`**:
   * **`_SCORE_CACHE`**: Una cache in-memory basata su `frozenset(action_ids)`. Se l'algoritmo valuta la stessa combinazione di azioni più volte, lo score viene restituito immediatamente senza dover ri-eseguire il processo esterno ProbLog.

4. **Metriche di Rendimento (`delta_score` & `gain_table`)**:
   * **`delta_score(action_ids, s0)`**: Calcola l'incremento di sicurezza rispetto alla baseline ($\Delta score = score(A) - score_{baseline}$).
   * **`gain_table(s0)`**: Costruisce una tabella dei rendimenti per ogni singola azione (inclusi gli eventuali prerequisiti), calcolando il rapporto efficienza/costo ($Ratio = \frac{\Delta score}{Costo}$). Ordinando le azioni per questo rapporto, fornisce la base teorica per l'algoritmo Greedy.

5. **Ordinamento Dipendenze (`order_by_prerequisites`)**:
   * Garantisce che qualsiasi sequenza di azioni passata all'oracolo sia ordinata in modo che i prerequisiti vengano applicati prima delle azioni di livello superiore.


### Scelte Progettuali Chiave

* **Isolamento dell'Invocazione**: Usare file temporanei e chiamate a sottoprocesso `subprocess` isola l'ambiente Python da eventuali memory leak o errori interni dell'interprete ProbLog.
* **Supporto alle Non-Linearità**: Il calcolo dello score tramite oracolo probabilistico cattura le interazioni non-lineari del sistema: l'impatto di due azioni combinate non è semplicemente la somma dei loro singoli guadagni.

---

## `src/greedy.py`

Questo modulo implementa l'**algoritmo di ricerca Greedy** per la selezione ottimale delle contromisure di sicurezza, soggetto a un vincolo di budget (aka. *budget-constrained optimization*).


### Funzionalità e Architettura

* **`_missing_chain(candidate_id, current_list)`**:
  Identifica l'insieme di azioni non ancora applicate necessarie per abilitare il candidato scelto (inclusi eventuali prerequisiti non ancora soddisfatti), restituendoli nel corretto ordine di esecuzione tramite `order_by_prerequisites`.

* **`_incremental_cost(missing_ids)`**:
  Calcola il costo economico aggiuntivo necessario per applicare la catena di azioni mancanti.

* **`greedy_search(budget, verbose)`**:
  Esegue la ricerca iterativa dell'ottimo locale basata sul rapporto rendimento/costo:
  1. Parte da uno stato iniziale vuoto ($S = []$) e calcola lo score di baseline $s_0$.
  2. Ad ogni iterazione, valuta tutte le azioni non ancora selezionate.
  3. Per ciascun candidato, determina la catena di dipendenze mancanti e il costo cumulativo aggiuntivo.
  4. Interroga `score_wrapper.py` sul potenziale set $S + \text{missing}$ per calcolare il guadagno $\Delta score$.
  5. Calcola il Gain Ratio:
     $$Ratio = \frac{\Delta score}{Costo_{aggiuntivo}}$$
  6. Sceglie l'azione/catena con il **miglior $Gain Ratio$ positivo** che rispetta il budget residuo.
  7. Aggiorna lo stato $S$, sottrae il costo dal budget residuo e ricalcola lo score corrente.
  8. L'algoritmo termina quando il budget è esaurito oppure quando nessuna azione residua apporta un miglioramento al sistema ($\Delta score \le 0$).


### Scelte Progettuali Fondamentali

* **Ricalcolo Dinamico ad Ogni Passo (No tabella statica)**:
  L'algoritmo **non** usa una tabella delle performance statica pre-calcolata. Poiché il modello probabilistico sottostante mostra interazioni non-lineari tra le contromisure, l'incremento $\Delta score$ fornito da un'azione varia in base al set di azioni $S$ *già applicate*. Pertanto, l'incremento viene valutato dinamicamente ad ogni iterazione rispetto allo **stato corrente**.

* **Risoluzione Automatica delle Catene di Prerequisiti**:
  L'algoritmo non valuta mai un'azione di livello 2 in modo isolato (cosa che fallirebbe per prerequisito mancante), ma valuta l'intero pacchetto *"Prerequisiti Mancanti + Azione Desiderata"*, allocando il costo corretto e permettendo la selezione di azioni ad alto rendimento che richiedono un investimento propedeutico.


---

## Analisi di sensibilità al trust iniziale

> Nota: test condotto su una variante semplificata del modello di trust con relazioni dirette `appOp→cloudOp` e `appOp→edgeOp` . Ho adottato questa versione per isolare l'effetto del trust sullo score senza introdurre la complessità di modellare trust per ogni operatore del catalogo azioni. Il prossimo passo è testare su `weatherExampleWithTrust.pl`.

Test condotto su `weatherApp` con budget fisso a 300, dove vengono confrontate sei configurazioni di trust:

| Configurazione | Baseline | Azioni | Score finale | Δscore | Costo |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Trust originale (cloud=1.0, edge=1.0)** | 0.873000 | A9, A8, A7 | 0.987525 | +0.114525 | 290 |
| **Solo cloud ridotto (cloud=0.9, edge=1.0)** | 0.792000 | A1, A2, A5 | 0.980100 | +0.188100 | 240 |
| **Solo edge ridotto (cloud=1.0, edge=0.9)** | 0.873000 | A9, A8, A7 | 0.987525 | +0.114525 | 290 |
| **Solo edge ridotto (cloud=1.0, edge=0.7)** | 0.873000 | A9, A8, A7 | 0.987525 | +0.114525 | 290 |
| **Solo edge ridotto (cloud=1.0, edge=0.5)** | 0.873000 | A9, A8, A7 | 0.987525 | +0.114525 | 290 |
| **Cloud e edge ridotti (cloud=0.9, edge=0.9)** | 0.785700 | A9, A8, A7 | 0.888772 | +0.103073 | 290 |

**OSSERVAZIONI:**

**1. L'edge trust da solo non ha alcun effetto**
Le configurazioni con `cloud=1.0` e trust edge a 0.9, 0.7 e 0.5 producono baseline, azioni selezionate e score finale identici al caso di trust originale (0.873000 / A9, A8, A7 / 0.987525). Riducendo il trust dell'edge fino al 50% il comportamento non cambia: finché il cloud resta a trust pieno, l'edge non influisce sullo score. Sembra essere coerente con la saturazione via disgiunzione già documentata per A5 nella sezione sperimentale sul greedy.

**2. Il trust ridefinisce la strategia ottima, non solo il punto di partenza**
Il greedy seleziona un set di azioni completamente diverso nei seguenti scenari:
- Trust Originale → A9, A8, A7 → rinforza le catene cloud/edge, nonostante rendimento marginale basso (rapporto 0.000202 su A8)
- Trust Cloud Ridotto → A1, A2, A5 → preferisce catene alternative, coerentemente con l'intuizione che non convenga investire ulteriormente su un canale già poco affidabile (cioè con un trust basso)

**3. Δscore e costo utilizzato**
Nonostante un baseline più basso, lo scenario a trust cloud ridotto produce un guadagno totale maggiore (+0.1881 vs +0.1145) a parità di budget disponibile (300). Un trust iniziale più basso lascia un margine di miglioramento più ampio ed economico da colmare tramite azioni a basso costo/alto guadagno marginale: il greedy si ferma infatti con un costo effettivamente utilizzato inferiore (240 vs 290).

**4. Anomalia da verificare — possibile effetto soglia**
Riducendo sia cloud che edge (0.9/0.9), il greedy ritorna a selezionare A9/A8/A7, ma con uno score finale peggiore (0.888772 contro ~0.98 negli altri scenari), a parità di costo (290). Se il valore di baseline sarà confermato (vedi avviso sopra), questo suggerirebbe un comportamento non monotono del greedy: in questo scenario specifico, la catena A1/A2/A5 potrebbe risultare più conveniente di A9/A8/A7, ma il greedy non lo rileva. Da confrontare con Brute Force.

> OSSERVAZIONE: il test dimostra che il modello non è solo formalmente corretto ma anche comportamentalmente coerente rispetto a variazioni realistiche delle assunzioni di fiducia. Il punto 4, se confermato, fornirebbe inoltre un caso empirico diretto di sub-ottimalità del greedy, utile per la sezione di confronto greedy vs ottimo.

**Prossimi passi**:
- Testare su `weatherExampleWithTrust.pl`
- Eseguire Brute Force sullo scenario `cloud=0.9, edge=0.9` e confrontare con il risultato greedy
- Estendere l'analisi all'esempio `smartBuilding`

--- 

## Risultati sperimentali dell'algoritmo greedy

### 1. Dinamica del Budget e Allocazione
* **Budget = 300**: L'algoritmo seleziona `[A9, A8, A7]` (azioni Cloud Livello 1) ottenendo un $\Delta\text{score} = +0.114525$ con un costo di $290/300$. Il ratio beneficio/costo decresce in modo strettamente monotono ($0.001091 \to 0.000202 \to 0.000050$), confermando la corretta logica della ricerca greedy.

```
INFO: Baseline score: 0.873000 | Budget: 300
INFO: Azione selezionata: A9 | Catena: A9 | Costo: 80 | Guadagno: +0.087300 | Rapporto: 0.001091 | Budget residuo: 220
INFO: Azione selezionata: A8 | Catena: A8 | Costo: 110 | Guadagno: +0.022275 | Rapporto: 0.000202 | Budget residuo: 110
INFO: Azione selezionata: A7 | Catena: A7 | Costo: 100 | Guadagno: +0.004950 | Rapporto: 0.000050 | Budget residuo: 10
INFO: Nessuna azione migliorativa disponibile nel budget residuo: STOP.

============================================================
RISULTATO GREEDY (budget=300)
============================================================
Azioni selezionate: ['A9', 'A8', 'A7']
Score finale: 0.987525
Δscore totale: +0.114525
Costo totale usato: 290
```

* **Budget = 1000**: Vengono selezionate `[A9, A8, A10, A7, A11]` ($\Delta\text{score} = +0.124400$, costo $570/1000$). L'algoritmo arresta l'esecuzione lasciando $430$ unità di budget inutilizzate: i candidati economici residui (`A1`, `A3`, `A4`, `A5`) non offrono alcun guadagno marginale nello stato corrente.


```
INFO: Baseline score: 0.873000 | Budget: 1000
INFO: Azione selezionata: A9 | Catena: A9 | Costo: 80 | Guadagno: +0.087300 | Rapporto: 0.001091 | Budget residuo: 920
INFO: Azione selezionata: A8 | Catena: A8 | Costo: 110 | Guadagno: +0.022275 | Rapporto: 0.000202 | Budget residuo: 810
INFO: Azione selezionata: A10 | Catena: A10 | Costo: 150 | Guadagno: +0.008436 | Rapporto: 0.000056 | Budget residuo: 660
INFO: Azione selezionata: A7 | Catena: A7 | Costo: 100 | Guadagno: +0.004992 | Rapporto: 0.000050 | Budget residuo: 560
INFO: Azione selezionata: A11 | Catena: A11 | Costo: 130 | Guadagno: +0.001397 | Rapporto: 0.000011 | Budget residuo: 430
INFO: Nessuna azione migliorativa disponibile nel budget residuo: STOP.

============================================================
RISULTATO GREEDY (budget=1000)
============================================================
Azioni selezionate: ['A9', 'A8', 'A10', 'A7', 'A11']
Score finale: 0.997400
Δscore totale: +0.124400
Costo totale usato: 570
```

> Nota: All'aumentare del budget $B$, aumenta il numero di chiamate a SecFig, determinando una crescita lineare (da testare) del tempo totale dovuta al ricalcolo dinamico dello score. Infatti, si può osservare sperimentalmente che con budget alzato a 1000 l'algoritmo impiega più tempo rispetto a quando il budget = 300. 

### 2. Necessità del Ricalcolo Dinamico di $\Delta\text{score}$
La decisione architetturale di ricalcolare $\Delta\text{score}$ ad ogni step (anziché fare affidamento su una `gain_table` statica) trova una **conferma sperimentale diretta**:

* **Prestazione Isolata**: L'azione `A5` (Edge Access Control) presenta isolatamente il secondo miglior rapporto beneficio/costo dell'intero catalogo ($\Delta\text{score} = +0.0774$, costo $120$).

```
>> python3 debug_A5.py
Step 1: baseline
baseline: 0.873
Step 2: crea pl per A5
PL generato, lunghezza: 904
Step 3: chiamo score(['A5'])
Risultato A5: 0.9504
Step 4: chiamo delta_score(['A5'])
Delta A5: 0.07740000000000002
Step 5: gain marginale di A5 DOPO A9+A8+A10+A7
score prima: 0.99600375
score dopo A5: 0.99600375
gain marginale A5: 0.0
```

$$\text{score}([A9, A8, A10, A7]) = 0.99600375$$
$$\text{score}([A9, A8, A10, A7, A5]) = 0.99600375 \implies \text{Gain Marginale} = 0.0$$

> OSS: La regola Prolog sottostante adotta disgiunzioni nei requisiti: `securityRequirements(weatherMonitor, N) :- (anti_tampering(N) ; access_control(N)), ...`. Una volta che il nodo Cloud ha già soddisfatto la clausola tramite `A7-A10`, rinforzare l'Edge non apre nuovi percorsi nel *proof tree* Prolog. 
> OSS: Un approccio basato su tabella statica (gain_table) avrebbe selezionato `A5` sprecando budget; il ricalcolo dinamico rileva invece un guadagno marginale nullo e la scarta.

---

### 3. Gestione delle Catene Multi-livello e Dipendenze
La funzione di risoluzione delle dipendenze (`_missing_chain`) è stata verificata con successo:

```
>>python3 debug_chain.py
baseline: 0.873

Candidato A2 con S=[]:
 catena mancante: ['A1', 'A2']
 costo cumulativo: 120
 gain cumulativo: +0.067500

Candidato A6 con S=[]:
 catena mancante: ['A5', 'A6']
 costo cumulativo: 220
 gain cumulativo: +0.107100

Candidato A2 con S=['A1'] (A1 già presente):
  catena mancante: ['A2']  <- deve essere solo ['A2'], non ['A1','A2']
```

* **Espansione e Deduplicazione**: L'invocazione di `A2` con stato vuoto genera correttamente la catena `['A1', 'A2']` (costo $120$). Se `A1` è già presente nello stato, viene generata la sola singola azione `['A2']`.
* **Path Dependency**:
  * La catena `['A5', 'A6']` valutata su stato vuoto genera un incremento di $+0.1071$ (il più alto tra le catene testate).
  * L'azione `A6` aggiunge un guadagno marginale pieno solo se applicata **prima** che il Cloud saturi i requisiti di sistema, dimostrando come l'ordine e il contesto di applicazione determinino il valore reale di ogni misura di sicurezza.


---

## PROSSIMI PASSI
- Implementare Brute Force e ripetere i test per confrontare i risultati con quelli del Greedy
- Implementare MILP 
- Ritestare tutto su `smartBuildingExample.pl`
- Esperimento sistematico greedy vs Brute Force vs MILP (cioè creando una griglia di budget e testare su entrambi i deployment e annotare score finale, distanza rispetto alla soluzione ottima, tempo di esecuzione e budget residuo)
> Nota: Un argomento interessante da esplorare potrebbe essere se sia vantaggioso risparmiare (più budget rimanente) quando spendere di più non comporta un significativo aumento dei benefici.
- Analisi di complessità/scalabilità (sopratutto legato alle chiamate a SecFog)
- Test su weatherExampleWithTrust.pl (da valutare)
