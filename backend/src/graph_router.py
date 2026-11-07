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

    @staticmethod
    def formatear_tiempo(segundos_totales : float) -> str:
        minutos, segundos = divmod(int(round(segundos_totales)), 60)
        return f"{minutos:02d}:{segundos:02d}"
    
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
            "tiempo_formateado": self.formatear_tiempo(tiempo_total),
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
                self.graph[u][v]["tiempo_segundos"] = max(5.0, float(t_estimado))

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

    def comparar_rutas(self, origen = str, destino = str, hora_dia = int, dia_semana = str, clima = str, es_feriado: bool = False):
        ruta_estatica = self.calcular_ruta_dijkstra(origen, destino, criterio_peso= "distancia_metros")
        if not ruta_estatica:
            return None

        self.actualizar_pesos(hora_dia, dia_semana, clima, es_feriado)

        tiempo_real_estatica = 0.0
        nodos_estatica= ruta_estatica["camino_nodos"]
        for i in range(len(nodos_estatica) -1 ):
            u = nodos_estatica[i]
            v = nodos_estatica[i+1]
            tiempo_real_estatica += self.graph[u][v]["tiempo_segundos"]
        
        ruta_estatica["tiempo_con_trafico_segundos"] = round(tiempo_real_estatica, 1)
        ruta_estatica["tiempo_con_trafico_minutos"] = round(tiempo_real_estatica / 60, 2)
        ruta_estatica["tiempo_con_trafico_formateado"] = self.formatear_tiempo(tiempo_real_estatica)

        ruta_dinamica = self.calcular_ruta_dijkstra(origen,destino,criterio_peso= "tiempo_segundos")

        ahorro_segundos = max(0.0, tiempo_real_estatica - ruta_dinamica["total_segundos"])
        ahorro_minutos = round(ahorro_segundos / 60, 2)
        ahorro_porcentaje = round((ahorro_segundos / tiempo_real_estatica) * 100, 1) if tiempo_real_estatica > 0 else 0.0

        son_caminos_distintos= ruta_estatica["camino_nodos"] != ruta_dinamica["camino_nodos"]

        return {
            "contexto": {
                "hora_dia": hora_dia,
                "dia_semana": dia_semana,
                "clima": clima,
                "es_feriado": es_feriado
            },
            "origen": origen,
            "destino": destino,
            "caminos_distintos": son_caminos_distintos,
            "ruta_estatica": ruta_estatica,
            "ruta_dinamica": ruta_dinamica,
            "ahorro_minutos": ahorro_minutos,
            "ahorro_formateado": self.formatear_tiempo(ahorro_segundos),
            "ahorro_porcentaje": ahorro_porcentaje
        }

    def calcular_ronda_entregas(self, origen = str, destinos = list[str], criterio_peso: str="tiempo_segundos", volver_origen: bool = True ):
        if not destinos:
            return None

        pendientes = list(destinos)
        nodo_actual = origen

        orden_visita= [origen]
        camino_completo= [origen]
        distancia_total= 0.0
        tiempo_total = 0.0
        etapas_viaje = []

        while pendientes:
            mejor_proximo_nodo = None
            mejor_ruta = None
            menor_costo = float("inf")

            for candidato in pendientes:
                ruta = self.calcular_ruta_dijkstra(nodo_actual, candidato, criterio_peso= criterio_peso)
                if ruta is not None:
                    costo = ruta["total_segundos"] if criterio_peso == "tiempo_segundos" else ruta["total_metros"]
                    if costo < menor_costo:
                        mejor_ruta = ruta
                        mejor_proximo_nodo = candidato
                        menor_costo = costo

            if mejor_proximo_nodo is None:
                print(f"no hay ruta disponible para los puntos restantes: {pendientes}")
                break

            pendientes.remove(mejor_proximo_nodo)
            orden_visita.append(mejor_proximo_nodo)
            camino_completo.extend(mejor_ruta["camino_nodos"][1:])
            distancia_total += mejor_ruta["total_metros"]
            tiempo_total += mejor_ruta["total_segundos"]

            etapas_viaje.append({
                "desde": nodo_actual,
                "hasta": mejor_proximo_nodo,
                "distancia_metros": mejor_ruta["total_metros"],
                "tiempo_segundos": mejor_ruta["total_segundos"],
                "tiempo_formateado": mejor_ruta["tiempo_formateado"],
            })

            nodo_actual = mejor_proximo_nodo

        if volver_origen and nodo_actual != origen:
            ruta_regreso = self.calcular_ruta_dijkstra(nodo_actual, origen, criterio_peso=criterio_peso)
            if ruta_regreso is not None:
                orden_visita.append(origen)
                camino_completo.extend(ruta_regreso["camino_nodos"][1:])
                distancia_total += ruta_regreso["total_metros"]
                tiempo_total += ruta_regreso["total_segundos"]
                etapas_viaje.append({
                    "desde": nodo_actual,
                    "hasta": origen,
                    "distancia_metros": ruta_regreso["total_metros"],
                    "tiempo_segundos": ruta_regreso["total_segundos"],
                    "tiempo_formateado": ruta_regreso["tiempo_formateado"]
                })

        return {
            "deposito": origen, 
            "orden_visitas": orden_visita,
            "camino_completo_nodos": camino_completo,
            "distancia_total_metros": round(distancia_total, 1),
            "tiempo_total_segundos": round(tiempo_total, 1),
            "tiempo_total_minutos": round(tiempo_total / 60, 2),
            "tiempo_total_formateado": self.formatear_tiempo(tiempo_total),
            "etapas_viaje": etapas_viaje
        }


