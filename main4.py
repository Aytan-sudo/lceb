from itertools import combinations

NB = [1, 3, 8, 75, 50, 4]
CIBLE = 990

def trouver_toutes_solutions_opti(nombres, cible):
    # Le cache : associe un groupe d'index à un dictionnaire {valeur_atteinte: set(expressions)}
    memo = {}

    def resoudre_sous_ensemble(indices):
        # On utilise un frozenset d'index pour représenter notre sous-ensemble (qui sert de clé de cache)
        # On utilise les index et non les valeurs pour gérer les nombres en double (ex: deux fois le chiffre 4)
        if indices in memo:
            return memo[indices]

        resultats = {}

        # Cas de base : s'il n'y a qu'un seul nombre
        if len(indices) == 1:
            idx = next(iter(indices))
            val = nombres[idx]
            resultats[val] = {str(val)}
            memo[indices] = resultats
            return resultats

        # Pour séparer en deux parties sans calculer de doublons symétriques (A|B et B|A),
        # on force le premier élément de la liste à toujours rester dans la partie de gauche.
        liste_idx = list(indices)
        pivot = liste_idx[0]
        autres = liste_idx[1:]

        # On génère toutes les combinaisons possibles avec le reste des éléments
        for r in range(len(autres) + 1):
            for comb in combinations(autres, r):
                partie_gauche = frozenset([pivot] + list(comb))
                partie_droite = indices - partie_gauche

                if not partie_droite:
                    continue

                # Calculs récursifs des deux moitiés (bénéficiant du cache)
                res_gauche = resoudre_sous_ensemble(partie_gauche)
                res_droite = resoudre_sous_ensemble(partie_droite)

                # Croisement mathématique des résultats des deux parties
                for val_g, exprs_g in res_gauche.items():
                    for val_d, exprs_d in res_droite.items():
                        
                        # On ordonne a et b pour simplifier les calculs
                        if val_g >= val_d:
                            a, expr_a = val_g, exprs_g
                            b, expr_b = val_d, exprs_d
                        else:
                            a, expr_a = val_d, exprs_d
                            b, expr_b = val_g, exprs_g

                        operations = [
                            (a + b, '+'),
                            (a * b, '*')
                        ]
                        if a > b:
                            operations.append((a - b, '-'))
                        if b != 0 and a % b == 0:
                            operations.append((a // b, '/'))

                        # Création des nouvelles expressions pour le dictionnaire
                        for nouv_val, operateur in operations:
                            if nouv_val > 0:
                                if nouv_val not in resultats:
                                    resultats[nouv_val] = set()
                                # Produit cartésien des chaînes de caractères
                                for ea in expr_a:
                                    for eb in expr_b:
                                        resultats[nouv_val].add(f"({ea} {operateur} {eb})")

        # On sauvegarde dans le cache avant de retourner
        memo[indices] = resultats
        return resultats

    # Lancement de l'algorithme sur l'ensemble complet des index
    index_complets = frozenset(range(len(nombres)))
    toutes_les_combinaisons = resoudre_sous_ensemble(index_complets)

    # On extrait uniquement les expressions correspondant à notre cible
    return toutes_les_combinaisons.get(cible, set())

# --- Zone de test ---
if __name__ == "__main__":
    import time
    
    print(f"Recherche de toutes les solutions (version optimisée) pour {CIBLE} avec {NB}...\n")
    
    debut = time.time()
    solutions = trouver_toutes_solutions_opti(NB, CIBLE)
    fin = time.time()
    
    if solutions:
        print(f"{len(solutions)} solution(s) trouvée(s) en {fin - debut:.4f} secondes :")
        for i, sol in enumerate(list(solutions)[:10], 1): # Affiche les 10 premières pour éviter d'inonder la console
            print(f"Solution {i} : {sol} = {CIBLE}")
        if len(solutions) > 10:
            print(f"... et {len(solutions) - 10} autres.")
    else:
        print("Aucune solution trouvée.")