"""Zentraler Einstiegspunkt zur Ausführung der Sicherheitsanalysen (LPDDR4 & LPDDR5)."""

# import sympy

# from matplotlib import pyplot as plt

# from ecc_analyzer.models.lpddr4 import Lpddr4System
# from ecc_analyzer.models.lpddr5 import Lpddr5System
from ecc_analyzer.models.miniSys.mini_sys import MinimalSystem


def run_analysis_for_system(system, pipeline_name_for_detail="DRAM_Path"):
    """Hilfsfunktion, um doppelten Code für Analyse und Ausgabe zu vermeiden."""

    print(f"\n{'=' * 60}")
    print(f" ANALYSE GESTARTET: {system.name}")
    print(f"{'=' * 60}")

    metrics = system.run_analysis()

    print(f"\nERGEBNIS FÜR {system.name}:")
    print(f" SPFM:             {metrics['SPFM'] * 100.0:.2f}%")
    print(f" LFM:              {metrics['LFM'] * 100.0:.2f}%")
    print(f" Residual (RF):    {metrics['Lambda_RF_Sum']:.2f} FIT")
    print(f" Latent Fault:      {metrics['Lambda_Latent']:.2f} FIT")
    print(f" total_fit          {metrics['total_fit']:.2f} FIT")
    print(f" ASIL:             {metrics['ASIL_Achieved']}")
    print("=" * 60)

    pdf_name = f"{system.name}_Report"
    print(f"Generiere PDF: {pdf_name}.pdf ...")
    system.generate_pdf(pdf_name)
    print("Fertig.\n")


import numpy as np


def run_dram_sensitivity_analysis(system_class, start_fit=0.01, end_fit=2500, steps=100):
    dram_rates = np.linspace(start_fit, end_fit, steps)
    spfm_results = []
    lfm_results = []
    residual_results = []

    for rate in dram_rates:
        # 1. System mit der aktuellen Rate initialisieren
        # Annahme: Dein System nimmt die total_fit im Konstruktor oder
        # du passt die Events intern an.
        system = system_class("LPDDR5_Sweep", total_fit=rate, other_fit=1900.0)

        # Falls du nur die DRAM-Events ändern willst:
        # Manuelle Suche nach dem DRAM-Event Block im Layout:
        # system.system_layout.find_block("DRAM_Sources").lambda_BE = rate

        # 2. Analyse ausführen
        results = system.run_analysis()

        # 3. Metriken extrahieren
        spfm_results.append(results["SPFM"] * 100)
        lfm_results.append(results["LFM"] * 100)
        residual_results.append(results["Lambda_RF_Sum"])

    return dram_rates, spfm_results, lfm_results, residual_results


def main():
    test = MinimalSystem("MinimalSystem", 45, other_fit=5)
    run_analysis_for_system(test)
    test.save_to_json("minimal_system_config.json")
    metrics = test.get_symbolic_metrics(mode="all_vars")
    print(metrics)

    # lpddr4 = Lpddr4System("LPDDR4_System", total_fit=4220.0)
    # # run_analysis_for_system(lpddr4)

    # lpddr5 = Lpddr5System("LPDDR5_System", total_fit=2300.0, other_fit=1900.0)
    # run_analysis_for_system(lpddr5)

    # metrics = lpddr5.get_symbolic_metrics(mode="numeric")
    # print(metrics)
    # spfm_expr = metrics["SPFM"]

    # dram_fit = 2300.0

    # substitutions = {
    #     sympy.Symbol("lambda_Bus_AZ"): 172.0,
    #     sympy.Symbol("lambda_Events_DBE"): 0.0748 * dram_fit,
    #     sympy.Symbol("lambda_Events_MBE"): 0.0748 * dram_fit,
    #     sympy.Symbol("lambda_Events_WD"): 0.0748 * dram_fit,
    #     sympy.Symbol("lambda_OTH_OTH"): 9.5,
    # }

    # ergebnis = spfm_expr.subs(substitutions).evalf()
    # print(f"Berechneter SPFM: {ergebnis}%")

    # metrics = lpddr5.get_symbolic_metrics(mode="all_vars")
    # spfm_expr = metrics["SPFM"]

    # target_var = sympy.Symbol("c_R_SEC")

    # spfm_derivative = sympy.diff(spfm_expr, target_var)

    # print(f"Ableitung nach {target_var}:")
    # print(sympy.simplify(spfm_derivative))

    # rates, spfm, lfm, residual = run_dram_sensitivity_analysis(Lpddr5System)

    # plt.figure(figsize=(10, 6))

    # # Plot SPFM und LFM
    # plt.plot(rates, spfm, label="SPFM (%)", color="red")
    # plt.plot(rates, lfm, label="LFM (%)", color="blue")

    # # ASIL D Schwellenwert (99% für SPFM)
    # plt.axhline(y=99, color="gray", linestyle="--", label="ASIL D SPFM Target (99%)")

    # plt.xscale("log")  # Oft sinnvoll bei FIT-Sweeps
    # plt.xlabel("DRAM Fault Rate (FIT)")
    # plt.ylabel("Metric Score (%)")
    # plt.title("Sensitivity Analysis: Relative Metrics")
    # plt.legend()
    # plt.grid(True)
    # plt.show()


if __name__ == "__main__":
    main()
