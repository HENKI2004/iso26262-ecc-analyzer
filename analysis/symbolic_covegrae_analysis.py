import matplotlib.pyplot as plt
import sympy

from ecc_analyzer.models.lpddr5 import Lpddr5System


def main():
    # 1. System initialisieren
    system = Lpddr5System("LPDDR5_Analysis", total_fit=2300.0, other_fit=1900.0)

    # 2. Formel extrahieren
    metrics = system.get_symbolic_metrics(mode="coverage_vars")
    spfm_expr = metrics["SPFM"]

    # Definition der Symbole und Werte (wie in deinem Code)
    manual_values = {
        sympy.Symbol("c_R_Inline_ECC_MBE_MBE"): 0.5,
        sympy.Symbol("c_R_Inline_ECC_DBE_DBE"): 1.0,
        sympy.Symbol("c_R_Inline_ECC_SBE_SBE"): 1.0,
        sympy.Symbol("c_R_Inline_ECC_TBE_TBE"): 1.0,
        sympy.Symbol("c_R_OTHER_COV_OTH"): 0.99,
        sympy.Symbol("c_R_Link_SBE"): 1.0,
        sympy.Symbol("c_R_Sec_SBE"): 1.0,
    }

    # 3. Gradienten berechnen
    target_coverages = [sympy.Symbol("c_R_Inline_ECC_MBE_MBE"), sympy.Symbol("c_R_Inline_ECC_DBE_DBE"), sympy.Symbol("c_R_Link_SBE"), sympy.Symbol("c_R_Inline_ECC_TBE_TBE")]

    gradients = {}
    for sym in target_coverages:
        derivative = sympy.diff(spfm_expr, sym)
        latex_formula = sympy.latex(derivative)
        print(f"% Ableitung nach {sym.name}")
        print("\\begin{equation}")
        print(f"  \\frac{{\\partial SPFM}}{{\\partial {sympy.latex(sym)}}} = {latex_formula}")
        print("\\end{equation}")
        value = derivative.subs(manual_values).evalf()
        gradients[sym.name] = float(value)

    # 4. Sortieren für das Diagramm (Wichtigster Hebel oben)
    sorted_gradients = dict(sorted(gradients.items(), key=lambda item: item[1], reverse=True))

    # --- DIAGRAMM ERSTELLEN ---
    plt.figure(figsize=(10, 6))

    # Manuelles Mapping für professionelle Labels in der Thesis
    name_mapping = {
        "c_R_Inline_ECC_MBE_MBE": "SEC DED MBE",
        "c_R_Inline_ECC_DBE_DBE": "SEC DED DBE",
        "c_R_Inline_ECC_TBE_TBE": "SEC DED TBE",
        "c_R_Link_SBE": "Link SBE",
        "c_R_OTHER_COV_OTH": "Other HW DC",
    }

    # Namen übersetzen (falls ein Name nicht im Mapping ist, nimm den Originalnamen)
    clean_names = [name_mapping.get(n, n) for n in sorted_gradients.keys()]
    values = list(sorted_gradients.values())

    # Horizontale Balken zeichnen
    # Farbe: Ein kräftiges Blau/Grau wirkt in wissenschaftlichen Arbeiten oft seriöser
    colors = ["#2c3e50" if v > 0.01 else "#7f8c8d" for v in values]
    bars = plt.barh(clean_names, values, color=colors, edgecolor="black", alpha=0.8)

    plt.gca().invert_yaxis()  # Höchster Impact nach oben

    # Beschriftung der Achsen
    plt.xlabel(r"$\frac{\partial SPFM}{\partial c_R}$", fontsize=12, fontweight="bold")
    plt.grid(axis="x", linestyle="--", alpha=0.6)

    # Werte direkt an die Balken schreiben
    for bar in bars:
        width = bar.get_width()
        plt.text(width + 0.0005, bar.get_y() + bar.get_height() / 2, f"{width:.6f}", va="center", fontsize=10, fontweight="bold")

    plt.tight_layout()
    plt.savefig("safety_gradients_lpddr5.png", dpi=300)
    plt.show()


if __name__ == "__main__":
    main()
