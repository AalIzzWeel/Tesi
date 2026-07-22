"""greedy.py — Algoritmo Greedy per l'ottimizzazione budget-constrained.

Ad ogni iterazione sceglie l'azione (o catena azione+prerequisiti mancanti)
con il miglior rapporto Δscore/costo tra quelle che rientrano nel budget
residuo. Ricalcola i delta dallo STATO CORRENTE ad ogni passo (non usa
gain_table statica), perché il modello mostra interazioni non lineari tra
azioni (vedi test in score_wrapper.py).
"""

import logging
from typing import List, Optional, Tuple

from action_catalog import ACTIONS, get_action
from score_wrapper import score, order_by_prerequisites

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def _incremental_cost(missing_ids: List[str]) -> int:
    return sum(get_action(aid)['cost'] for aid in missing_ids)


def _missing_chain(candidate_id: str, current_list: List[str]) -> List[str]:
    """Catena di id (prerequisiti + candidato) non ancora selezionati,
    in ordine di applicazione corretto."""
    full_chain = order_by_prerequisites(current_list + [candidate_id])
    current_set = set(current_list)
    return [aid for aid in full_chain if aid not in current_set]


def greedy_search(budget: int, verbose: bool = True) -> Tuple[List[str], float, float]:
    """Esegue la ricerca greedy.

    Returns:
        (S, score_finale, delta_score_totale)
    """
    S: List[str] = []
    remaining_budget = budget

    s0 = score([])
    current_score = s0
    all_ids = [a['id'] for a in ACTIONS]

    if verbose:
        logging.info(f"Baseline score: {s0:.6f} | Budget: {budget}")

    while True:
        best_id: Optional[str] = None
        best_ratio: float = -1.0
        best_missing: List[str] = []
        best_gain: float = 0.0
        best_cost: int = 0

        candidates = [aid for aid in all_ids if aid not in S]
        if not candidates:
            break

        for aid in candidates:
            missing = _missing_chain(aid, S)
            cost = _incremental_cost(missing)

            if cost == 0 or cost > remaining_budget:
                continue

            candidate_score = score(S + missing)
            gain = candidate_score - current_score

            if gain <= 0:
                continue

            ratio = gain / cost
            if ratio > best_ratio:
                best_ratio = ratio
                best_id = aid
                best_missing = missing
                best_gain = gain
                best_cost = cost

        if best_id is None:
            if verbose:
                logging.info("Nessuna azione migliorativa disponibile nel budget residuo: STOP.")
            break

        # Aggiornamento dello stato corrente del sistema
        S.extend(best_missing)
        remaining_budget -= best_cost
        current_score += best_gain

        if verbose:
            chain_str = "+".join(best_missing)
            logging.info(
                f"Azione selezionata: {best_id} | Catena: {chain_str} | "
                f"Costo: {best_cost} | Guadagno: {best_gain:+.6f} | "
                f"Rapporto: {best_ratio:.6f} | Budget residuo: {remaining_budget}"
            )

    total_delta = current_score - s0
    return S, current_score, total_delta


if __name__ == "__main__":
    BUDGET_TEST = 300
    #BUDGET_TEST = 1000
    S, final_score, delta = greedy_search(BUDGET_TEST)

    print("\n" + "=" * 60)
    print(f"RISULTATO GREEDY (budget={BUDGET_TEST})")
    print("=" * 60)
    print(f"Azioni selezionate: {S}")
    print(f"Score finale: {final_score:.6f}")
    print(f"Δscore totale: {delta:+.6f}")
    print(f"Costo totale usato: {sum(get_action(a)['cost'] for a in S)}")