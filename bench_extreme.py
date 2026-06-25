import subprocess
import time
import statistics
import sys
import os

# On ne garde que l'élite pour ce test
FICHIERS_A_TESTER = ["main6.py", "main7.py", "main8.py"]
ITERATIONS = 3 

def executer_benchmark_extreme():
    print(f"Démarrage du BENCHMARK EXTRÊME ({ITERATIONS} itérations par script)...\n")
    print("Attention, avec N=7 ou N=8, l'exécution peut prendre quelques secondes par itération.\n")
    
    print(f"{'Script':<15} | {'Temps Moyen':<15} | {'Min':<12} | {'Max':<12}")
    print("-" * 60)

    for fichier in FICHIERS_A_TESTER:
        if not os.path.exists(fichier):
            print(f"{fichier:<15} | --- FICHIER INTROUVABLE ---")
            continue

        temps_execution = []
        erreur = False

        for _ in range(ITERATIONS):
            debut = time.perf_counter()
            
            resultat = subprocess.run(
                [sys.executable, fichier], 
                capture_output=True, 
                text=True
            )
            
            fin = time.perf_counter()

            if resultat.returncode != 0:
                print(f"{fichier:<15} | ERREUR LORS DE L'EXÉCUTION")
                print(f"Détail :\n{resultat.stderr}")
                erreur = True
                break
                
            temps_execution.append(fin - debut)

        if not erreur and temps_execution:
            t_moyen = statistics.mean(temps_execution)
            t_min = min(temps_execution)
            t_max = max(temps_execution)
            
            print(f"{fichier:<15} | {t_moyen:.5f} s     | {t_min:.5f} s | {t_max:.5f} s")

if __name__ == "__main__":
    executer_benchmark_extreme()