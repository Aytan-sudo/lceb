import subprocess
import time
import statistics
import sys
import os

# --- Configuration ---
# Liste exacte de tes fichiers à tester
FICHIERS_A_TESTER = ["main1.py", "main2.py", "main3.py", "main4.py", "main5.py", "main6.py", "main7.py", "main8.py"]
# Nombre de fois que chaque script sera exécuté pour calculer la moyenne
ITERATIONS = 5 

def executer_benchmark():
    print(f"Démarrage du benchmark ({ITERATIONS} itérations par script)...\n")
    
    # En-tête du tableau
    print(f"{'Script':<15} | {'Temps Moyen':<15} | {'Min':<12} | {'Max':<12}")
    print("-" * 60)

    for fichier in FICHIERS_A_TESTER:
        if not os.path.exists(fichier):
            print(f"{fichier:<15} | --- FICHIER INTROUVABLE ---")
            continue

        temps_execution = []
        erreur_rencontree = False

        for _ in range(ITERATIONS):
            debut = time.perf_counter()
            
            # On lance le script de manière isolée avec le même interpréteur Python
            resultat = subprocess.run(
                [sys.executable, fichier], 
                capture_output=True, 
                text=True
            )
            
            fin = time.perf_counter()

            # Vérification que le script n'a pas planté
            if resultat.returncode != 0:
                print(f"{fichier:<15} | ERREUR LORS DE L'EXÉCUTION")
                print(f"Détail de l'erreur :\n{resultat.stderr}")
                erreur_rencontree = True
                break
                
            temps_execution.append(fin - debut)

        # Affichage des statistiques si aucune erreur
        if not erreur_rencontree and temps_execution:
            t_moyen = statistics.mean(temps_execution)
            t_min = min(temps_execution)
            t_max = max(temps_execution)
            
            print(f"{fichier:<15} | {t_moyen:.5f} s     | {t_min:.5f} s | {t_max:.5f} s")

if __name__ == "__main__":
    executer_benchmark()