import React, { useState, useEffect, useCallback } from 'react';
import { GrafoData, MetricasDict, ResultadoComparacion, ResultadoRonda } from './types';
import { fetchGrafo, fetchMetricas, calcularRuta, planificarRonda } from './services/api';
import { CityMap } from './components/CityMap';
import { RouteControls } from './components/RouteControls';
import { RouteComparison } from './components/RouteComparison';
import { DeliveryRoundPanel } from './components/DeliveryRoundPanel';
import { MetricsPanel } from './components/MetricsPanel';
import './App.css';

export const App: React.FC = () => {
  // Estado del Grafo y Métricas del Backend
  const [grafo, setGrafo] = useState<GrafoData | null>(null);
  const [metricas, setMetricas] = useState<MetricasDict | null>(null);
  const [loadingInit, setLoadingInit] = useState(true);
  const [backendError, setBackendError] = useState<string | null>(null);

  // Parámetros de Ruteo Punto a Punto
  const [origen, setOrigen] = useState<string>('N_0_0');
  const [destino, setDestino] = useState<string>('N_3_3');

  // Condiciones de Contexto Dinámico
  const [horaDia, setHoraDia] = useState<number>(18);
  const [diaSemana, setDiaSemana] = useState<string>('lunes');
  const [clima, setClima] = useState<string>('tormenta');
  const [esFeriado, setEsFeriado] = useState<boolean>(false);

  // Modo de operación: 'punto_a_punto' | 'ronda_entregas'
  const [modo, setModo] = useState<'punto_a_punto' | 'ronda_entregas'>('punto_a_punto');

  // Parámetros de Ronda de Entregas
  const [deposito, setDeposito] = useState<string>('N_0_0');
  const [puntosEntrega, setPuntosEntrega] = useState<string[]>(['N_0_1', 'N_2_2', 'N_3_1']);
  const [retornarAlDeposito, setRetornarAlDeposito] = useState<boolean>(false);

  // Resultados
  const [resultadoRuta, setResultadoRuta] = useState<ResultadoComparacion | null>(null);
  const [resultadoRonda, setResultadoRonda] = useState<ResultadoRonda | null>(null);
  const [loadingCalculo, setLoadingCalculo] = useState<boolean>(false);
  const [calculoError, setCalculoError] = useState<string | null>(null);

  // Pestaña activa ('ruteo' | 'metricas')
  const [vistaActiva, setVistaActiva] = useState<'ruteo' | 'metricas'>('ruteo');

  // Carga inicial de datos desde la API
  useEffect(() => {
    async function init() {
      try {
        setLoadingInit(true);
        setBackendError(null);
        const [grafoData, metricasData] = await Promise.all([
          fetchGrafo(),
          fetchMetricas().catch(() => null),
        ]);
        setGrafo(grafoData);
        if (metricasData) setMetricas(metricasData);
      } catch (err: any) {
        console.error('Error inicializando datos del backend:', err);
        setBackendError(
          'No se pudo conectar con la API. Inicia el servidor con `python backend/src/api.py`.'
        );
      } finally {
        setLoadingInit(false);
      }
    }
    init();
  }, []);

  // Función para calcular la ruta punto a punto
  const handleCalcularRuta = useCallback(async () => {
    if (!origen || !destino) return;
    try {
      setLoadingCalculo(true);
      setCalculoError(null);
      const res = await calcularRuta({
        origen,
        destino,
        hora_dia: horaDia,
        dia_semana: diaSemana,
        clima,
        es_feriado: esFeriado,
      });
      setResultadoRuta(res);
    } catch (err: any) {
      setCalculoError(err.message || 'Error al calcular la ruta');
    } finally {
      setLoadingCalculo(false);
    }
  }, [origen, destino, horaDia, diaSemana, clima, esFeriado]);

  // Función para planificar la ronda de entregas (Nearest Neighbor)
  const handleCalcularRonda = useCallback(async () => {
    if (!deposito || puntosEntrega.length === 0) return;
    try {
      setLoadingCalculo(true);
      setCalculoError(null);
      const res = await planificarRonda({
        deposito,
        destinos: puntosEntrega,
        hora_dia: horaDia,
        dia_semana: diaSemana,
        clima,
        es_feriado: esFeriado,
        criterio_peso: 'tiempo_segundos',
        retornar_al_deposito: retornarAlDeposito,
      });
      setResultadoRonda(res);
    } catch (err: any) {
      setCalculoError(err.message || 'Error al planificar la ronda de entregas');
    } finally {
      setLoadingCalculo(false);
    }
  }, [deposito, puntosEntrega, horaDia, diaSemana, clima, esFeriado, retornarAlDeposito]);

  // Calcular automáticamente la primera ruta al cargar el grafo
  useEffect(() => {
    if (grafo && !resultadoRuta && !loadingCalculo) {
      handleCalcularRuta();
    }
  }, [grafo, handleCalcularRuta, resultadoRuta, loadingCalculo]);

  const handleSelectNodo = (nodoId: string, tipo: 'origen' | 'destino' | 'entrega') => {
    if (tipo === 'origen') {
      if (modo === 'punto_a_punto') setOrigen(nodoId);
      else setDeposito(nodoId);
    } else if (tipo === 'destino') {
      setDestino(nodoId);
    } else if (tipo === 'entrega') {
      setPuntosEntrega((prev) =>
        prev.includes(nodoId) ? prev.filter((id) => id !== nodoId) : [...prev, nodoId]
      );
    }
  };

  const handleTogglePuntoEntrega = (nodoId: string) => {
    setPuntosEntrega((prev) =>
      prev.includes(nodoId) ? prev.filter((id) => id !== nodoId) : [...prev, nodoId]
    );
  };

  return (
    <div className="app-container">
      {/* Header Superior Simple y Blanco */}
      <header className="app-header">
        <div className="header-brand">
          <div>
            <h1 className="brand-title">Ruteo de Última Milla</h1>
            <p className="brand-subtitle">
              Red Vial Urbana de Buenos Aires • Optimización con Random Forest y Dijkstra
            </p>
          </div>
        </div>

        <div className="header-nav">
          <button
            className={`nav-tab-btn ${vistaActiva === 'ruteo' ? 'active' : ''}`}
            onClick={() => setVistaActiva('ruteo')}
          >
            Ruteo y Entregas
          </button>
          <button
            className={`nav-tab-btn ${vistaActiva === 'metricas' ? 'active' : ''}`}
            onClick={() => setVistaActiva('metricas')}
          >
            Métricas del Modelo
          </button>
        </div>
      </header>

      {/* Alerta de Error de Backend */}
      {backendError && (
        <div className="alert-banner alert-danger">
          <div className="alert-text">
            <strong>Error de conexión con la API:</strong> {backendError}
          </div>
          <button className="btn-retry" onClick={() => window.location.reload()}>
            Reintentar
          </button>
        </div>
      )}

      {/* Alerta de Error de Cálculo */}
      {calculoError && (
        <div className="alert-banner alert-warning">
          <div className="alert-text">{calculoError}</div>
          <button className="btn-close-alert" onClick={() => setCalculoError(null)}>Cerrar</button>
        </div>
      )}

      {/* Contenido Principal */}
      <main className="app-main">
        {vistaActiva === 'metricas' ? (
          <div className="metrics-view">
            <MetricsPanel metricas={metricas} loading={loadingInit} />
          </div>
        ) : (
          <div className="routing-layout">
            {/* Panel Lateral de Controles y Resultados */}
            <aside className="sidebar-panel">
              <RouteControls
                nodos={grafo ? grafo.nodos : []}
                origen={origen}
                destino={destino}
                horaDia={horaDia}
                diaSemana={diaSemana}
                clima={clima}
                esFeriado={esFeriado}
                modo={modo}
                loading={loadingCalculo}
                onOrigenChange={setOrigen}
                onDestinoChange={setDestino}
                onHoraChange={setHoraDia}
                onDiaChange={setDiaSemana}
                onClimaChange={setClima}
                onFeriadoChange={setEsFeriado}
                onModoChange={setModo}
                onCalcular={handleCalcularRuta}
              />

              {modo === 'ronda_entregas' && (
                <DeliveryRoundPanel
                  nodos={grafo ? grafo.nodos : []}
                  deposito={deposito}
                  puntosEntrega={puntosEntrega}
                  retornarAlDeposito={retornarAlDeposito}
                  loading={loadingCalculo}
                  resultadoRonda={resultadoRonda}
                  onDepositoChange={setDeposito}
                  onTogglePuntoEntrega={handleTogglePuntoEntrega}
                  onCargarEjemplo={() => setPuntosEntrega(['N_0_1', 'N_2_2', 'N_3_1'])}
                  onLimpiarPuntos={() => setPuntosEntrega([])}
                  onRetornarDepositoChange={setRetornarAlDeposito}
                  onCalcularRonda={handleCalcularRonda}
                />
              )}

              {modo === 'punto_a_punto' && (
                <RouteComparison resultado={resultadoRuta} loading={loadingCalculo} />
              )}
            </aside>

            {/* Panel Principal: Mapa de la Ciudad */}
            <section className="map-panel">
              <CityMap
                grafo={grafo}
                origen={origen}
                destino={destino}
                onSelectNodo={handleSelectNodo}
                resultadoRuta={resultadoRuta}
                resultadoRonda={resultadoRonda}
                modo={modo}
                puntosEntrega={puntosEntrega}
                deposito={deposito}
              />
            </section>
          </div>
        )}
      </main>
    </div>
  );
};
export default App;
