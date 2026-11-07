import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import sys

# Asegurar que el directorio src esté en sys.path
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from graph_router import CityGraphRouter
except ImportError:
    from backend.src.graph_router import CityGraphRouter

DATA_DIR = SRC_DIR.parent / "data"
GRAPH_PATH = DATA_DIR / "city_graph.json"
METRICS_PATH = DATA_DIR / "metricas_modelos.json"

# Instancia global del router para reutilizar el grafo y el modelo en memoria
router = CityGraphRouter()


class CityRouterAPIHandler(BaseHTTPRequestHandler):

    def _set_cors_headers(self, status_code=200):
        self.send_response(status_code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()

    def do_OPTIONS(self):
        # Responder preflight CORS
        self._set_cors_headers(204)

    def _send_json(self, data, status_code=200):
        self._set_cors_headers(status_code)
        response_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.wfile.write(response_bytes)

    def _send_error_json(self, message: str, status_code=400):
        self._send_json({"error": message}, status_code=status_code)

    def _read_body_json(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                return {}
            body_bytes = self.rfile.read(content_length)
            return json.loads(body_bytes.decode("utf-8"))
        except Exception as e:
            return None

    def do_GET(self):
        url_path = self.path.split("?")[0]

        if url_path == "/" or url_path == "/api/health":
            self._send_json({
                "status": "online",
                "modelo_cargado": router.modelo is not None,
                "nodos_grafo": router.graph.number_of_nodes(),
                "tramos_grafo": router.graph.number_of_edges(),
            })

        elif url_path == "/api/grafo":
            if not GRAPH_PATH.exists():
                self._send_error_json("Archivo city_graph.json no encontrado", 404)
                return
            with open(GRAPH_PATH, "r", encoding="utf-8") as f:
                grafo_data = json.load(f)
            self._send_json(grafo_data)

        elif url_path == "/api/metricas":
            if not METRICS_PATH.exists():
                self._send_error_json("Archivo metricas_modelos.json no encontrado", 404)
                return
            with open(METRICS_PATH, "r", encoding="utf-8") as f:
                metricas_data = json.load(f)
            self._send_json(metricas_data)

        else:
            self._send_error_json(f"Ruta no encontrada: {url_path}", 404)

    def do_POST(self):
        url_path = self.path.split("?")[0]
        payload = self._read_body_json()

        if payload is None:
            self._send_error_json("JSON inválido en el cuerpo de la solicitud", 400)
            return

        if url_path == "/api/calcular-ruta":
            origen = payload.get("origen", "N_0_0")
            destino = payload.get("destino", "N_3_3")
            hora_dia = int(payload.get("hora_dia", 18))
            dia_semana = str(payload.get("dia_semana", "lunes"))
            clima = str(payload.get("clima", "soleado"))
            es_feriado = bool(payload.get("es_feriado", False))

            try:
                resultado = router.comparar_rutas(
                    origen=origen,
                    destino=destino,
                    hora_dia=hora_dia,
                    dia_semana=dia_semana,
                    clima=clima,
                    es_feriado=es_feriado
                )
                if resultado is None:
                    self._send_error_json(f"No existe camino entre {origen} y {destino}", 404)
                    return
                self._send_json(resultado)
            except Exception as e:
                self._send_error_json(f"Error al calcular la ruta: {str(e)}", 500)

        elif url_path == "/api/ronda-entregas":
            deposito = payload.get("deposito", "N_0_0")
            destinos = payload.get("destinos", ["N_0_1", "N_2_2", "N_3_1"])
            hora_dia = int(payload.get("hora_dia", 18))
            dia_semana = str(payload.get("dia_semana", "lunes"))
            clima = str(payload.get("clima", "soleado"))
            es_feriado = bool(payload.get("es_feriado", False))
            criterio_peso = payload.get("criterio_peso", "tiempo_segundos")
            retornar_al_deposito = bool(payload.get("retornar_al_deposito", False))

            try:
                # Actualizar pesos en el grafo antes de calcular la ronda de entregas
                router.actualizar_pesos(
                    hora_dia=hora_dia,
                    dia_semana=dia_semana,
                    clima=clima,
                    es_feriado=es_feriado
                )
                ronda = router.planificar_ronda_entregas(
                    deposito=deposito,
                    destinos=destinos,
                    criterio_peso=criterio_peso,
                    retornar_al_deposito=retornar_al_deposito
                )
                self._send_json(ronda)
            except Exception as e:
                self._send_error_json(f"Error al planificar ronda de entregas: {str(e)}", 500)

        else:
            self._send_error_json(f"Ruta no encontrada: {url_path}", 404)

    def log_message(self, format, *args):
        # Log simplificado
        sys.stdout.write(f"[API] {self.address_string()} - {format % args}\n")
        sys.stdout.flush()


def run_server(port=8000, host="0.0.0.0"):
    server_address = (host, port)
    httpd = HTTPServer(server_address, CityRouterAPIHandler)
    print("=" * 60)
    print(f" Servidor API de Ruteo iniciado en http://localhost:{port}")
    print(f" - Grafo: {router.graph.number_of_nodes()} nodos, {router.graph.number_of_edges()} tramos")
    print(f" - Modelo ML: {'Cargado exitosamente' if router.modelo is not None else 'No disponible'}")
    print("=" * 60)
    print("Endpoints disponibles:")
    print(f"  GET  http://localhost:{port}/api/grafo")
    print(f"  GET  http://localhost:{port}/api/metricas")
    print(f"  POST http://localhost:{port}/api/calcular-ruta")
    print(f"  POST http://localhost:{port}/api/ronda-entregas")
    print("=" * 60)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor API detenido.")
        httpd.server_close()


if __name__ == "__main__":
    puerto = 8000
    if len(sys.argv) > 1:
        try:
            puerto = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port=puerto)
