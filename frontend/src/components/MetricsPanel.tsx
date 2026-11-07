import React from 'react';
import { MetricasDict } from '../types';

interface MetricsPanelProps {
  metricas: MetricasDict | null;
  loading: boolean;
}

export const MetricsPanel: React.FC<MetricsPanelProps> = ({ metricas, loading }) => {
  if (loading) {
    return <div className="metrics-loading">Cargando métricas de evaluación...</div>;
  }

  if (!metricas) {
    return (
      <div className="metrics-empty">
        <p>No se encontraron métricas exportadas. Ejecuta <code>python backend/src/train_model.py</code> para generarlas.</p>
      </div>
    );
  }

  const mejorModeloNombre = Object.keys(metricas).reduce((mejor, actual) => {
    return metricas[actual].R2 > metricas[mejor].R2 ? actual : mejor;
  }, Object.keys(metricas)[0]);

  const mejorModelo = metricas[mejorModeloNombre];

  return (
    <div className="metrics-panel-container">
      <div className="metrics-intro-card">
        <div className="intro-badge">Modelo Seleccionado para Producción</div>
        <h3 className="winner-title">{mejorModeloNombre}</h3>
        <p className="winner-desc">
          Ensamble de 100 árboles de decisión que captura los efectos de la hora pico, precipitaciones y tramos urbanos.
        </p>

        {/* 3 Métricas Principales */}
        <div className="top-metrics-grid">
          <div className="top-metric-card">
            <span className="top-metric-label">MAE (Error Absoluto Medio)</span>
            <span className="top-metric-value">{mejorModelo.MAE.toFixed(2)} s</span>
            <span className="top-metric-hint">Error promedio por esquina</span>
          </div>

          <div className="top-metric-card">
            <span className="top-metric-label">RMSE (Raíz Error Cuadrático)</span>
            <span className="top-metric-value">{mejorModelo.RMSE.toFixed(2)} s</span>
            <span className="top-metric-hint">Penalización de desvíos grandes</span>
          </div>

          <div className="top-metric-card highlight-card">
            <span className="top-metric-label">R² (Coef. de Determinación)</span>
            <span className="top-metric-value success-val">{(mejorModelo.R2 * 100).toFixed(1)}%</span>
            <span className="top-metric-hint">{mejorModelo.R2.toFixed(4)} varianza explicada</span>
          </div>
        </div>
      </div>

      {/* Tabla comparativa */}
      <div className="models-comparison-table-wrapper">
        <h4 className="table-heading">Comparativa de Modelos Evaluados</h4>
        <table className="models-table">
          <thead>
            <tr>
              <th>Modelo</th>
              <th>MAE (seg)</th>
              <th>RMSE (seg)</th>
              <th>R² Score</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(metricas).map(([nombre, m]) => {
              const isWinner = nombre === mejorModeloNombre;
              return (
                <tr key={nombre} className={isWinner ? 'winner-row' : ''}>
                  <td>
                    <strong>{nombre}</strong>
                    {isWinner && <span className="winner-tag"> (Mejor R²)</span>}
                  </td>
                  <td>{m.MAE.toFixed(4)}</td>
                  <td>{m.RMSE.toFixed(4)}</td>
                  <td>
                    <strong>{m.R2.toFixed(4)}</strong>
                  </td>
                  <td>
                    <span className={`status-pill ${isWinner ? 'pill-active' : 'pill-bench'}`}>
                      {isWinner ? 'Activo' : 'Benchmark'}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