if __name__ == "__main__":
    router = CityGraphRouter()


    resultado = router.comparar_rutas(
        origen="N_0_0",
        destino="N_3_3",
        hora_dia=18,
        dia_semana="lunes",
        clima="tormenta",
        es_feriado=False
    )

    print(f"contexto: lunes 18:00 hs con Tormenta , origen: {resultado['origen']} -> Destino: {resultado['destino']}")
    print("-" * 55)
    print("1. ruta estatica (GPS convencional sin tráfico):")
    print("   camino:", " -> ".join(resultado["ruta_estatica"]["camino_nodos"]))
    print(f"   distancia: {resultado['ruta_estatica']['total_metros']} m")
    print(f"   tiempo con trafico real: {resultado['ruta_estatica']['tiempo_con_trafico_minutos']} minutos")
    print("-" * 55)
    print("2. ruta dinamica (Optimización por Grafo + Predicción):")
    print("   camino:", " -> ".join(resultado["ruta_dinamica"]["camino_nodos"]))
    print(f"   distancia: {resultado['ruta_dinamica']['total_metros']} m")
    print(f"   tiempo optimizado:       {resultado['ruta_dinamica']['total_minutos']} minutos")
    print("-" * 55)
    print(f"cambio la ruta?: {'SÍ' if resultado['caminos_distintos'] else 'NO'}")
    print(f"ahorro de tiempo: {resultado['ahorro_formateado']} minutos ({resultado['ahorro_porcentaje']}%)")

 
    pedidos = ["N_0_3", "N_2_2", "N_3_1"]
    ronda = router.calcular_ronda_entregas(
        origen="N_0_0",
        destinos=pedidos,
        criterio_peso="tiempo_segundos",
        volver_origen=True
    )

    print("\n---Ronda de entregas---")
    print(f"Depósito de salida: {ronda['deposito']}")
    print(f"Puntos solicitados: {pedidos}")
    print(f"Orden de entrega óptimo: {' -> '.join(ronda['orden_visitas'])}")
    print(f"Distancia total recorrida: {ronda['distancia_total_metros']} m")
    print(f"Tiempo total de la ronda:  {ronda['tiempo_total_formateado']} (MM:SS)")

