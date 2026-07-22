"""score_wrapper.py : Wrapper tra Python e ProbLog.


Questo script funge da oracolo per il calcolo della funzione obiettivo dell'algoritmo.
Prende le contromisure selezionate dall'ottimizzatore, aggiorna lo stato del sistema,
genera il file Prolog corrispondente e invoca ProbLog per calcolare la sicurezza
attesa del deployment.
"""


import copy
import logging
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set


# Importazione delle funzioni dal catalogo delle azioni
from action_catalog import ACTIONS, BASELINE, get_action, get_prerequisites

# Configurazione del logging per il tracciamento di anomalie o skip
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


# --- PERCORSI E CONFIGURAZIONI GLOBALI ---


# Directory principale del framework SecFog
SECFOG_DIR = Path(__file__).resolve().parent.parent / "SecFog"


# File principale contenente le regole logiche di base di SecFog
SECFOG_CORE = SECFOG_DIR / "secfog.pl"


# File esterno contenente i requisiti specifici dell'applicazione
REQUIREMENTS_FILE = Path(__file__).resolve().parent / "requirements.pl"


# Espressione regolare per estrarre il valore numerico dello score dall'output di ProbLog
SCORE_REGEX = re.compile(r"secFog\(.*?\):\s+([\d.e+-]+)")


# Cache globale per memorizzare gli score già calcolati ed evitare chiamate ridondanti
# Uso esclusivo interno al wrapper
_SCORE_CACHE: Dict[frozenset, float] = {}




# ------ FUNZIONI DI SUPPORTO -----------------------------------------------------------------


def load_requirements() -> str:
    """Carica i requisiti dal file esterno.
   
    In caso di assenza o errore di lettura, solleva un'eccezione.
    """
    if not REQUIREMENTS_FILE.exists():
        logging.critical(f"File dei requisiti non trovato in: {REQUIREMENTS_FILE}")
        raise FileNotFoundError(f"Manca il file di configurazione: {REQUIREMENTS_FILE}")


    try:
        return REQUIREMENTS_FILE.read_text().strip()
    except IOError as e:
        logging.error(f"Errore di lettura del file dei requisiti: {e}")
        return ""




def apply_actions(baseline: Dict[str, Dict[str, float]], action_ids: List[str]) -> Dict[str, Dict[str, float]]:
    """Applica la lista di azioni selezionate allo stato di baseline del sistema.
   
    Verifica la validità delle azioni, il rispetto dei prerequisiti e la coerenza
    dei valori di probabilità precedenti (p_before).
    """
    # Creazione di una copia deep dello stato iniziale
    state = copy.deepcopy(baseline)
    action_set = set(action_ids)


    for aid in action_ids:
        a = get_action(aid)
        if a is None:
            raise ValueError(f"L'azione '{aid}' non esiste nel catalogo.")


        # Verifica del prerequisito dell'azione
        req = a.get("requires")
        if req and req not in action_set:
            raise ValueError(f"L'azione '{aid}' richiede il prerequisito '{req}' non soddisfatto.")


        node = a["node"]
        cap = a["capability"]
        current = state[node].get(cap, 0.0)


        # Controllo di tolleranza sui float per evitare errori di arrotondamento
        # prima: if (current - a["p_before"]) > 0 che è stata modificata in una tolleranza di 1e-6 per evitare errori di arrotondamento
        if abs(current - a["p_before"]) > 1e-6:
            raise ValueError(
                f"Incoerenza per {node}.{cap}: atteso p_before {a['p_before']:.2f}, "
                f"rilevato {current:.2f}."
            )


        # Aggiornamento dello stato con la nuova probabilità
        state[node][cap] = a["p_after"]


    return state




def build_pl(state: Dict[str, Dict[str, float]]) -> str:
    """Genera il contenuto stringa del file sorgente Prolog finale.
   
    Unisce le regole core di SecFog, i requisiti applicativi e i fatti probabilistici
    derivanti dallo stato corrente del sistema.
    """
    core = SECFOG_CORE.read_text().strip() if SECFOG_CORE.exists() else ""
    reqs = load_requirements()


    lines = [core, reqs, ""]


    # Generazione dei fatti del modello e delle relative probabilità
    for node, caps in state.items():
        lines.append(f"node({node}, {node}Op).")
        for cap, prob in caps.items():
            if prob > 0.0:
                lines.append(f"{prob}::{cap}({node}).")
        lines.append("")


    # Definizione della query finale per ProbLog
    lines.append("query(secFog(appOp, weatherApp, D)).")
    return "\n".join(lines)




# --- FUNZIONI CORE DI VALUTAZIONE -----------------------------------------------------------------------


