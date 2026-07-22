''' Test di verifica per la gestione delle prerequisiti e delle catene di dipendenza multi-livello
    Lo scopo principale del codice è testare due funzioni chiave dell' algoritmo greedy (_missing_chain e _incremental_cost)
    in tre scenari specifici, per assicurarmi che l'espansione delle azioni avvenga correttamente e senza duplicazioni.
'''

from action_catalog import get_action
from score_wrapper import score
from greedy import _missing_chain, _incremental_cost

s0 = score([])
print("baseline:", s0)

# Caso 1: A2 (livello 2, richiede A1) quando S è vuoto
S = []
missing = _missing_chain('A2', S)
cost = _incremental_cost(missing)
gain = score(S + missing) - score(S)
print(f"\nCandidato A2 con S=[]:")
print(f" catena mancante: {missing}")
print(f" costo cumulativo: {cost}")
print(f" gain cumulativo: {gain:+.6f}")

# Caso 2: A6 (livello 2, richiede A5) quando S è vuoto
missing6 = _missing_chain('A6', S)
cost6 = _incremental_cost(missing6)
gain6 = score(S + missing6) - score(S)
print(f"\nCandidato A6 con S=[]:")
print(f" catena mancante: {missing6}")
print(f" costo cumulativo: {cost6}")
print(f" gain cumulativo: {gain6:+.6f}")

# Caso 3: A2 quando A1 è GIA' in S (deve restituire solo ['A2'])
S_with_A1 = ['A1']
missing_after = _missing_chain('A2', S_with_A1)
print(f"\nCandidato A2 con S=['A1'] (A1 già presente):")
print(f"  catena mancante: {missing_after}  <- deve essere solo ['A2'], non ['A1','A2']")