import { GrafoData, MetricasDict, ResultadoComparacion, ResultadoRonda } from '../types';

const API_BASE = '/api';

export async function fetchGrafo(): Promise<GrafoData> {
  const res = await fetch(`${API_BASE}/grafo`);
  if (!res.ok) {
    throw new Error(`Error al obtener el grafo: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchMetricas(): Promise<MetricasDict> {
  const res = await fetch(`${API_BASE}/metricas`);
  if (!res.ok) {
    throw new Error(`Error al obtener las métricas: ${res.statusText}`);
  }
  return res.json();
}

export interface CalcularRutaPayload {
  origen: string;
  destino: string;
  hora_dia: number;
  dia_semana: string;
  clima: string;
  es_feriado: boolean;
}

export async function calcularRuta(payload: CalcularRutaPayload): Promise<ResultadoComparacion> {
  const res = await fetch(`${API_BASE}/calcular-ruta`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.error || `Error al calcular ruta: ${res.statusText}`);
  }
  return res.json();
}

export interface RondaEntregasPayload {
  deposito: string;
  destinos: string[];
  hora_dia: number;
  dia_semana: string;
  clima: string;
  es_feriado: boolean;
  criterio_peso?: string;
  retornar_al_deposito?: boolean;
}

export async function planificarRonda(payload: RondaEntregasPayload): Promise<ResultadoRonda> {
  const res = await fetch(`${API_BASE}/ronda-entregas`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.error || `Error al planificar ronda: ${res.statusText}`);
  }
  return res.json();
}
