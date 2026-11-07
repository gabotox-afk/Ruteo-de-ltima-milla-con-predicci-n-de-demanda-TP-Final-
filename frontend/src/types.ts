export interface Nodo {
  id: string;
  lat: number;
  lon: number;
  label: string;
}

export interface Arista {
  tramo_id: string;
  origen: string;
  destino: string;
  distancia_metros: number;
  tipo: 'avenida' | 'calle';
  velocidad_base_kmh: number;
}

export interface GrafoMetadata {
  descripcion: string;
  total_nodos: number;
  total_tramos: number;
}

export interface GrafoData {
  metadata: GrafoMetadata;
  nodos: Nodo[];
  aristas: Arista[];
}

export interface TramoDetalle {
  tramo_id: string;
  desde: string;
  hasta: string;
  tipo: string;
  distancia: number;
  tiempo: number;
}

export interface RutaDetalle {
  criterio: string;
  camino_nodos: string[];
  total_metros: number;
  total_segundos?: number;
  total_minutos?: number;
  tiempo_formateado?: string;
  tiempo_con_trafico_segundos?: number;
  tiempo_con_trafico_minutos?: number;
  tiempo_con_trafico_formateado?: string;
  detalle_tramos: TramoDetalle[];
}

export interface ContextoRuta {
  hora_dia: number;
  dia_semana: string;
  clima: string;
  es_feriado: boolean;
}

export interface ResultadoComparacion {
  contexto: ContextoRuta;
  origen: string;
  destino: string;
  caminos_distintos: boolean;
  ruta_estatica: RutaDetalle;
  ruta_dinamica: RutaDetalle;
  ahorro_minutos: number;
  ahorro_formateado: string;
  ahorro_porcentaje: number;
}

export interface EtapaRonda {
  desde: string;
  hacia: string;
  distancia_metros: number;
  segundos: number;
  minutos: number;
  tiempo_formateado: string;
  camino_nodos: string[];
  detalle_tramos: TramoDetalle[];
  es_regreso?: boolean;
}

export interface ResultadoRonda {
  deposito: string;
  destinos_solicitados: string[];
  criterio: string;
  secuencia_visita: string[];
  clientes_ordenados: string[];
  camino_completo_nodos: string[];
  total_metros: number;
  total_segundos: number;
  total_minutos: number;
  tiempo_formateado: string;
  etapas: EtapaRonda[];
  detalle_tramos: TramoDetalle[];
}

export interface MetricasModelo {
  MAE: number;
  RMSE: number;
  R2: number;
}

export type MetricasDict = Record<string, MetricasModelo>;
