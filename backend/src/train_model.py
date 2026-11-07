import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
from sklearn.tree import DecisionTreeRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor

# Rutas del proyecto
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CSV_PATH = DATA_DIR / "viajes_historicos.csv"
METRICS_PATH = DATA_DIR / "metricas_modelos.json"
MODEL_PATH = DATA_DIR / "modelo_tiempo_viaje.joblib"

# Definición de variables
CATEGORICAL_FEATURES = ["tramo_id", "dia_semana", "clima", "es_feriado"]
NUMERIC_FEATURES = ["hora_dia", "velocidad_promedio_historica"]
TARGET_FEATURE = "tiempo_real_viaje"
FEATURE_COLS = CATEGORICAL_FEATURES + NUMERIC_FEATURES


def cargar_datos(csv_path: Path = CSV_PATH):
    """
    Carga el dataset de viajes históricos con pandas y separa las variables
    predictoras (X) y la variable objetivo (y).
    """
    df = pd.read_csv(csv_path)
    X = df[FEATURE_COLS]
    y = df[TARGET_FEATURE]
    return df, X, y


def crear_preprocesador() -> ColumnTransformer:
    """
    Crea un ColumnTransformer que aplica OneHotEncoder a las variables categóricas
    y StandardScaler a las variables numéricas.
    """
    return ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
            ("num", StandardScaler(), NUMERIC_FEATURES),
        ]
    )


def definir_modelos():
    """
    Define el diccionario de modelos a evaluar:
    - LinearRegression (modelo base / benchmark)
    - DecisionTreeRegressor
    - KNeighborsRegressor
    - RandomForestRegressor
    """
    return {
        "LinearRegression": LinearRegression(),
        "DecisionTreeRegressor": DecisionTreeRegressor(random_state=42),
        "KNeighborsRegressor": KNeighborsRegressor(),
        "RandomForestRegressor": RandomForestRegressor(n_estimators=100, random_state=42),
    }


def entrenar_y_evaluar_modelos(modelos, X_train, y_train, X_test, y_test, preprocesador_fn=crear_preprocesador):
    """
    Entrena cada modelo dentro de un Pipeline (preprocesador + regresor)
    y evalúa las métricas MAE, RMSE y R^2 sobre el conjunto de test.
    """
    metricas = {}
    pipelines_entrenados = {}

    for nombre, regressor in modelos.items():
        pipeline = Pipeline(
            steps=[
                ("preprocessor", preprocesador_fn()),
                ("regressor", regressor),
            ]
        )

        # Entrenamiento del Pipeline
        pipeline.fit(X_train, y_train)

        # Predicción sobre el conjunto de test
        y_pred = pipeline.predict(X_test)

        # Cálculo de métricas pedidas
        mae = float(mean_absolute_error(y_test, y_pred))
        rmse = float(root_mean_squared_error(y_test, y_pred))
        r2 = float(r2_score(y_test, y_pred))

        metricas[nombre] = {
            "MAE": round(mae, 4),
            "RMSE": round(rmse, 4),
            "R2": round(r2, 4),
        }
        pipelines_entrenados[nombre] = pipeline

    return metricas, pipelines_entrenados


def imprimir_tabla_comparativa(metricas: dict):
    """Imprime una tabla comparativa formateada por consola con los resultados."""
    print("=" * 66)
    print("                 TABLA COMPARATIVA DE MODELOS                     ")
    print("=" * 66)
    print(f"{'Modelo':<25} | {'MAE (seg)':<10} | {'RMSE (seg)':<10} | {'R²':<10}")
    print("-" * 66)
    for nombre, valores in metricas.items():
        print(
            f"{nombre:<25} | {valores['MAE']:<10.4f} | {valores['RMSE']:<10.4f} | {valores['R2']:<10.4f}"
        )
    print("=" * 66)


def exportar_metricas(metricas: dict, output_path: Path = METRICS_PATH):
    """Exporta el diccionario de métricas en formato JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metricas, f, indent=2, ensure_ascii=False)
    print(f"[OK] Métricas exportadas exitosamente en: {output_path}")


def seleccionar_mejor_modelo(metricas: dict, pipelines: dict):
    """
    Identifica en el código cuál fue el modelo con mejor puntaje R^2.
    Retorna el nombre del modelo, su pipeline completo y su puntaje R^2.
    """
    mejor_nombre = max(metricas, key=lambda m: metricas[m]["R2"])
    mejor_pipeline = pipelines[mejor_nombre]
    mejor_r2 = metricas[mejor_nombre]["R2"]
    return mejor_nombre, mejor_pipeline, mejor_r2


def guardar_modelo(pipeline, output_path: Path = MODEL_PATH):
    """
    Guarda el pipeline completo (preprocesador + modelo) usando joblib.dump.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, output_path)
    print(f"[OK] Mejor pipeline guardado exitosamente en: {output_path}")


# 1. Cargar el dataset y separar X e y
df, X, y = cargar_datos(CSV_PATH)

# 2. Partición en 70% entrenamiento y 30% test
X_train_raw, X_test_raw, y_train, y_test = train_test_split(
    X, y, test_size=0.30, random_state=42
)

# 3. Crear ColumnTransformer y obtener conjuntos preprocesados
preprocessor = crear_preprocesador()
X_train = preprocessor.fit_transform(X_train_raw)
X_test = preprocessor.transform(X_test_raw)

# 4. Definición de modelos a comparar
modelos = definir_modelos()


if __name__ == "__main__":
    print(f"Dataset cargado: {len(df)} registros.")
    print(f"Conjunto de entrenamiento: {len(X_train_raw)} muestras (70%).")
    print(f"Conjunto de prueba:        {len(X_test_raw)} muestras (30%).\n")
    print("Entrenando y evaluando modelos dentro de sus respectivos Pipelines...")

    metricas, pipelines = entrenar_y_evaluar_modelos(
        modelos=modelos,
        X_train=X_train_raw,
        y_train=y_train,
        X_test=X_test_raw,
        y_test=y_test,
    )

    print()
    imprimir_tabla_comparativa(metricas)
    print()
    exportar_metricas(metricas, METRICS_PATH)

    # Identificar y guardar el mejor modelo según R^2
    mejor_nombre, mejor_pipeline, mejor_r2 = seleccionar_mejor_modelo(metricas, pipelines)
    print()
    print(f"Mejor modelo identificado según R²: {mejor_nombre} (R² = {mejor_r2:.4f})")
    guardar_modelo(mejor_pipeline, MODEL_PATH)
