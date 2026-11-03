import math

def load_mcdp_instance(filepath):
  """Charge une instance du Multi-Compartment Delivery Problem

  selon la structure exacte de loadInstance1.h.h.
  """
  with open(filepath, "r") as f:
    tokens = f.read().split()

  idx = 0

  def next_int():
    nonlocal idx
    val = int(float(tokens[idx]))
    idx += 1
    return val

  def next_float():
    nonlocal idx
    val = float(tokens[idx])
    idx += 1
    return val

  # En-tête : stations (n), produits (m), compartiments (comps), véhicules (K), périodes (H)
  n = next_int()
  m = next_int()
  comps = next_int()
  K = next_int()
  H = next_int()

  V = list(range(0, n + 1))
  V_prime = list(range(1, n + 1))
  M = list(range(1, m + 1))
  L = list(range(1, comps + 1))
  K_set = list(range(1, K + 1))
  T = list(range(1, H + 1))

  coor_x = [0] * (n + 1)
  coor_y = [0] * (n + 1)

  # Coordonnées du dépôt (noeud 0)
  coor_x[0] = next_int()
  coor_y[0] = next_int()

  # Capacités des compartiments : Q[l, k]
  Q = {}
  for k in K_set:
    for l in L:
      Q[l, k] = next_int()

  # Données des stations-service (noeuds 1 à n)
  I0, d, C, h = {}, {}, {}, {}
  for i in V_prime:
    coor_x[i] = next_int()
    coor_y[i] = next_int()

    for prod in M:
      I0[i, prod] = next_int()

    for prod in M:
      for t in T:
        d[i, prod, t] = next_int()

    for prod in M:
      C[i, prod] = next_int()
      h[i, prod] = next_float()

  # Matrice des distances euclidiennes arrondies à l'entier le plus proche
  c = {}
  for i in V:
    for j in V:
      if i != j:
        d_eucl = math.sqrt(
            (coor_x[i] - coor_x[j]) ** 2 + (coor_y[i] - coor_y[j]) ** 2
        )
        c[i, j] = int(math.floor(d_eucl + 0.5))
      else:
        c[i, j] = 0

  return {
      "n": n,
      "m": m,
      "comps": comps,
      "K": K,
      "T_max": H,
      "V": V,
      "V_prime": V_prime,
      "M": M,
      "L": L,
      "K_set": K_set,
      "T": T,
      "Q": Q,
      "I0": I0,
      "d": d,
      "C": C,
      "h": h,
      "c": c,
  }