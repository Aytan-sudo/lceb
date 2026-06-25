NB = [1, 3, 8, 75, 50, 4]
CIBLE = 990


def trouver_toutes_les_solutions(nombres, cible):
    elements = [(n, str(n)) for n in nombres]
    toutes_les_solutions = set()

    def chercher(etat_actuel):
        # Ne compter que les solutions utilisant toutes les plaques
        if len(etat_actuel) == 1:
            val, expr = etat_actuel[0]
            if val == cible:
                toutes_les_solutions.add(expr)
            return

        for i in range(len(etat_actuel)):
            for j in range(i + 1, len(etat_actuel)):
                val1, expr1 = etat_actuel[i]
                val2, expr2 = etat_actuel[j]

                reste = [etat_actuel[k] for k in range(len(etat_actuel)) if k != i and k != j]

                if val1 >= val2:
                    a, expr_a = val1, expr1
                    b, expr_b = val2, expr2
                else:
                    a, expr_a = val2, expr2
                    b, expr_b = val1, expr1

                operations = []
                operations.append((a + b, f"({expr_a} + {expr_b})"))

                if a > b:
                    operations.append((a - b, f"({expr_a} - {expr_b})"))

                operations.append((a * b, f"({expr_a} * {expr_b})"))

                if b != 0 and a % b == 0:
                    operations.append((a // b, f"({expr_a} / {expr_b})"))

                for nouv_val, nouv_expr in operations:
                    if nouv_val > 0:
                        chercher(reste + [(nouv_val, nouv_expr)])

    chercher(elements)
    return toutes_les_solutions

# --- Zone de test ---
if __name__ == "__main__":
    nombres_depart = NB
    cible_visee = CIBLE
    
    print(f"Recherche de toutes les solutions pour {cible_visee} avec {nombres_depart}...\n")
    
    solutions = trouver_toutes_les_solutions(nombres_depart, cible_visee)
    
    if solutions:
        print(f"{len(solutions)} solution(s) trouvée(s) :")
        for i, sol in enumerate(solutions, 1):
            print(f"Solution {i} : {sol} = {cible_visee}")
    else:
        print("Aucune solution trouvée.")