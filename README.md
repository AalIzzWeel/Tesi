# Ottimizzazione budget-constrained della sicurezza in deployment Cloud-Edge

Implementazione e confronto sperimentale di algoritmi (Greedy, Brute Force, MILP) per la selezione ottimale di azioni di miglioramento della sicurezza, sotto vincolo di budget, su deployment valutati con SecFog (Forti et al., 2020).

---

## Problema

Dato un deployment `D` con uno score di sicurezza SecFog e un budget `B`, trovare il sottoinsieme di azioni di miglioramento che massimizza l'aumento di score rispettando `B`. 
OSS: Formalizzato come variante di knapsack con vincoli di precedenza (NP-hard), per la presenza di catene di prerequisiti tra azioni.

---

TBC

**Settimana 2: Riscrivere il Greedy e creare l'euristica** 
* Riaddattare il greedy e testare
* Primo run completo su smartBuilding con budget diversi
* Capire come gestire l'eventuale budget residuo

> Nota: due settimane SE non ci sono grandi problemi di debugging
