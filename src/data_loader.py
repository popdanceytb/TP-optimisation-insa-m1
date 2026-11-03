import math

def load_coelho_instance(filepath):
    with open(filepath, 'r') as f:
        tokens = f.read().split()

    if not tokens:
        raise ValueError("Le fichier d'instance est vide.")

    idx = 0
    n = int(tokens[idx])
    m = int(tokens[idx + 1])
    comps = int(tokens[idx + 2])
    K = int(tokens[idx + 3])
    H = int(tokens[idx + 4])
    idx += 5

    depot_x = float(tokens[idx])
    depot_y = float(tokens[idx + 1])
    idx += 2
    coor = [(depot_x, depot_y)]

    comp = {}
    for k in range(1, K + 1):
        comp[k] = {}
        for c in range(1, comps + 1):
            comp[k][c] = float(tokens[idx])
            idx += 1

    I0, r, U, h = {}, {}, {}, {}

    for i in range(1, n + 1):
        x = float(tokens[idx])
        y = float(tokens[idx + 1])
        coor.append((x, y))
        idx += 2

        I0[i] = {}
        for l in range(1, m + 1):
            I0[i][l] = float(tokens[idx])
            idx += 1

        r[i] = {}
        for l in range(1, m + 1):
            r[i][l] = {}
        for t in range(1, H + 1):
            r[i][l][t] = float(tokens[idx])
            idx += 1

        U[i], h[i] = {}, {}
        for l in range(1, m + 1):
            U[i][l] = float(tokens[idx])
            h[i][l] = float(tokens[idx + 1])
            idx += 2

    dist = {}
    for i in range(n + 1):
        dist[i] = {}
        for j in range(n + 1):
            dx = coor[i][0] - coor[j][0]
            dy = coor[i][1] - coor[j][1]
            dist[i][j] = int(math.floor(math.sqrt(dx * dx + dy * dy) + 0.5))

    return {
        'n': n,
        'm': m,
        'comps': comps,
        'K': K,
        'H': H,
        'comp': comp,
        'I0': I0,
        'r': r,
        'U': U,
        'h': h,
        'dist': dist,
    }