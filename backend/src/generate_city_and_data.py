import json
from pathlib import Path
import numpy as np
import pandas as pd

# Fijar semilla para reproducibilidad (requisito para el informe)
np.random.seed(42)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def build_city_graph(num_filas=5, num_columnas=5, paso_avenida=3):
    """
    Crea un grafo urbano realista y escalable tipo cuadrícula (num_filas x num_columnas)
    con coordenadas geográficas centradas en Buenos Aires.
    
    Reglas de diseño urbanístico:
    1. Las avenidas son siempre de doble mano (<-> y ^v).
    2. Dos calles de un sentido consecutivas nunca tienen la misma dirección.
    3. Las dos calles a los lados de una avenida tampoco tienen la misma dirección
       (se usa un contador exclusivo de calles de mano única que no avanza en las avenidas).
    """
    # Coordenadas base (Palermo / Colegiales, CABA)
    base_lat = -34.5850
    base_lon = -58.4350
    lat_step = 0.0030  # aprox 330 metros entre esquinas norte-sur
    lon_step = 0.0035  # aprox 320 metros entre esquinas este-oeste

    nodes = []
    node_coords = {}

    for row in range(num_filas):
        for col in range(num_columnas):
            node_id = f"N_{row}_{col}"
            lat = base_lat - (row * lat_step)
            lon = base_lon + (col * lon_step)
            node_coords[node_id] = (lat, lon)
            nodes.append({
                "id": node_id,
                "lat": round(lat, 6),
                "lon": round(lon, 6),
                "label": f"Esquina ({row},{col})"
            })

    # Precalcular el tipo/sentido de cada fila y columna con un contador exclusivo de calles
    dirs_h = []
    contador_calle_h = 0
    for r in range(num_filas):
        if r % paso_avenida == 2:
            dirs_h.append("AV")
        else:
            dirs_h.append("E" if contador_calle_h % 2 == 0 else "O")
            contador_calle_h += 1

    dirs_v = []
    contador_calle_v = 0
    for c in range(num_columnas):
        if c % paso_avenida == 2:
            dirs_v.append("AV")
        else:
            dirs_v.append("N" if contador_calle_v % 2 == 0 else "S")
            contador_calle_v += 1

    edges = []
    edge_counter = 1

    for r in range(num_filas):
        for c in range(num_columnas):
            curr_id = f"N_{r}_{c}"

            # 1. Conexiones Horizontales (Este - Oeste)
            if c < num_columnas - 1:
                next_id = f"N_{r}_{c+1}"
                tipo_h = dirs_h[r]

                if tipo_h == "AV":
                    # Avenida doble mano (<->)
                    edges.append({
                        "tramo_id": f"T_{edge_counter:03d}",
                        "origen": curr_id,
                        "destino": next_id,
                        "distancia_metros": 340,
                        "tipo": "avenida",
                        "velocidad_base_kmh": 50
                    })
                    edge_counter += 1
                    edges.append({
                        "tramo_id": f"T_{edge_counter:03d}",
                        "origen": next_id,
                        "destino": curr_id,
                        "distancia_metros": 340,
                        "tipo": "avenida",
                        "velocidad_base_kmh": 50
                    })
                    edge_counter += 1
                elif tipo_h == "E":
                    # Calle mano única hacia el Este (->)
                    edges.append({
                        "tramo_id": f"T_{edge_counter:03d}",
                        "origen": curr_id,
                        "destino": next_id,
                        "distancia_metros": 350,
                        "tipo": "calle",
                        "velocidad_base_kmh": 35
                    })
                    edge_counter += 1
                else:
                    # Calle mano única hacia el Oeste (<-)
                    edges.append({
                        "tramo_id": f"T_{edge_counter:03d}",
                        "origen": next_id,
                        "destino": curr_id,
                        "distancia_metros": 350,
                        "tipo": "calle",
                        "velocidad_base_kmh": 35
                    })
                    edge_counter += 1

            # 2. Conexiones Verticales (Norte - Sur)
            if r < num_filas - 1:
                next_id = f"N_{r+1}_{c}"
                tipo_v = dirs_v[c]

                if tipo_v == "AV":
                    # Avenida doble mano (^v)
                    edges.append({
                        "tramo_id": f"T_{edge_counter:03d}",
                        "origen": curr_id,
                        "destino": next_id,
                        "distancia_metros": 320,
                        "tipo": "avenida",
                        "velocidad_base_kmh": 45
                    })
                    edge_counter += 1
                    edges.append({
                        "tramo_id": f"T_{edge_counter:03d}",
                        "origen": next_id,
                        "destino": curr_id,
                        "distancia_metros": 320,
                        "tipo": "avenida",
                        "velocidad_base_kmh": 45
                    })
                    edge_counter += 1
                elif tipo_v == "N":
                    # Calle mano única hacia el Norte (|^)
                    edges.append({
                        "tramo_id": f"T_{edge_counter:03d}",
                        "origen": next_id,
                        "destino": curr_id,
                        "distancia_metros": 330,
                        "tipo": "calle",
                        "velocidad_base_kmh": 35
                    })
                    edge_counter += 1
                else:
                    # Calle mano única hacia el Sur (|v)
                    edges.append({
                        "tramo_id": f"T_{edge_counter:03d}",
                        "origen": curr_id,
                        "destino": next_id,
                        "distancia_metros": 330,
                        "tipo": "calle",
                        "velocidad_base_kmh": 35
                    })
                    edge_counter += 1

    city_data = {
        "metadata": {
            "descripcion": "Red vial sintética para ruteo de última milla",
            "total_nodos": len(nodes),
            "total_tramos": len(edges)
        },
        "nodos": nodes,
        "aristas": edges
    }

    graph_file = DATA_DIR / "city_graph.json"
    with open(graph_file, "w", encoding="utf-8") as f:
        json.dump(city_data, f, indent=2, ensure_ascii=False)

    print(f"[OK] Grafo guardado en {graph_file} ({len(nodes)} nodos, {len(edges)} tramos).")
    return edges