def score(action_ids: Optional[List[str]] = None) -> float:
    """Calcola lo score di sicurezza invocando ProbLog su un file temporaneo.
   
    Utilizza un sistema di caching interno per evitare computazioni ridondanti.
    """
    ids = action_ids or []
    key = frozenset(ids)


    # Controllo se il risultato è già presente in cache
    if key in _SCORE_CACHE:
        return _SCORE_CACHE[key]


    # Generazione dello stato e del codice Prolog corrispondente
    state = apply_actions(BASELINE, ids)
    pl_content = build_pl(state)


    # Creazione del file temporaneo ed esecuzione di ProbLog
    with tempfile.NamedTemporaryFile(mode="w", suffix=".pl", delete=False) as tmp_file:
        tmp_file.write(pl_content)
        tmp_path = Path(tmp_file.name)


    try:
        result = subprocess.run(
            ["python3", "-m", "problog", str(tmp_path)],
            capture_output=True, text=True, timeout=30, check=True,
        )
       
        # Estrazione dello score tramite regex (stile standard senza operatore walrus)
        scores = []
        for line in result.stdout.splitlines():
            match = SCORE_REGEX.search(line)
            if match:
                scores.append(float(match.group(1)))
               
        value = max(scores) if scores else 0.0
        _SCORE_CACHE[key] = value
        return value


    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Errore durante l'esecuzione di ProbLog:\n{e.stderr}") from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError("Il processo ProbLog ha superato il timeout di 30 secondi.") from e
    finally:
        # Rimozione sicura del file temporaneo
        tmp_path.unlink(missing_ok=True)




def delta_score(action_ids: List[str], s0: Optional[float] = None) -> float:
    """Calcola il guadagno netto di sicurezza rispetto allo score iniziale (baseline)."""
    base_score = s0 if s0 is not None else score([])
    return score(action_ids) - base_score




def gain_table(s0: Optional[float] = None) -> List[dict]:
    """Costruisce una tabella dei rendimenti per ciascuna azione del catalogo.
   
    Le azioni vengono ordinate in base al rapporto rendimento/costo (efficienza Greedy).
    """
    base_score = s0 if s0 is not None else score([])
    rows = []


    for a in ACTIONS:
        ids = [a["id"]]
        if a.get("requires"):
            ids = [a["requires"], a["id"]]
           
        try:
            g = delta_score(ids, s0=base_score)
            cost = sum(get_action(i)["cost"] for i in ids)
           
            rows.append({
                "id": a["id"],
                "description": a["description"],
                "category": a["category"],
                "gain": g,
                "cost": cost,
                "ratio": g / cost if cost > 0 else 0.0,
                "action_ids": ids,
            })
        except ValueError as e:
            logging.warning(f"Salto l'azione {a['id']} nei test: {e}")


    # Ordinamento decrescente in base al rapporto Gain/Cost
    rows.sort(key=lambda r: r["ratio"], reverse=True)
    return rows




def order_by_prerequisites(action_ids: List[str]) -> List[str]:
    """Ordina una lista di azioni assicurando che i prerequisiti precedano l'azione stessa."""
    ordered = []
    seen = set()


    for aid in action_ids:
        for prereq in get_prerequisites(aid):
            if prereq['id'] not in seen:
                ordered.append(prereq['id'])
                seen.add(prereq['id'])
        if aid not in seen:
            ordered.append(aid)
            seen.add(aid)


    return ordered




# --- BLOCCO DI VERIFICA E TEST ---------------------------------------------------------------------------


if __name__ == "__main__":
    print("=" * 60)
    print("TEST MODULO SCORE_WRAPPER")
    print("=" * 60)


    # 1. Calcolo dello score iniziale
    s0 = score([])
    print(f"\nScore della Baseline: {s0:.6f}\n")


    # 2. Valutazione dell'impatto isolato delle azioni di Livello 1
    print(f"{'ID':<5} {'Δscore':>10} {'Note'}")
    print("-" * 40)
    singles = [a["id"] for a in ACTIONS if a.get("level") == 1]
    for aid in singles:
        try:
            d = delta_score([aid], s0=s0)
            print(f"{aid:<5} {d:>+10.6f}")
        except ValueError as e:
            print(f"{aid:<5} {'SKIP':>10}  ({e})")


    # 3. Analisi delle non-linearità del modello interazione (A1 e A2)
    d1 = delta_score(["A1"], s0=s0)
    d12 = delta_score(["A1", "A2"], s0=s0)
    d2_marginal = d12 - d1
   
    print(f"\nA1 da sola: Δ={d1:+.6f}")
    print(f"A1 + A2 insieme: Δ={d12:+.6f}")
    print(f"Guadagno effettivo di A2 (con A1 attiva): {d2_marginal:+.6f}")
   
    is_nonlinear = abs(d12 - d1) > 1e-9
    print(f"→ Il modello riscontra non-linearità? {'SI' if is_nonlinear else 'NO'}")


    # 4. Stampa della Gain Table per la strategia Greedy
    print("\n" + "=" * 60)
    print("GAIN TABLE (Ordinata per rapporto guadagno/costo)")
    print("=" * 60)
    print(f"{'ID':<5} {'Categoria':<16} {'Gain':>8} {'Costo':>6} {'Ratio':>8}  Catena Azioni")
    print("-" * 70)
    for r in gain_table(s0=s0):
        print(f"{r['id']:<5} {r['category']:<16} {r['gain']:>8.5f} "
              f"{r['cost']:>6}  {r['ratio']:>8.5f}  "
              f"{'+'.join(r['action_ids'])}")