import math
import gurobipy as gp
from gurobipy import GRB


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


def solve_single_route_mcdp(data, time_limit=3600, break_symmetry=True, verbose=True):
  """Construit et résout le modèle MILP 'Unsplit Compartments - Split Tanks' (A0-A20)."""
  V = data["V"]
  V_prime = data["V_prime"]
  M = data["M"]
  L = data["L"]
  K_set = data["K_set"]
  T = data["T"]
  n = data["n"]
  Q = data["Q"]
  I0 = data["I0"]
  d = data["d"]
  C = data["C"]
  h = data["h"]
  c = data["c"]

  model = gp.Model("MCDP_SingleRoute")
  if not verbose:
    model.Params.OutputFlag = 0
  model.Params.TimeLimit = time_limit

  # =========================================================================
  # A.4 & A.10 : VARIABLES DE DÉCISION ET DOMAINES (A2 & A20)
  # =========================================================================

  # I[i, m, t] : stock à la fin de la période t (borné par C[i, m] selon A2)
  I = model.addVars(
      V_prime,
      M,
      T,
      lb=0.0,
      ub={
          (i, prod, t): C[i, prod] for i in V_prime for prod in M for t in T
      },
      vtype=GRB.CONTINUOUS,
      name="I",
  )

  # q[i, m, l, k, t] : quantité livrée
  q = model.addVars(
      V_prime, M, L, K_set, T, lb=0.0, vtype=GRB.CONTINUOUS, name="q"
  )

  # x[i, j, k, t] : routage sur les arcs dirigés (i != j)
  arcs = [(i, j) for i in V for j in V if i != j]
  x = model.addVars(arcs, K_set, T, vtype=GRB.BINARY, name="x")

  # y[i, k, t] : visite du noeud i (i=0 correspond à l'utilisation du véhicule k)
  y = model.addVars(V, K_set, T, vtype=GRB.BINARY, name="y")

  # w[m, l, k, t] : chargement du produit m dans le compartiment l
  w = model.addVars(M, L, K_set, T, vtype=GRB.BINARY, name="w")

  # z[i, m, l, k, t] : affectation du compartiment l au client i pour le produit m
  z = model.addVars(V_prime, M, L, K_set, T, vtype=GRB.BINARY, name="z")

  # u[i, k, t] : variables d'ordre MTZ pour l'élimination des sous-tours
  u = model.addVars(
      V_prime, K_set, T, lb=0.0, ub=float(n), vtype=GRB.CONTINUOUS, name="u"
  )

  # =========================================================================
  # A.5 : FONCTION OBJECTIF (A0)
  # =========================================================================
  holding_cost = gp.quicksum(
      h[i, prod] * I[i, prod, t] for i in V_prime for prod in M for t in T
  )
  routing_cost = gp.quicksum(
      c[i, j] * x[i, j, k, t] for (i, j) in arcs for k in K_set for t in T
  )

  model.setObjective(holding_cost + routing_cost, GRB.MINIMIZE)

  # =========================================================================
  # A.6 : CONTRAINTES DE STOCK (A1 - A3)
  # =========================================================================
  for i in V_prime:
    for prod in M:
      for t in T:
        prev_I = I0[i, prod] if t == 1 else I[i, prod, t - 1]
        delivered = gp.quicksum(
            q[i, prod, l, k, t] for l in L for k in K_set
        )

        # A1 : Équilibre des stocks
        model.addConstr(
            I[i, prod, t] == prev_I + delivered - d[i, prod, t],
            name=f"A1_{i}_{prod}_{t}",
        )

        # A3 : Espace disponible dans la cuve avant consommation
        model.addConstr(
            delivered <= C[i, prod] - prev_I,
            name=f"A3_{i}_{prod}_{t}",
        )

  # =========================================================================
  # A.7 : CONTRAINTES DE LIVRAISON ET COMPARTIMENTS (A4 - A12)
  # =========================================================================
  for k in K_set:
    for t in T:
      # A4 : Une livraison requiert la visite du client
      for i in V_prime:
        for prod in M:
          model.addConstr(
              gp.quicksum(q[i, prod, l, k, t] for l in L)
              <= C[i, prod] * y[i, k, t],
              name=f"A4_{i}_{prod}_{k}_{t}",
          )

      for l in L:
        for prod in M:
          # A6 : Capacité du compartiment
          model.addConstr(
              gp.quicksum(q[i, prod, l, k, t] for i in V_prime) <= Q[l, k],
              name=f"A6_{prod}_{l}_{k}_{t}",
          )

          for i in V_prime:
            # A5 & A10 : Livraison du compartiment complet (Unsplit compartments)
            # A5 (q <= Q*z) et A10 (q >= Q*z) combinées donnent q == Q*z
            model.addConstr(
                q[i, prod, l, k, t] <= Q[l, k] * z[i, prod, l, k, t],
                name=f"A5_{i}_{prod}_{l}_{k}_{t}",
            )
            model.addConstr(
                q[i, prod, l, k, t] >= Q[l, k] * z[i, prod, l, k, t],
                name=f"A10_{i}_{prod}_{l}_{k}_{t}",
            )

            # A7 : L'affectation requiert une visite
            model.addConstr(
                z[i, prod, l, k, t] <= y[i, k, t],
                name=f"A7_{i}_{prod}_{l}_{k}_{t}",
            )

            # A8 : L'affectation requiert que le produit soit chargé
            model.addConstr(
                z[i, prod, l, k, t] <= w[prod, l, k, t],
                name=f"A8_{i}_{prod}_{l}_{k}_{t}",
            )

        # A9 : Au plus un produit par compartiment
        model.addConstr(
            gp.quicksum(w[prod, l, k, t] for prod in M) <= 1,
            name=f"A9_{l}_{k}_{t}",
        )

        # A11 : Au plus un couple client/produit par compartiment (renforcement)
        model.addConstr(
            gp.quicksum(z[i, prod, l, k, t] for i in V_prime for prod in M)
            <= 1,
            name=f"A11_{l}_{k}_{t}",
        )

      # A12 : Tout client visité reçoit au moins un compartiment (renforcement)
      for i in V_prime:
        model.addConstr(
            gp.quicksum(z[i, prod, l, k, t] for prod in M for l in L)
            >= y[i, k, t],
            name=f"A12_{i}_{k}_{t}",
        )

  # =========================================================================
  # A.8 : CONTRAINTES DE ROUTAGE DIRIGÉ (A13 - A17)
  # =========================================================================
  for k in K_set:
    for t in T:
      for i in V_prime:
        # A13 : Exactement un arc sortant par client visité
        model.addConstr(
            gp.quicksum(x[i, j, k, t] for j in V if j != i) == y[i, k, t],
            name=f"A13_{i}_{k}_{t}",
        )
        # A14 : Exactement un arc entrant par client visité
        model.addConstr(
            gp.quicksum(x[j, i, k, t] for j in V if j != i) == y[i, k, t],
            name=f"A14_{i}_{k}_{t}",
        )
        # A17 : Un client ne peut être visité que par un véhicule actif
        model.addConstr(
            y[i, k, t] <= y[0, k, t],
            name=f"A17_{i}_{k}_{t}",
        )

      # A15 : Départ du dépôt
      model.addConstr(
          gp.quicksum(x[0, j, k, t] for j in V_prime) == y[0, k, t],
          name=f"A15_{k}_{t}",
      )
      # A16 : Retour au dépôt
      model.addConstr(
          gp.quicksum(x[i, 0, k, t] for i in V_prime) == y[0, k, t],
          name=f"A16_{k}_{t}",
      )

  # =========================================================================
  # A.9 : ÉLIMINATION DES SOUS-TOURS MTZ (A18 - A19)
  # =========================================================================
  for k in K_set:
    for t in T:
      for i in V_prime:
        # A18 : Bornes de la variable d'ordre MTZ
        model.addConstr(u[i, k, t] >= y[i, k, t], name=f"A18_lb_{i}_{k}_{t}")
        model.addConstr(
            u[i, k, t] <= n * y[i, k, t], name=f"A18_ub_{i}_{k}_{t}"
        )

        for j in V_prime:
          if i != j:
            # A19 : Ordre MTZ sur les arcs entre clients
            model.addConstr(
                u[i, k, t] - u[j, k, t] + n * x[i, j, k, t] <= n - y[j, k, t],
                name=f"A19_{i}_{j}_{k}_{t}",
            )

  # =========================================================================
  # OPTIONNEL : CASSAGE DE SYMÉTRIE ENTRE CAMIONS IDENTIQUES
  # =========================================================================
  if break_symmetry and len(K_set) > 1:
    for t in T:
      for idx_k in range(len(K_set) - 1):
        k1, k2 = K_set[idx_k], K_set[idx_k + 1]
        # Si deux camions consécutifs ont les mêmes compartiments, on ordonne leur utilisation
        if all(Q[l, k1] == Q[l, k2] for l in L):
          model.addConstr(
              y[0, k1, t] >= y[0, k2, t], name=f"sym_veh_{k1}_{k2}_{t}"
          )

  # Résolution
  model.optimize()

  # =========================================================================
  # AFFICHAGE DES RÉSULTATS
  # =========================================================================
  if model.SolCount > 0:
    val_hold = holding_cost.getValue()
    val_rout = routing_cost.getValue()
    print("\n" + "=" * 65)
    print(f"RÉSULTATS DE LA RÉSOLUTION (Statut Gurobi : {model.Status})")
    print(
        f"Objectif Total   : {model.ObjVal:.2f} (Gap : {model.MIPGap*100:.2f}%)"
    )
    print(f" - Coût Routage  : {val_rout:.2f}")
    print(f" - Coût Stockage : {val_hold:.2f}")
    print(f"Temps de calcul  : {model.Runtime:.2f} s")
    print("=" * 65)

    for t in T:
      print(f"\n--- PÉRIODE t = {t} ---")
      active_vehicles = [k for k in K_set if y[0, k, t].X > 0.5]
      if not active_vehicles:
        print("  Aucune tournée effectuée.")
      for k in active_vehicles:
        # Reconstruction de la tournée dans l'ordre des arcs suivis
        route = [0]
        curr = 0
        while True:
          next_nodes = [
              j for j in V if j != curr and x[curr, j, k, t].X > 0.5
          ]
          if not next_nodes:
            break
          nxt = next_nodes[0]
          route.append(nxt)
          curr = nxt
          if curr == 0:
            break
        route_str = " -> ".join(map(str, route))

        # Détail des compartiments livrés
        deliveries = []
        for l in L:
          for i in V_prime:
            for prod in M:
              if z[i, prod, l, k, t].X > 0.5:
                qty = q[i, prod, l, k, t].X
                deliveries.append(f"Comp {l}: Client {i} (Prod {prod}, {qty:.0f}L)")
        print(f"  Véhicule {k:2d} | Route : {route_str} | " + ", ".join(deliveries))

  return model


if __name__ == "__main__":
  # Exemple de lancement sur l'une de vos instances
  instance_file = "/home/maximeh/Documents/Université/Master/Semestre 1/Opti/Projet/MCDs/mcd-50-3-5-30-5-5.dat"
  data = load_mcdp_instance(instance_file)
  solve_single_route_mcdp(data, time_limit=300)