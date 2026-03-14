def run_pipeline():

    # Chequeo preflight: detectar archivos Python vacíos antes de importar módulos
    try:
        from src.scripts.preflight import check_empty_python_files
        empties = check_empty_python_files(root="src")
        if empties:
            print("\nERROR: Se detectaron archivos Python vacíos o que sólo contienen espacios en blanco:")
            for p in empties:
                print("  -", p)
            print("\nCorrige esos archivos antes de ejecutar el pipeline.")
            return
    except Exception as e:
        print("Advertencia: no se pudo ejecutar el chequeo preflight:", e)

    # Importar módulos del pipeline después del chequeo (evita ImportError por archivos vacíos)
    from src.ingesta.loader import DataLoader
    from src.preprocessing.feature_engineering import generate_features
    from src.analysis.risk_prediction import RiskPredictor
    from src.dashboard.app import ModelOutputSaver

    print("\n===================================")
    print("INICIANDO PIPELINE DE MONITOREO")
    print("===================================\n")

    # ---------------------------------
    # 1. INGESTA
    # ---------------------------------

    print("1. Ejecutando ingesta...")

    loader = DataLoader()
    loader.load_and_validate()

    print("Ingesta completada\n")

    # ---------------------------------
    # 2. FEATURE ENGINEERING
    # ---------------------------------

    print("2. Generando features...")

    generate_features()

    print("Features generadas\n")

    # ---------------------------------
    # 3. MODELO DE RIESGO
    # ---------------------------------

    print("3. Ejecutando modelo baseline...")

    predictor = RiskPredictor()
    predictor.run()

    print("Predicción completada\n")

    # ---------------------------------
    # 4. GUARDAR RESULTADOS
    # ---------------------------------

    print("4. Guardando resultados finales...")

    saver = ModelOutputSaver()
    saver.run()

    print("\n===================================")
    print("PIPELINE EJECUTADO CORRECTAMENTE")
    print("===================================\n")


if __name__ == "__main__":
    run_pipeline()