def generate_synthetic_travel_dataset(edges, num_samples_per_edge=400):
    """
    Genera observaciones históricas de viajes para cada tramo del grafo.
    Aplica las reglas declaradas de tránsito y clima con variabilidad estocástica.
    """
    dias_semana = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
    climas = ["soleado", "lluvia", "tormenta"]
    clima_probs = [0.70, 0.22, 0.08]

    records = []

    for edge in edges:
        tramo_id = edge["tramo_id"]
        distancia = edge["distancia_metros"]
        tipo = edge["tipo"]
        v_base = edge["velocidad_base_kmh"]

        for _ in range(num_samples_per_edge):
            hora = int(np.random.randint(0, 24))
            dia = np.random.choice(dias_semana)
            clima = np.random.choice(climas, p=clima_probs)
            es_fin_de_semana = dia in ["sabado", "domingo"]
            es_feriado = bool(np.random.rand() < 0.04) if not es_fin_de_semana else False

            # --- MODELADO DE CONGESTIÓN ---
            # 1. Factor horario
            es_hora_pico_manana = (7 <= hora <= 9)
            es_hora_pico_tarde = (17 <= hora <= 20)
            es_hora_valle_noche = (0 <= hora <= 5)

            factor_congestion = 1.0

            if not es_fin_de_semana and not es_feriado:
                if es_hora_pico_manana:
                    # Las avenidas se congestionan mucho más que las calles internas
                    factor_congestion *= 2.5 if tipo == "avenida" else 1.15
                elif es_hora_pico_tarde:
                    factor_congestion *= 2.8 if tipo == "avenida" else 1.20
                elif es_hora_valle_noche:
                    factor_congestion *= 0.85

            # 2. Factor clima (afecta más a las arterias principales)
            if clima == "lluvia":
                factor_congestion *= 1.35 if tipo == "avenida" else 1.15
            elif clima == "tormenta":
                factor_congestion *= 1.80 if tipo == "avenida" else 1.30

            # 3. Factor feriado / fin de semana
            if es_feriado or es_fin_de_semana:
                if 12 <= hora <= 18:
                    factor_congestion *= 1.15
                else:
                    factor_congestion *= 0.90

            # Ruido aleatorio realista (semáforos, peatones, etc.)
            ruido = np.random.normal(loc=1.0, scale=0.08)
            factor_final = max(0.6, factor_congestion * ruido)

            # Velocidad efectiva en el viaje (km/h)
            v_real = max(5.0, v_base / factor_final)

            # Velocidad promedio histórica estimada para ese tramo (con algo de ruido histórico)
            v_historica = round(float(np.random.normal(v_base * 0.9, 2.0)), 1)

            # Tiempo real de viaje en segundos: t = d / v
            # d en metros, v en m/s => v(km/h) / 3.6
            v_ms = v_real / 3.6
            tiempo_real_segundos = distancia / v_ms

            # Variable a predecir: tiempo en segundos (redondeado a 1 decimal)
            tiempo_real_viaje = round(float(tiempo_real_segundos), 1)

            records.append({
                "tramo_id": tramo_id,
                "hora_dia": hora,
                "dia_semana": dia,
                "clima": clima,
                "es_feriado": es_feriado,
                "velocidad_promedio_historica": v_historica,
                "tiempo_real_viaje": tiempo_real_viaje
            })

    df = pd.DataFrame(records)

    csv_file = DATA_DIR / "viajes_historicos.csv"
    df.to_csv(csv_file, index=False)

    print(f"[OK] Dataset generado exitosamente en {csv_file}")
    print(f"     Total de filas: {len(df)}")
    print(f"     Columnas: {list(df.columns)}")
    print("\nPrimeras 5 filas:")
    print(df.head())


if __name__ == "__main__":
    tramos = build_city_graph()
    generate_synthetic_travel_dataset(tramos, num_samples_per_edge=120)
