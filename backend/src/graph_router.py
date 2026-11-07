import json
from pathlib import Path
import networkx as nx

# ruta del archivo json con el mapa de la ciudad
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
GRAPH_PATH = DATA_DIR / "city_graph.json"

class CityGraphRouter:
    def __init__(self):
        # hacemos que el grafo sea dirigido por como funcionan las calles
        self.graph = nx.DiGraph()
        self.nodes_info = {}
        self.edges_info = {}
        self.cargar_grafo()

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




if __name__ == "__main__":
    router = CityGraphRouter()

    resultado = router.calcular_ruta_dijkstra("N_0_0", "N_3_3", criterio_peso="distancia_metros")
    print("\n--- PRUEBA DIJKSTRA (POR DISTANCIA) ---")
    print("Camino:", " -> ".join(resultado["camino_nodos"]))
    print(f"Distancia total: {resultado['total_metros']} metros")
    print(f"Tiempo base: {resultado['total_minutos']} minutos")