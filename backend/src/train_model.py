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


# 1. Cargar el dataset y separar X e y
df, X, y = cargar_datos(CSV_PATH)

# 2. Partición en 70% entrenamiento y 30% test (test_size=0.30, random_state=42)
X_train_raw, X_test_raw, y_train, y_test = train_test_split(
    X, y, test_size=0.30, random_state=42
)

# 3. Crear ColumnTransformer
preprocessor = crear_preprocesador()

# 4. Ajustar preprocesador con train y transformar train y test
X_train = preprocessor.fit_transform(X_train_raw)
X_test = preprocessor.transform(X_test_raw)


if __name__ == "__main__":
    print("=" * 60)
    print("Preprocesamiento de datos finalizado exitosamente")
    print("=" * 60)
    print(f"Dataset cargado desde: {CSV_PATH}")
    print(f"Total de registros:    {len(df)}")
    print(f"Variables categóricas: {CATEGORICAL_FEATURES}")
    print(f"Variables numéricas:   {NUMERIC_FEATURES}")
    print(f"Variable objetivo:     {TARGET_FEATURE}")
    print("-" * 60)
    print(f"X_train (preprocesado): {X_train.shape}")
    print(f"X_test  (preprocesado): {X_test.shape}")
    print(f"y_train:                {y_train.shape}")
    print(f"y_test:                 {y_test.shape}")
    print("=" * 60)
