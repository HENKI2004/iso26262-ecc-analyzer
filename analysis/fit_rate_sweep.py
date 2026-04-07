import matplotlib.pyplot as plt
import numpy as np

from ecc_analyzer.models.lpddr5.lpddr5_system import Lpddr5System

# --- Konfiguration ---
# Logarithmische Skala von 0.1 bis 10.000 FIT
dram_rates = np.logspace(-1, 4, 100)
other_fit_fixed = 1900.0
residual_rf = []
latent_fault = []

print("Starte Sensitivitätsanalyse für DRAM FIT...")

for r in dram_rates:
    # Initialisierung des Systems mit variabler DRAM-Rate
    system = Lpddr5System("LPDDR5_Stress", r, other_fit_fixed)

    # Analyse ausführen
    metrics = system.run_analysis()

    # Metriken für den Plot sammeln
    residual_rf.append(metrics["Lambda_RF_Sum"])
    latent_fault.append(metrics["Lambda_Latent"])

# In Numpy-Arrays umwandeln für Berechnungen
residual_rf = np.array(residual_rf)
latent_fault = np.array(latent_fault)

# --- Erstellung des Diagramms ---
plt.figure(figsize=(12, 8))

# 1. Hauptkurven plotten
plt.plot(dram_rates, residual_rf, label="Residual (RF)", color="red", linewidth=3, zorder=5)
plt.plot(dram_rates, latent_fault, label="Latent Fault (MPF,L)", color="blue", linewidth=3, zorder=5)

# 2. ASIL Grenzwerte für Residual Faults (RF)
targets = [(10, "darkred", "ASIL D (RF <= 10 FIT)"), (100, "orange", "ASIL B/C (RF <= FIT)")]

for level, color, label in targets:
    # Zeichne horizontale Linie
    plt.axhline(y=level, color=color, linestyle=":", alpha=0.8, label=label)

    # Berechne Schnittpunkt (FIT-Wert bei dem RF = level)
    # Da residual_rf mit dram_rates steigt, können wir direkt interpolieren
    if residual_rf[0] < level < residual_rf[-1]:
        isect_fit = np.interp(level, residual_rf, dram_rates)

        # Zeichne vertikale Linie nach unten
        plt.vlines(x=isect_fit, ymin=0, ymax=level, color=color, linestyle="--", alpha=0.7)

        # Beschriftung des FIT-Wertes an der X-Achse
        # plt.text(isect_fit, 0.2, f" {isect_fit:.1f} FIT", color=color, rotation=90, verticalalignment="bottom", fontweight="bold", fontsize=9)

# --- Formatierung ---
plt.xscale("log")
plt.yscale("log")

# Grenzen der Achsen festlegen (Start bei 0.1 FIT)
plt.xlim(dram_rates[0], dram_rates[-1])
plt.ylim(0.1, max(latent_fault) * 1.5)

plt.xlabel(r"$\lambda_{DRAM}$ (FIT)", fontsize=12)
plt.ylabel(r"$\lambda_{out}$ (FIT)", fontsize=12)
# plt.title("LPDDR5 Logarithmic Sensitivity Analysis: DRAM FIT vs. System Metrics", fontsize=14, fontweight="bold")

# Legende
plt.legend(loc="upper left", fontsize=10, frameon=True)

# Dezentes Gitter (nur Hauptlinien)
plt.grid(True, which="major", linestyle="-", color="gray", alpha=0.1)

plt.tight_layout()

# Speichern für die Thesis
plt.savefig("dram_fit_sensitivity_plot_log_with_violation.png", dpi=300)
print(f"Analyse abgeschlossen. Max Residual RF: {residual_rf[-1]:.2f} FIT")
plt.show()
