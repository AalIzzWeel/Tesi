# Ottimizzazione budget-constrained della sicurezza in deployment Cloud-Edge

Implementazione e confronto sperimentale di algoritmi (Greedy, Brute Force, MILP) per la selezione ottimale di azioni di miglioramento della sicurezza, sotto vincolo di budget, su deployment valutati con SecFog (Forti et al., 2020).

---

## Problema

Dato un deployment `D` con uno score di sicurezza SecFog e un budget `B`, trovare il sottoinsieme di azioni di miglioramento che massimizza l'aumento di score rispettando `B`. 
OSS: Formalizzato come variante di knapsack con vincoli di precedenza (NP-hard), per la presenza di catene di prerequisiti tra azioni.

---

## Architettura del progetto (bozza: 24/07/26)
```
tesi/
├── model/
│   ├── formalization.py  # dataclass: Nodo, Contromisura, Livello, Policy
│   ├── policy.py # funzioni per applicare le policy da assegnazione livelli
├── scoring/
│   ├── score_wrapper.py  # da adattare 
├── algorithms/
│   ├── greedy.py # adattare: gruppi invece di azioni singole
│   ├── brute_force.py  # da fare se avanza tempo
│   ├── milp.py # da fare se avanza tempo
├── experiments/
│   ├── run_experiments.py  # loop su deployment × budget × algoritmo usando smartBuilding
│   ├── results/ # output leggibile (csv o json)
├── README.md
```

## Domande da fare
1. Da uno stato inattivo, il greedy può proporre direttamente un salto a un livello alto (es. anti-tampering2) come singola azione 'add', oppure deve necessariamente passare prima per un add a livello base e poi modify sequenziali verso l'alto? Nel primo caso, una volta aggiunto anti-tampering2, posso "degradarlo" di livello nelle iterazioni successive?

## Piano (bozza)

**Settimana 1:** 
* Implementare i livelli come fatti ProbLog indipendenti (tipo anti-tampering0/1/2) + test dello score
* Costruire il catalogo a gruppi per smartBuilding: per ogni (𝑛,𝑖), lista livelli + costi indipendenti + stato iniziale (attivo/inattivo).
* Testare score()
* Implementare le hashmap
* Implementare net_cost() per modify (delta rispetto al livello corrente) e costo assoluto per add.

> Nota: L'obiettivo di questa settimana è scrivere una funzione che, dato uno stato e un budget, produce la lista corretta di mosse fattibili.

**Settimana 2: Riscrivere il Greedy e creare l'euristica** 
* Riaddattare il greedy e testare
* Primo run completo su smartBuilding con budget diversi
* Capire come gestire l'eventuale budget residuo

> Nota: due settimane SE non ci sono grandi problemi di debugging
