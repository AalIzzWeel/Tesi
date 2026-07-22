"""
Catalogo azioni: weatherExample.pl con baseline modificato
Uso la Tassonomia definita nel paper di SecFog
Livelli progressivi: l'azione di livello 2 richiede il livello 1 come prerequisito.
"""

#Nota per il futuro: la baseline poi verrà definita in un file esterno
BASELINE = {
    'cloud': {
        'anti_tampering': 0.85, #prima era 0.99
        'access_control': 0.80, #prima era 0.99
        'iot_data_encryption': 0.90, #prima era 0.99
        'wireless_security': 0.0, #non dichiarato in weatherExample.pl, quindi 0.0
    },
    'edge': {
        'anti_tampering': 0.80,
        'wireless_security': 0.90,
        'iot_data_encryption': 0.90,
        'access_control': 0.0, #non dichiarato in weatherExample.pl, quindi 0.0
    }
}

#NOTA PER IL FUTURO: decidere se definire azioni più generali (e aggiungere controlli nell'algoritmo greedy) 
#o definire azioni specifiche per ogni nodo e capacità (in questo caso mi limito strettamente all'esercizio scelto).
""" 
In questo catalogo, le azioni sono definite come dizionari con i seguenti campi:
- 'id': identificatore univoco dell'azione
- 'type': tipo di azione ('improve' o 'buy')
- 'node': nodo a cui si applica l'azione ('edge' o 'cloud')
- 'capability': capacità che l'azione migliora o acquista
- 'category': categoria della capacità ('Fisico', 'Comunicazione', 'Dati', 'Virtualizzazione')
- 'p_before': probabilità prima dell'azione 
- 'p_after': probabilità dopo l'azione
- 'cost': costo dell'azione
- 'level': livello dell'azione (1 o 2)
- 'requires': azione prerequisito (se presente)
- 'description': descrizione dell'azione
"""

ACTIONS = [
    # nodo EDGE
    {
        'id': 'A1',
        'type': 'improve',
        'node': 'edge',
        'capability': 'anti_tampering',
        'category': 'Fisico',
        'p_before': 0.80, 'p_after': 0.90,
        'cost': 50,
        'level': 1, 'requires': None,
        'description': 'anti-tampering edge: 0.80 --> 0.90'
    },
    {
        'id': 'A2',
        'type': 'improve',
        'node': 'edge',
        'capability': 'anti_tampering',
        'category': 'Fisico',
        'p_before': 0.90, 'p_after': 0.95,  # parte da 0.90, non 0.80 (livello 2)
        'cost': 70, # costo del solo salto 0.90 --> 0.95
        'level': 2, 'requires': 'A1',
        'description': 'anti-tampering edge: 0.90 --> 0.95'
    },
    {
        'id': 'A5',
        'type': 'buy',
        'node': 'edge',
        'capability': 'access_control',
        'category': 'Fisico',
        'p_before': 0.0, 'p_after': 0.80,
        'cost': 120,
        'level': 1, 'requires': None,
        'description': 'access_control edge: 0 --> 0.80'
    },
    {
        'id': 'A6',
        'type': 'improve',
        'node': 'edge',
        'capability': 'access_control',
        'category': 'Fisico',
        'p_before': 0.80, 'p_after': 0.95,   # parte da 0.80, non 0.0
        'cost': 100,
        'level': 2, 'requires': 'A5',
        'description': 'access_control edge: 0.80 --> 0.95'
    },

    {
        'id': 'A3',
        'type': 'improve',
        'node': 'edge',
        'capability': 'wireless_security',
        'category': 'Comunicazione',
        'p_before': 0.90, 'p_after': 0.99,
        'cost': 80,
        'level': 1, 'requires': None,
        'description': 'wireless_security edge: 0.90 --> 0.99'
    },
    {
        'id': 'A4',
        'type': 'improve',
        'node': 'edge',
        'capability': 'iot_data_encryption',
        'category': 'Comunicazione',
        'p_before': 0.90, 'p_after': 0.99,
        'cost': 80,
        'level': 1, 'requires': None,
        'description': 'iot_data_encryption edge: 0.90 --> 0.99'
    },

    # CLOUD
    {
        'id': 'A7',
        'type': 'improve',
        'node': 'cloud',
        'capability': 'anti_tampering',
        'category': 'Fisico',
        'p_before': 0.85, 'p_after': 0.95,
        'cost': 100,
        'level': 1, 'requires': None,
        'description': 'anti-tampering cloud: 0.85 --> 0.95'
    },
    {
        'id': 'A8',
        'type': 'improve',
        'node': 'cloud',
        'capability': 'access_control',
        'category': 'Fisico',
        'p_before': 0.80, 'p_after': 0.95,
        'cost': 110,
        'level': 1, 'requires': None,
        'description': 'access_control cloud: 0.80 --> 0.95'
    },

    {
        'id': 'A9',
        'type': 'improve',
        'node': 'cloud',
        'capability': 'iot_data_encryption',
        'category': 'Comunicazione',
        'p_before': 0.90, 'p_after': 0.99,
        'cost': 80,
        'level': 1, 'requires': None,
        'description': 'iot_data_encryption cloud: 0.90 --> 0.99'
    },
    {
        'id': 'A10',
        'type': 'buy',
        'node': 'cloud',
        'capability': 'wireless_security',
        'category': 'Comunicazione',
        'p_before': 0.0, 'p_after': 0.85,
        'cost': 150,
        'level': 1, 'requires': None,
        'description': 'wireless_security cloud: 0 --> 0.85'
    },
    {
        'id': 'A11',
        'type': 'improve',
        'node': 'cloud',
        'capability': 'wireless_security',
        'category': 'Comunicazione',
        'p_before': 0.85, 'p_after': 0.99,   # parte da 0.85, non 0.0
        'cost': 130,
        'level': 2, 'requires': 'A10',
        'description': 'wireless_security cloud: 0.85 --> 0.99'
    },
]

