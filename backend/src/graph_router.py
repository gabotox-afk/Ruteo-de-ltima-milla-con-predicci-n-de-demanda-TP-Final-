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
                t_seg = max(5.0, float(t_estimado))
                self.graph[u][v]["tiempo_segundos"] = t_seg
                self.graph[u][v]["tiempos_segundos"] = t_seg

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

    def planificar_ronda_entregas(
        self,
        deposito: str,
        destinos: list,
        criterio_peso: str = "tiempo_segundos",
        retornar_al_deposito: bool = False
    ) -> dict:
        """
        Calcula la ronda de entregas óptima a partir de un depósito y una lista de esquinas (clientes)
        utilizando la heurística voraz del Vecino Más Cercano (Nearest Neighbor) basada en Dijkstra.

        Parámetros:
            deposito: ID del nodo de inicio/depósito (ej: 'N_0_0').
            destinos: Lista de esquinas donde entregar paquetes (ej: ['N_0_1', 'N_2_2', 'N_3_1']).
            criterio_peso: 'tiempo_segundos' (para minimizar tiempo) o 'distancia_metros'.
            retornar_al_deposito: Si True, incluye el tramo de regreso al depósito al finalizar.

        Retorna:
            Diccionario con la secuencia ordenada de visita, camino completo continuo y métricas totales.
        """
        # Filtrar destinos válidos, únicos y excluir el depósito de la lista de pendientes inicial
        pendientes = [d for d in dict.fromkeys(destinos) if d != deposito and d in self.graph]

        actual = deposito
        secuencia_visita = [deposito]
        camino_completo_nodos = [deposito]
        etapas = []
        distancia_total = 0.0
        tiempo_total = 0.0
        todos_los_tramos = []

        while pendientes:
            mejor_candidato = None
            mejor_ruta = None
            mejor_costo = float("inf")

            for candidato in pendientes:
                ruta = self.calcular_ruta_dijkstra(actual, candidato, criterio_peso=criterio_peso)
                if ruta is not None:
                    costo = ruta["total_segundos"] if criterio_peso == "tiempo_segundos" else ruta["total_metros"]
                    if costo < mejor_costo:
                        mejor_costo = costo
                        mejor_candidato = candidato
                        mejor_ruta = ruta

            if mejor_candidato is None:
                print(f"[AVISO] No se pudo encontrar camino alcanzable desde {actual} hacia {pendientes}")
                break

            # Registrar la etapa
            etapas.append({
                "desde": actual,
                "hacia": mejor_candidato,
                "distancia_metros": mejor_ruta["total_metros"],
                "segundos": mejor_ruta["total_segundos"],
                "minutos": mejor_ruta["total_minutos"],
                "tiempo_formateado": mejor_ruta["tiempo_formateado"],
                "camino_nodos": mejor_ruta["camino_nodos"],
                "detalle_tramos": mejor_ruta["detalle_tramos"]
            })

            secuencia_visita.append(mejor_candidato)
            camino_completo_nodos.extend(mejor_ruta["camino_nodos"][1:])
            distancia_total += mejor_ruta["total_metros"]
            tiempo_total += mejor_ruta["total_segundos"]
            todos_los_tramos.extend(mejor_ruta["detalle_tramos"])

            pendientes.remove(mejor_candidato)
            actual = mejor_candidato

        # Tramo opcional de regreso al depósito
        if retornar_al_deposito and actual != deposito:
            ruta_regreso = self.calcular_ruta_dijkstra(actual, deposito, criterio_peso=criterio_peso)
            if ruta_regreso is not None:
                etapas.append({
                    "desde": actual,
                    "hacia": deposito,
                    "distancia_metros": ruta_regreso["total_metros"],
                    "segundos": ruta_regreso["total_segundos"],
                    "minutos": ruta_regreso["total_minutos"],
                    "tiempo_formateado": ruta_regreso["tiempo_formateado"],
                    "camino_nodos": ruta_regreso["camino_nodos"],
                    "detalle_tramos": ruta_regreso["detalle_tramos"],
                    "es_regreso": True
                })
                secuencia_visita.append(deposito)
                camino_completo_nodos.extend(ruta_regreso["camino_nodos"][1:])
                distancia_total += ruta_regreso["total_metros"]
                tiempo_total += ruta_regreso["total_segundos"]
                todos_los_tramos.extend(ruta_regreso["detalle_tramos"])

        return {
            "deposito": deposito,
            "destinos_solicitados": destinos,
            "criterio": criterio_peso,
            "secuencia_visita": secuencia_visita,
            "clientes_ordenados": [n for n in secuencia_visita if n != deposito],
            "camino_completo_nodos": camino_completo_nodos,
            "total_metros": round(distancia_total, 1),
            "total_segundos": round(tiempo_total, 1),
            "total_minutos": round(tiempo_total / 60, 2),
            "tiempo_formateado": self.formatear_tiempo(tiempo_total),
            "etapas": etapas,
            "detalle_tramos": todos_los_tramos
        }

    # Alias para mayor compatibilidad
    ordenar_entregas_nearest_neighbor = planificar_ronda_entregas
    resolver_ronda_entregas = planificar_ronda_entregas


def planificar_ronda_entregas(
    deposito: str,
    destinos: list,
    router: CityGraphRouter = None,
    criterio_peso: str = "tiempo_segundos",
    retornar_al_deposito: bool = False
) -> dict:
    """
    Función modular para planificar la ronda de entregas con Nearest Neighbor.
    Crea una instancia de CityGraphRouter si no se proporciona una.
    """
    if router is None:
        router = CityGraphRouter()
    return router.planificar_ronda_entregas(
        deposito=deposito,
        destinos=destinos,
        criterio_peso=criterio_peso,
        retornar_al_deposito=retornar_al_deposito
    )


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

    # Demostración Issue 5: Ronda de entregas (Nearest Neighbor)
    print("\n" + "=" * 55)
    print("3. RONDA DE ENTREGAS (Heurística Vecino Más Cercano)")
    print("=" * 55)
    deposito_ejemplo = "N_0_0"
    pedidos_ejemplo = ["N_0_1", "N_2_2", "N_3_1"]

    ronda = router.planificar_ronda_entregas(
        deposito=deposito_ejemplo,
        destinos=pedidos_ejemplo,
        criterio_peso="tiempo_segundos"
    )

    print(f"Punto de inicio (depósito): {ronda['deposito']}")
    print(f"Pedidos solicitados:         {ronda['destinos_solicitados']}")
    print(f"Orden de visita calculado:   {' -> '.join(ronda['secuencia_visita'])}")
    print(f"Recorrido completo nodos:    {' -> '.join(ronda['camino_completo_nodos'])}")
    print(f"Distancia total:             {ronda['total_metros']} m")
    print(f"Tiempo total estimado:       {ronda['tiempo_formateado']} ({ronda['total_minutos']} min)")
    print("-" * 55)
    print("Detalle de etapas:")
    for idx, etapa in enumerate(ronda["etapas"], start=1):
        print(
            f"   Etapa {idx}: {etapa['desde']} -> {etapa['hacia']} | "
            f"{etapa['distancia_metros']} m | {etapa['tiempo_formateado']} min | "
            f"Nodos: {' -> '.join(etapa['camino_nodos'])}"
        )
    print("=" * 55)
