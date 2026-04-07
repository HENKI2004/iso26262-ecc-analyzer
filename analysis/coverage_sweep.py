import matplotlib.pyplot as plt
import numpy as np

from ecc_analyzer.models.lpddr5 import Lpddr5System


def get_crossing_point(x, y, threshold):
    """Findet den X-Wert (Coverage), an dem y den Schwellenwert überschreitet."""
    if y[-1] < threshold:
        return None  # Erreicht den Schwellenwert nie
    return np.interp(threshold, y, x)


def plot_enhanced_sweep(cov, results, title, label, color, baseline_x=None):
    plt.figure(figsize=(10, 6))
    cov_pct = cov * 100
    plt.plot(cov_pct, results, color=color, linewidth=2.5, label=label)

    # ASIL Linien
    targets = [(90, "orange", "ASIL C"), (99, "red", "ASIL D")]
    for val, col, lab in targets:
        plt.axhline(y=val, color=col, linestyle="--", alpha=0.4)
        plt.text(99, val - 0.3, f" {lab}", color=col, va="top", ha="right", fontweight="bold", fontsize=9)
        # Schnittpunkt berechnen
        cross = get_crossing_point(cov_pct, results, val)
        if cross:
            plt.vlines(x=cross, ymin=0, ymax=val, color=col, linestyle=":", alpha=0.6)
            plt.text(cross, 50, f" {cross:.1f}% DC", color=col, rotation=90, va="bottom", fontweight="bold")

    # Baseline Punkt (optional)
    if baseline_x is not None:
        # Finde y-Wert an der Baseline
        baseline_y = np.interp(baseline_x, cov_pct, results)
        plt.scatter([baseline_x], [baseline_y], color="black", s=100, zorder=10, label=f"Current Design ({baseline_x}%)")

    # plt.title(title, fontsize=13, fontweight="bold")
    plt.xlabel(r"Diagnostic Coverage $c_R$ [%]", fontsize=12)
    plt.ylabel(r"System $SPFM$ [%]", fontsize=12)
    plt.ylim(min(results) - 5, 101)
    plt.xlim(0, 100)
    plt.legend(loc="lower right")
    plt.grid(True, alpha=0.15)
    plt.tight_layout()
    plt.savefig("sec_ded_sensitivity_plot_mbe.png", dpi=300)


def find_block_by_name(root, name):
    """Sucht rekursiv nach einem Block in der gesamten System-Hierarchie."""
    if root is None:
        return None
    if hasattr(root, "name") and root.name == name:
        return root
    if hasattr(root, "system_layout") and root.system_layout:
        found = find_block_by_name(root.system_layout, name)
        if found:
            return found
    if hasattr(root, "root_block") and root.root_block:
        found = find_block_by_name(root.root_block, name)
        if found:
            return found
    if hasattr(root, "sub_blocks") and root.sub_blocks:
        for sub in root.sub_blocks:
            found = find_block_by_name(sub, name)
            if found:
                return found
    return None


def run_sweep(system, block_names, steps=50):
    """Hilfsfunktion: Führt einen Sweep für eine Liste von Blöcken aus."""
    coverages = np.linspace(0.0, 1.0, steps)
    results = []

    # Initialisiere Struktur
    system.run_analysis()

    # Suche die Ziel-Objekte
    targets = [find_block_by_name(system, name) for name in block_names]
    targets = [t for t in targets if t is not None]

    if not targets:
        print(f"Warnung: Keine Blöcke für {block_names} gefunden.")
        return coverages, [0] * steps

    for c in coverages:
        for block in targets:
            block.c_R = c
        metrics = system.run_analysis()
        results.append(metrics["SPFM"] * 100)

    return coverages, results


def plot_asil_lines():
    """Zeichnet die ISO 26262 Schwellenwerte ein."""
    plt.axhline(y=60, color="orange", linestyle="--", alpha=0.5, label="ASIL B (60%)")
    plt.axhline(y=90, color="red", linestyle="--", alpha=0.5, label="ASIL C (90%)")
    plt.axhline(y=99, color="darkred", linestyle="--", alpha=0.5, label="ASIL D (99%)")


def main():
    steps = 100  # Höhere Auflösung für glattere Linien

    # Simulationen ausführen
    sys1 = Lpddr5System("LPDDR5_Single", total_fit=2300.0, other_fit=1900.0)
    cov, res_single = run_sweep(sys1, ["Inline_ECC_MBE"], steps)

    sys2 = Lpddr5System("LPDDR5_Group", total_fit=2300.0, other_fit=1900.0)
    _, res_group = run_sweep(sys2, ["Inline_ECC_SBE", "Inline_ECC_DBE", "Inline_ECC_MBE", "Inline_ECC_TBE"], steps)

    # Plots generieren
    plot_enhanced_sweep(cov, res_single, "Sensitivity Analysis: Inline ECC MBE Coverage", "Sensitivity MBE Coverage", "red", baseline_x=50)

    # Vergleichsplot separat
    plt.figure(figsize=(10, 6))
    plt.plot(cov * 100, res_single, "b-", linewidth=2, color="lightcoral", label=r"Sensitivity MBE Coverage")
    plt.plot(cov * 100, res_group, "b-", linewidth=2, color="red", label=r"Sensitivity SEC-DED Coverage")
    plt.axhline(y=90, color="orange", linestyle="--", alpha=0.5)
    plt.text(98, 90 - 0.3, "ASIL C", color="orange", va="top", ha="right", fontweight="bold", fontsize=9)
    plt.xlabel(r"Diagnostic Coverage $c_R$ [%]")
    plt.ylabel(r"System $SPFM$ [%]")
    plt.xlim(0, 100)
    # plt.title("Comparison: Local vs. Global Coverage Impact")
    plt.legend()
    plt.grid(True, alpha=0.2)
    plt.savefig("sec_ded_sensitivity_plot_global.png", dpi=300)
    plt.show()


if __name__ == "__main__":
    main()
