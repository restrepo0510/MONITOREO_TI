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
    from src.dashboard.utils.sensor_thresholds import calibrate_sensor_thresholds, save_sensor_thresholds
    from src.config import SENSOR_THRESHOLDS_PATH
    from src.dashboard.model_output_saver import ModelOutputSaver

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
    risk_df = predictor.run()

    print("Predicción completada\n")

    # ---------------------------------
    # 3.5 UMBRALES FIJOS POR SENSOR
    # ---------------------------------
    # Se calibran con histórico sano (risk_level == BAJO) para alertamiento formal.
    # Este artefacto es consumido por el front para mostrar referencias estables.
    print("3.5 Calibrando umbrales fijos por sensor...")
    if risk_df is not None:
        thresholds = calibrate_sensor_thresholds(risk_df)
        save_sensor_thresholds(thresholds, SENSOR_THRESHOLDS_PATH)
        print(f"Umbrales guardados en: {SENSOR_THRESHOLDS_PATH}\n")
    else:
        print("No se pudo calibrar umbrales porque la predicción falló.\n")

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
