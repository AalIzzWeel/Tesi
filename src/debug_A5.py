''' Misura il marginal gain (guadagno marginale) di A5. 
    Serve a verificare se la sicurezza scala in modo non lineare, 
    ovvero se A5 porta lo stesso identico beneficio quando il sistema è già parzialmente protetto da altre 4 azioni, 
    oppure se il suo valore relativo diminuisce/aumenta. '''

import sys
print("Python:", sys.executable)

from score_wrapper import score, delta_score, BASELINE, apply_actions, build_pl

print("Step 1: baseline")
s0 = score([])
print("baseline:", s0)

print("Step 2: crea pl per A5")
state = apply_actions(BASELINE, ['A5'])
pl = build_pl(state)
print("PL generato, lunghezza:", len(pl))

print("Step 3: chiamo score(['A5'])")
result = score(['A5'])
print("Risultato A5:", result)

print("Step 4: chiamo delta_score(['A5'])")
d = delta_score(['A5'], s0=s0)
print("Delta A5:", d)

print("Step 5: gain marginale di A5 DOPO A9+A8+A10+A7")
base_seq = ['A9', 'A8', 'A10', 'A7']
score_before = score(base_seq)
score_after = score(base_seq + ['A5'])
print("score prima:", score_before)
print("score dopo A5:", score_after)
print("gain marginale A5:", score_after - score_before)