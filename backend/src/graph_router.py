import json
from pathlib import Path
import networkx as nx
import joblib
import pandas as pd

# ruta del archivo json con el mapa de la ciudad
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
GRAPH_PATH = DATA_DIR / "city_graph.json"
MODEL_PATH = DATA_DIR / "modelo_tiempo_viaje.joblib"

class CityGraphRouter:
    def __init__(self):
        # hacemos que el grafo sea dirigido por como funcionan las calles
        self.graph = nx.DiGraph()
        self.nodes_info = {}
        self.edges_info = {}
        self.cargar_grafo()
        self.modelo = None
        self.cargar_modelo()

    def cargar_modelo(self):
        if MODEL_PATH.exists():
            self.modelo = joblib.load(MODEL_PATH)
            print("modelo de ML encontrado")
        else:
            print("modelo no encontrado, se usara simulador matematico")

    def cargar_grafo(self):
        with open(GRAPH_PATH, "r", encoding= "utf-8") as f:
            data = json.load(f)

        # agregamos los nodos al grafo
        for nodo in data["nodos"]:
            self.nodes_info[nodo["id"]] = nodo
            self.graph.add_node(
                nodo["id"],
                lat=nodo["lat"],
                lon=nodo["lon"],
                label=nodo["label"]
            )

        # agregamos las aristas al grafo
        for arista in data["aristas"]:
            self.edges_info[arista["tramo_id"]] = arista

            velocidad=arista["velocidad_base_kmh"] /3.6
            tiempo_base=arista["distancia_metros"] / velocidad

            self.graph.add_edge(                
                arista["origen"],
                arista["destino"],
                tramo_id=arista["tramo_id"],
                distancia_metros=arista["distancia_metros"],
                velocidad_base_kmh=arista["velocidad_base_kmh"],
                tipo=arista["tipo"],
                tiempo_segundos = tiempo_base # "costo" sin trafico
            )
        print(f"[OK] Grafo cargado: {self.graph.number_of_nodes()} esquinas y {self.graph.number_of_edges()} tramos de calle.")


    def calcular_ruta_dijkstra(self, origen: str, destino: str, criterio_peso: str = "distancia_metros"):
        try: 
            camino_nodos= nx.dijkstra_path(self.graph, origen, destino, weight = criterio_peso) 
        except nx.NetworkXNoPath :
            print (f"[AVISO] no existe camino entre {origen} y {destino}")
            return None
        tramos_recorridos = []
        distancia_total = 0.0
        tiempo_total = 0.0

        for i in range(len(camino_nodos) - 1):
            nodo_actual = camino_nodos[i]
            nodo_siguiente = camino_nodos[i + 1]
            datos_arista = self.graph[nodo_actual][nodo_siguiente]
            distancia_total += datos_arista["distancia_metros"]
            tiempo_total += datos_arista["tiempo_segundos"]
            tramos_recorridos.append({
                "tramo_id": datos_arista["tramo_id"],
                "desde": nodo_actual,
                "hasta": nodo_siguiente,
                "tipo": datos_arista["tipo"],
                "distancia": datos_arista["distancia_metros"],
                "tiempo": round(datos_arista["tiempo_segundos"], 1)
            })

        return {
            "criterio": criterio_peso,
            "camino_nodos": camino_nodos,
            "total_metros": round(distancia_total, 1),
            "total_segundos": round(tiempo_total, 1),
            "total_minutos": round(tiempo_total / 60, 2),
            "detalle_tramos": tramos_recorridos
        }
    def actualizar_pesos(self, hora_dia = int, dia_semana = str, clima = str, es_feriado: bool = False):
        dia_semana = dia_semana.lower()
        clima = clima.lower()

        if self.modelo is not None:
            filas_consultas = []
            aristas_lista = []

            for u, v, datos in self.graph.edges(data=True):
                filas_consultas.append({
                    "tramo_id": datos["tramo_id"],
                    "hora_dia": hora_dia,
                    "dia_semana": dia_semana,
                    "clima": clima,
                    "es_feriado": es_feriado,
                    "velocidad_promedio_historica": datos["velocidad_base_kmh"] * 0.9
                })
                aristas_lista.append((u, v))

            df_query = pd.DataFrame(filas_consultas)
            tiempos_predichos= self.modelo.predict(df_query)

            for (u,v), t_estimado in zip(aristas_lista, tiempos_predichos):
                self.graph[u][v]["tiempos_segundos"] = max(5.0, float(t_estimado))

        else:
            es_fin_de_semana = dia_semana in ["sabado", "domingo"]
            es_hora_pico = (7 <= hora_dia <= 9) or (17 <= hora_dia <= 20)

            for u, v, datos in self.graph.edges(data=True):
                distancia = datos["distancia_metros"]
                v_base = datos["velocidad_base_kmh"]
                tipo = datos["tipo"]

                factor = 1.0
                if not es_fin_de_semana and not es_feriado:
                    if es_hora_pico:
                        factor *= 1.8 if tipo == "avenida" else 1.3
                    elif 0 <= hora_dia <= 5:
                        factor *= 0.85

                if clima == "lluvia":
                    factor *= 1.25
                elif clima == "tormenta":
                    factor *= 1.60

                v_efectiva = max(5.0, v_base / factor)
                tiempo_estimado = distancia / (v_efectiva / 3.6)
                self.graph[u][v]["tiempo_segundos"] = round(tiempo_estimado, 1)




if __name__ == "__main__":
    router = CityGraphRouter()

    resultado = router.calcular_ruta_dijkstra("N_0_0", "N_3_3", criterio_peso="distancia_metros")
    print("\n--- PRUEBA DIJKSTRA (POR DISTANCIA) ---")
    print("Camino:", " -> ".join(resultado["camino_nodos"]))
    print(f"Distancia total: {resultado['total_metros']} metros")
    print(f"Tiempo base: {resultado['total_minutos']} minutos")

    router.actualizar_pesos(hora_dia=18, dia_semana="lunes", clima="tormenta", es_feriado=False)
    # 3. Ruta Dinámica (Dijkstra buscando menor tiempo con tráfico)

    ruta_dinamica = router.calcular_ruta_dijkstra("N_0_0", "N_3_3", criterio_peso="tiempo_segundos")
    print("\n--- 2. RUTA DINÁMICA (CON TORMENTA Y HORA PICO) ---")
    print("Camino:", " -> ".join(ruta_dinamica["camino_nodos"]))
    print(f"Distancia: {ruta_dinamica['total_metros']} m | Tiempo con tráfico: {ruta_dinamica['total_minutos']} min")

    if resultado["camino_nodos"] != ruta_dinamica["camino_nodos"]:
        print("\n¡ÉXITO TOTAL! Dijkstra cambió de ruta para esquivar la congestión.")
    else:
        print("\nEligió el mismo camino.")