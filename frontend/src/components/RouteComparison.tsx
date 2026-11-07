import React from 'react';
import { ResultadoComparacion } from '../types';

interface RouteComparisonProps {
  resultado: ResultadoComparacion | null;
  loading: boolean;
}

export const RouteComparison: React.FC<RouteComparisonProps> = ({ resultado, loading }) => {
  if (loading) {
    return (
      <div className="comparison-loading">
        <div className="spinner"></div>
        <p>Calculando ruta óptima con algoritmo Dijkstra y Random Forest...</p>
      </div>
    );
  }

  if (!resultado) {
    return (
      <div className="empty-state">
        <h3>Listo para calcular</h3>
        <p>Selecciona origen, destino y condiciones climáticas para calcular la ruta.</p>
      </div>
    );
  }

  const { ruta_estatica, ruta_dinamica, ahorro_formateado, ahorro_porcentaje, caminos_distintos, contexto } = resultado;

  return (
    <div className="route-comparison-container">
      {/* Banner de Ahorro */}
      <div className={`savings-banner ${caminos_distintos ? 'banner-alternate' : 'banner-same'}`}>
        <div className="savings-main">
          <div className="savings-badge">
            {caminos_distintos ? 'Camino Alternativo con IA' : 'Mismo Camino'}
          </div>
          <div className="savings-number">
            Ahorro estimado: <strong>{ahorro_formateado} min</strong> ({ahorro_porcentaje}%)
          </div>
        </div>
        <p className="savings-explanation">
          {caminos_distintos
            ? `Bajo clima ${contexto.clima} a las ${contexto.hora_dia}:00 hs, el modelo desvía el trayecto por calles con menor congestión.`
            : `El camino convencional es el más rápido bajo las condiciones actuales.`}
        </p>
      </div>

      {/* Tarjetas Comparativas */}
      <div className="comparison-cards-grid">
        {/* Tarjeta 1: Ruta Estática */}
        <div className="card-route static-route-card">
          <div className="card-header">
            <span className="route-badge static-badge">Ruta Estática</span>
            <span className="route-type-subtitle">Distancia</span>
          </div>

          <div className="metrics-row">
            <div className="metric-item">
              <span className="metric-label">Distancia Total</span>
              <span className="metric-val">{ruta_estatica.total_metros} m</span>
            </div>
            <div className="metric-item">
              <span className="metric-label">Tiempo c/ Tráfico Real</span>
              <span className="metric-val warning-val">
                {ruta_estatica.tiempo_con_trafico_formateado || `${ruta_estatica.tiempo_con_trafico_minutos}m`}
              </span>
            </div>
          </div>

          <div className="route-path-summary">
            <span className="path-label">Secuencia ({ruta_estatica.camino_nodos.length} esquinas):</span>
            <div className="nodes-chips">
              {ruta_estatica.camino_nodos.map((n, i) => (
                <span key={i} className="node-chip chip-static">
                  {n}
                  {i < ruta_estatica.camino_nodos.length - 1 && ' -> '}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Tarjeta 2: Ruta Dinámica (IA) */}
        <div className="card-route dynamic-route-card">
          <div className="card-header">
            <span className="route-badge dynamic-badge">Ruta Dinámica</span>
            <span className="route-type-subtitle">Predicción IA</span>
          </div>

          <div className="metrics-row">
            <div className="metric-item">
              <span className="metric-label">Distancia Total</span>
              <span className="metric-val">{ruta_dinamica.total_metros} m</span>
            </div>
            <div className="metric-item">
              <span className="metric-label">Tiempo Estimado</span>
              <span className="metric-val success-val">
                {ruta_dinamica.tiempo_formateado || `${ruta_dinamica.total_minutos}m`}
              </span>
            </div>
          </div>

          <div className="route-path-summary">
            <span className="path-label">Secuencia ({ruta_dinamica.camino_nodos.length} esquinas):</span>
            <div className="nodes-chips">
              {ruta_dinamica.camino_nodos.map((n, i) => (
                <span key={i} className="node-chip chip-dynamic">
                  {n}
                  {i < ruta_dinamica.camino_nodos.length - 1 && ' -> '}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Desglose de Tramos */}
      <details className="details-accordion">
        <summary className="accordion-summary">
          Ver detalle tramo por tramo
        </summary>
        <div className="accordion-content">
          <table className="tramos-table">
            <thead>
              <tr>
                <th>Tramo</th>
                <th>Desde</th>
                <th>Hasta</th>
                <th>Tipo</th>
                <th>Distancia</th>
                <th>Tiempo Estimado</th>
              </tr>
            </thead>
            <tbody>
              {ruta_dinamica.detalle_tramos.map((t, idx) => (
                <tr key={idx}>
                  <td><strong>{t.tramo_id}</strong></td>
                  <td>{t.desde}</td>
                  <td>{t.hasta}</td>
                  <td><span className={`tag-calle ${t.tipo}`}>{t.tipo}</span></td>
                  <td>{t.distancia} m</td>
                  <td>{t.tiempo.toFixed(1)} s</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
};
