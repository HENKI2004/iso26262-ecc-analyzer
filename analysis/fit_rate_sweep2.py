import matplotlib.pyplot as plt
import numpy as np

from ecc_analyzer.models.lpddr5.lpddr5_system import Lpddr5System

# --- Konfiguration ---
dram_rates = np.logspace(-1, 4, 100)
other_fit_fixed = 1900.0

spfm_results = []
lfm_results = []


def get_intersection_fit(fit_array, metric_array, target_value):
    return np.interp(target_value, metric_array[::-1], fit_array[::-1])


print("Starte Metrik-Analyse...")

for r in dram_rates:
    system = Lpddr5System("LPDDR5_Metric_Sweep", r, other_fit_fixed)
    metrics = system.run_analysis()
    spfm_results.append(metrics["SPFM"] * 100)
    lfm_results.append(metrics["LFM"] * 100)

spfm_results = np.array(spfm_results)
lfm_results = np.array(lfm_results)

# --- Plotting ---
plt.figure(figsize=(14, 8))

# 1. Metriken plotten
plt.plot(dram_rates, spfm_results, label="System SPFM", color="red", linewidth=3, zorder=5)
plt.plot(dram_rates, lfm_results, label="System LFM", color="blue", linewidth=3, zorder=5)

# 2. ISO Targets definieren (Alle wieder drin)
spfm_targets = [(99, "#c0392b", "ASIL D"), (97, "#d35400", "ASIL C"), (90, "#f1c40f", "ASIL B")]
lfm_targets = [(90, "blue", "ASIL D"), (80, "blue", "ASIL C"), (60, "blue", "ASIL B")]

# SPFM Schnittpunkte zeichnen
for level, color, label in spfm_targets:
    plt.axhline(y=level, color=color, linestyle=":", alpha=0.6)

    # LOGIK FÜR ASIL D TEXT-POSITION
    if "ASIL C" in label:
        # Text UNTER der Linie (va='top', Versatz negativ)
        y_pos = level - 0.8
        v_align = "top"
    else:
        # Text ÜBER der Linie (va='bottom', Versatz positiv)
        y_pos = level + 0.6
        v_align = "bottom"

    plt.text(dram_rates[-1], y_pos, f"{label} Target (SPFM) ", color=color, va=v_align, ha="right", fontsize=9, fontweight="bold")

    isect_fit = get_intersection_fit(dram_rates, spfm_results, level)
    if dram_rates[0] < isect_fit < dram_rates[-1]:
        plt.vlines(x=isect_fit, ymin=0, ymax=level, color=color, linestyle="--", alpha=0.7)
        plt.text(isect_fit, 1.5, f"{isect_fit:.1f} FIT ", color=color, rotation=90, va="bottom", ha="right", fontsize=8, fontweight="bold")

# LFM Schnittpunkte zeichnen (Beschriftungen links)
for level, color, label in lfm_targets:
    plt.axhline(y=level, color=color, linestyle="--", alpha=0.3)

    # Auch hier für ASIL D nach unten schieben, falls gewünscht
    if "ASIL D" in label:
        y_pos = level - 0.8
        v_align = "top"
    else:
        y_pos = level + 0.6
        v_align = "bottom"

    plt.text(dram_rates[0], y_pos, f" {label} Target (LFM)", color=color, va=v_align, ha="left", fontsize=9)

    isect_fit = get_intersection_fit(dram_rates, lfm_results, level)
    if dram_rates[0] < isect_fit < dram_rates[-1]:
        plt.vlines(x=isect_fit, ymin=0, ymax=level, color=color, linestyle="--", alpha=0.4)

# Achsen-Setup
plt.xscale("log")
plt.ylim(0, 105)
plt.xlim(dram_rates[0], dram_rates[-1])

plt.xlabel(r"$\lambda_{DRAM}$ (FIT)", fontsize=12)
plt.ylabel("SPFM and LFM (%)", fontsize=12)

plt.grid(True, which="major", linestyle="-", color="gray", alpha=0.1)
plt.legend(loc="lower left", fontsize=10, frameon=True, ncol=2)

plt.tight_layout()
plt.savefig("dram_fit_sensitivity_plot_spfm_lfm.png", dpi=300)
plt.show()
