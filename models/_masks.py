"""Pré-calcul des partitions disjointes par masque, partagé par les modèles
deux-phases (6, 7, 8, 9).

Pour un masque donné, on génère les couples (A, B) tels que :
  - A | B == mask, A & B == 0, A et B non vides ;
  - A contient toujours le bit de poids faible (low-bit) du masque,
    ce qui évite de traiter symétriquement (A, B) puis (B, A).
"""


def partitions_by_mask(n: int) -> list[list[tuple[int, int]]]:
    max_mask = 1 << n
    parts_all: list[list[tuple[int, int]]] = [[] for _ in range(max_mask)]

    for mask in range(1, max_mask):
        if not (mask & (mask - 1)):
            continue  # singleton : aucune partition

        lowbit = mask & -mask
        rest = mask ^ lowbit
        parts = []
        sub = rest
        while True:
            A = sub | lowbit
            B = mask ^ A
            if B:
                parts.append((A, B))
            if sub == 0:
                break
            sub = (sub - 1) & rest
        parts_all[mask] = parts

    return parts_all