def print_catalog():
    cats = ['Fisico', 'Comunicazione', 'Dati', 'Virtualizzazione', 'Other']
    for cat in cats:
        actions = [a for a in ACTIONS if a['category'] == cat]
        if not actions:
            continue
        print(f"\n Categoria: {cat}")
        print(f"  {'ID':<5} {'T':<8} {'Nodo':<7} {'Capability':<22}"
              f"{'p_bef':>6} {'p_aft':>6} {'Costo':>6} {'Lv':>3} {'Req':>5}")
        print("  " + "─" * 68)
        for a in actions:
            req = a['requires'] or '—'
            print(f"  {a['id']:<5} {a['type']:<8} {a['node']:<7}"
                  f"{a['capability']:<22}{a['p_before']:>6.2f}"
                  f"{a['p_after']:>6.2f} {a['cost']:>6}"
                  f"{a['level']:>3}  {req:>4}")

# Funzione per recuperare azioni e prerequisiti da un ID di azione
def get_action(aid):
    return next((a for a in ACTIONS if a['id'] == aid), None) # Restituisce l'azione con l'ID specificato, o None se non esiste.

# Funzione per ottenere la catena completa di prerequisiti per un'azione
def get_prerequisites(aid):
    chain = []
    current = get_action(aid)
    while current and current['requires']:
        current = get_action(current['requires'])
        chain.insert(0, current)
    return chain

if __name__ == '__main__':
    print_catalog()
    print(f"\nTotale azioni: {len(ACTIONS)}")
    print(f"Costo totale (tutte): {sum(a['cost'] for a in ACTIONS)}")
    print(f"\nCosto effettivo cumulativo con prerequisiti:")
    for a in ACTIONS:
        prereqs = get_prerequisites(a['id'])
        total = sum(p['cost'] for p in prereqs) + a['cost']
        chain = ' → '.join([p['id'] for p in prereqs] + [a['id']])
        print(f"  {chain:<15} costo cumulativo: {total}")