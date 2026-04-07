import matplotlib.pyplot as plt
import sympy

from ecc_analyzer.models.lpddr5 import Lpddr5System


def plot_vulnerability(vulnerabilities):
    # Namen für die Thesis säubern
    mapping = {"lambda_Events_WD": "Wrong Data ", "lambda_Events_MBE": "Multi-Bit Errors", "lambda_Events_DBE": "Double-Bit Errors", "lambda_Events_SBE": "Single-Bit Errors"}

    # Sortieren (höchster Wert oben)
    sorted_v = dict(sorted(vulnerabilities.items(), key=lambda item: item[1], reverse=True))
    labels = [mapping.get(k, k) for k in sorted_v.keys()]
    values = list(sorted_v.values())

    plt.figure(figsize=(10, 5))
    # Farbe: Ein warnendes Rot/Orange, da dies die Schwachstellen (Vulnerabilities) sind
    colors = ["#c0392b" if v > 0.4 else "#e67e22" if v > 0.0 else "#27ae60" for v in values]

    bars = plt.barh(labels, values, color=colors, edgecolor="black", alpha=0.8)
    plt.gca().invert_yaxis()

    plt.xlabel(r"Vulnerability Factor ($\frac{\partial \lambda_{RF}}{\partial \lambda_{i}}$)", fontsize=12, fontweight="bold")
    # plt.title("Hardware Vulnerability: Proportion of Faults becoming Residual", fontsize=14, pad=20)
    plt.grid(axis="x", linestyle="--", alpha=0.6)
    plt.xlim(0, 1.1)  # Da es Anteile sind (0 bis 1)

    # Werte beschriften
    for bar in bars:
        width = bar.get_width()
        plt.text(width + 0.02, bar.get_y() + bar.get_height() / 2, f"{width * 100:.1f}%", va="center", fontweight="bold")

    plt.tight_layout()
    plt.savefig("hardware_vulnerability.png", dpi=300)
    plt.show()


# In deiner main() aufrufen:


def main():
    # 1. System initialisieren
    # Wir nutzen mode="all_vars", damit Lambdas UND Coverages Symbole bleiben
    system = Lpddr5System("LPDDR5_Vulnerability_Analysis", total_fit=2300.0, other_fit=1900.0)

    # 2. Alle Metriken als rein symbolische Ausdrücke extrahieren
    metrics = system.get_symbolic_metrics(mode="be_vars")

    lambda_rf_expr = metrics["Lambda_RF"]
    print(lambda_rf_expr)

    print("\n--- Analyse der Hardware-Vulnerabilität (Ableitung nach FIT) ---")

    # 3. Definition der Lambdas der Basic Events (DRAM Sources)
    # Die Namen müssen exakt so lauten, wie sie im Framework generiert werden
    l_sbe = sympy.Symbol("lambda_Events_SBE")
    l_dbe = sympy.Symbol("lambda_Events_DBE")
    l_mbe = sympy.Symbol("lambda_Events_MBE")
    l_tbe = sympy.Symbol("lambda_Events_WD")

    target_lambdas = [l_sbe, l_dbe, l_mbe, l_tbe]

    # 4. Baseline-Werte für die Coverages (für die numerische Auswertung)
    # Hier setzen wir die DCs ein, um zu sehen, wie viel "durchlässt"
    manual_values = {
        sympy.Symbol("c_R_Inline_ECC_MBE_MBE"): 0.5,
        sympy.Symbol("c_R_Inline_ECC_DBE_DBE"): 1.0,
        sympy.Symbol("c_R_Inline_ECC_SBE_SBE"): 1.0,
        sympy.Symbol("c_R_Inline_ECC_TBE_TBE"): 1.0,
        sympy.Symbol("c_R_Link_SBE"): 1.0,
        sympy.Symbol("c_R_Sec_SBE"): 1.0,
        # Weitere Symbole falls vorhanden...
    }

    vulnerabilities = {}

    for l_sym in target_lambdas:
        # Bilde partielle Ableitung: d(Lambda_RF) / d(Lambda_i)
        derivative = sympy.diff(lambda_rf_expr, l_sym)

        # Numerischen Wert berechnen (Gibt den "Durchlassfaktor" an)
        val = derivative.subs(manual_values).evalf()
        vulnerabilities[l_sym.name] = float(val)

        print(f"\nAbleitung nach {l_sym.name}:")
        print(f"LaTeX: \\frac{{\\partial \\lambda_{{RF}}}}{{\\partial \\lambda_{{{l_sym.name.split('_')[-1]}}}}} = {sympy.latex(derivative)}")
        print(f"Wert (Durchlassfaktor): {val:.6f}")

    # 5. Ranking der kritischsten Hardware-Fehlerquellen
    print("\n--- Hardware Vulnerability Ranking ---")
    sorted_vulnerability = dict(sorted(vulnerabilities.items(), key=lambda item: item[1], reverse=True))

    for name, factor in sorted_vulnerability.items():
        print(f"{name:30}: {factor:.4f} (Anteil des Fehlers, der im System verbleibt)")

    plot_vulnerability(vulnerabilities)


if __name__ == "__main__":
    main()
