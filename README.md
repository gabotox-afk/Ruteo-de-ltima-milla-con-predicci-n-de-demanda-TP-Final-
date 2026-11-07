# Ruteo de Última Milla con Predicción de Demanda

**Trabajo Práctico Final — Lógica y Teoría de Grafos**

Sistema que combina un modelo de regresión para predecir tiempos de viaje con el algoritmo de Dijkstra para calcular rutas de entrega óptimas sobre un grafo de calles urbanas.

---

## Descripción

Una empresa de logística quiere optimizar sus entregas diarias. Las rutas convencionales usan distancias fijas, pero el tiempo de viaje real varía según la hora, el día, el clima y otros factores. Este sistema:

1. **Predice** el tiempo de viaje en cada tramo de la ciudad usando un modelo de Machine Learning entrenado sobre datos históricos de tráfico.
2. **Actualiza dinámicamente** los pesos del grafo de calles usando esas predicciones.
3. **Calcula rutas óptimas** con el algoritmo de Dijkstra sobre los tiempos estimados.
4. **Visualiza** ambas rutas (estática por distancia vs. dinámica por tráfico predicho) en un mapa interactivo para mostrar el valor agregado del modelo.

---

## Instalación

```bash
git clone https://github.com/gabotox-afk/Ruteo-de-ltima-milla-con-predicci-n-de-demanda-TP-Final-.git
cd Ruteo-de-ltima-milla-con-predicci-n-de-demanda-TP-Final-

python -m venv venv
source venv/bin/activate
pip install scikit-learn pandas numpy networkx joblib

cd frontend
npm install
cd ..
```

> En Windows reemplazá `source venv/bin/activate` por `venv\Scripts\activate`.

---

## Ejecución

### Terminal 1 — Backend

```bash
source venv/bin/activate
python backend/src/generate_city_and_data.py
python backend/src/train_model.py
python backend/src/api.py
```

### Terminal 2 — Frontend

```bash
cd frontend
npm run dev
```

La aplicación queda disponible en **`http://localhost:5173`**.

> El frontend redirige automáticamente las llamadas a `/api/*` al backend en el puerto 8000.

---

## Endpoints de la API

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/health` | Estado del servidor y del modelo cargado |
| `GET` | `/api/grafo` | Nodos y aristas del grafo de la ciudad |
| `GET` | `/api/metricas` | Métricas MAE/RMSE/R² de todos los modelos |
| `POST` | `/api/calcular-ruta` | Dijkstra: compara ruta estática vs. dinámica |
| `POST` | `/api/ronda-entregas` | Nearest Neighbor: secuencia óptima de entregas |

---

## Modelo de Machine Learning

Se entrenaron 4 modelos de regresión usando un `Pipeline` de scikit-learn (preprocesador + regresor). Las variables predictoras son `tramo_id`, `hora_dia`, `dia_semana`, `clima`, `es_feriado` y `velocidad_promedio_historica`. La variable objetivo es `tiempo_real_viaje` (segundos).

**Resultados sobre el conjunto de test (30% del dataset — 3.465 muestras):**

| Modelo | MAE (s) | RMSE (s) | R² |
|---|---|---|---|
| LinearRegression | 7.73 | 9.86 | 0.630 |
| KNeighborsRegressor | 6.42 | 9.04 | 0.689 |
| DecisionTreeRegressor | 4.00 | 5.55 | 0.883 |
| **RandomForestRegressor** ✅ | **3.06** | **4.24** | **0.932** |

El **RandomForestRegressor** (100 árboles) obtuvo el mejor R² y se selecciona automáticamente como modelo de producción.

---

## Funcionalidades del frontend

- Mapa interactivo del grafo con zoom, desplazamiento y selección de nodos con clic.
- Cálculo de ruta punto a punto con comparación visual entre la ruta estática (distancia) y la dinámica (predicción IA), mostrando el ahorro de tiempo.
- Planificación de ronda de entregas con múltiples paradas usando Nearest Neighbor.
- Selector de hora, día de la semana y clima para ajustar las condiciones del tráfico.
- Panel de métricas con la tabla comparativa de los 4 modelos evaluados.

---

## Estructura del proyecto

```
.
├── backend/
│   ├── data/
│   │   ├── city_graph.json            # Grafo de la ciudad (nodos y aristas)
│   │   ├── viajes_historicos.csv      # Dataset histórico de viajes
│   │   ├── modelo_tiempo_viaje.joblib # Mejor modelo entrenado (RandomForest)
│   │   └── metricas_modelos.json      # MAE, RMSE, R² de cada modelo evaluado
│   └── src/
│       ├── generate_city_and_data.py  # Genera el grafo y el dataset sintético
│       ├── train_model.py             # Entrena y evalúa los 4 modelos
│       ├── graph_router.py            # Lógica de grafos: Dijkstra + ronda de entregas
│       └── api.py                     # Servidor HTTP con endpoints REST
└── frontend/
    └── src/
        ├── App.tsx                    # Componente raíz y estado global
        ├── types.ts                   # Tipos TypeScript de la API
        ├── services/api.ts            # Funciones fetch al backend
        └── components/
            ├── CityMap.tsx            # Mapa SVG interactivo (zoom, pan, clic)
            ├── RouteControls.tsx      # Selector de origen, destino, hora, clima
            ├── RouteComparison.tsx    # Comparación ruta estática vs. dinámica
            ├── DeliveryRoundPanel.tsx # Panel de ronda de entregas
            └── MetricsPanel.tsx      # Tabla de métricas de los modelos ML
```
