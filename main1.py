NB = [5, 75, 2, 50, 100, 10]
CIBLE = 868



def trouver_toutes_les_solutions(nombres, cible):
    elements = [(n, str(n)) for n in nombres]
    toutes_les_solutions = set() # Utilisation d'un set pour éviter les doublons stricts
    
    def chercher(etat_actuel):
        # 1. On vérifie si on a atteint la cible
        for val, expr in etat_actuel:
            if val == cible:
                toutes_les_solutions.add(expr)
                # L'algo cherche plusieurs chemins dans l'arbre
                
        # 2. Condition d'arrêt
        if len(etat_actuel) <= 1:
            return
            
        # 3. Explorer toutes les combinaisons
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
                    
                if b > 1:
                    operations.append((a * b, f"({expr_a} * {expr_b})"))
                    
                if b > 1 and a % b == 0:
                    operations.append((a // b, f"({expr_a} / {expr_b})"))
                    
                # 4. Appel récursif sans bloquer le retour
                for nouv_val, nouv_expr in operations:
                    chercher(reste + [(nouv_val, nouv_expr)])

    # Lancement de la recherche
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