import json
from pathlib import Path
import networkx as nx

# ruta del archivo json con el mapa de la ciudad
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
GRAPH_PATH = DATA_DIR / "city_graph.json"

class CityGraphRouter:
    def __init__(self):
        # hacemos que el grafo sea dirigido por como funcional las calles
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

if __name__ == "__main__":
    router = CityGraphRouter()