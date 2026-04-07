import sympy

from ecc_analyzer.models.lpddr4 import Lpddr4System
from ecc_analyzer.models.lpddr5 import Lpddr5System


def perform_symbolic_deep_dive(system_class, name):
    print(f"\n{'=' * 60}")
    print(f" ANALYSE: {name}")
    print(f"{'=' * 60}")

    # 1. System-Instanz erstellen (Unterscheidung LPDDR4 / LPDDR5)
    if issubclass(system_class, Lpddr4System):
        # LPDDR4 nutzt meistens nur ein Feld für total_fit
        system = system_class(name, total_fit=2300.0, other_fit=1920.0)
    elif issubclass(system_class, Lpddr5System):
        # LPDDR5 nutzt die Aufteilung in DRAM (total_fit) und Peripherie (other_fit)
        system = system_class(name, total_fit=2300.0, other_fit=1900.0)
    else:
        system = system_class(name, total_fit=2300.0)

    # 2. Symbolische Formel extrahieren
    # 'all_vars' sorgt dafür, dass Lambdas und Coverage-Werte als Symbole erhalten bleiben
    sym_metrics = system.get_symbolic_metrics(mode="numeric")

    # print(sym_metrics)

    spfm_expr = sym_metrics["SPFM"]
    lfm_expr = sym_metrics["LFM"]
    rf_expr = sym_metrics["Lambda_RF"]

    print("\n[1] LaTeX-Formel für den SPFM:")
    print("-" * 30)
    print(sympy.latex(spfm_expr))
    print(sympy.latex(lfm_expr))
    print(sympy.latex(rf_expr))
    print("-" * 30)

    # 3. Numerische Analyse ausführen (Der Standard-Durchlauf)
    num_results = system.run_analysis()

    print("\n[2] Numerische Ergebnisse (Framework):")
    print(f" SPFM:     {num_results['SPFM'] * 100.0:.4f} %")
    print(f" RF FIT:   {num_results['Lambda_RF_Sum']:.4f} FIT")
    print(f" LFM:      {num_results['LFM'] * 100.0:.4f} %")

    # 4. Symbolischer Check (Substitution)
    # Wir nehmen die Formel und setzen die echten Werte ein, um zu sehen,
    # ob das gleiche Ergebnis wie bei der numerischen Analyse rauskommt.
    # try:
    #     sub_dict = system.get_substitution_dict()
    #     symbolic_numeric_value = spfm_expr.subs(sub_dict).evalf()

    #     print("\n[3] Konsistenz-Check:")
    #     print(f" Wert aus Formel:    {symbolic_numeric_value * 100.0:.4f} %")
    #     print(f" Wert aus Framework: {num_results['SPFM'] * 100.0:.4f} %")

    #     diff = abs(symbolic_numeric_value - num_results["SPFM"])
    #     print(f" Differenz:          {diff:.2e} (Sollte nahe 0 sein)")

    # except AttributeError:
    #     print("\n[3] Konsistenz-Check: get_substitution_dict() nicht gefunden. Manuelle Prüfung nötig.")

    # sym_metrics = system.get_symbolic_metrics(mode="coverage_vars")
    # print(sym_metrics["SPFM"])


def main():
    # Führe die Analyse für beide Systeme aus
    perform_symbolic_deep_dive(Lpddr4System, "LPDDR4_System")
    perform_symbolic_deep_dive(Lpddr5System, "LPDDR5_System")


if __name__ == "__main__":
    main()
