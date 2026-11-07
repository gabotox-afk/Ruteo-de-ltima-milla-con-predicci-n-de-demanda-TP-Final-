import React from 'react';
import { Nodo, ResultadoRonda } from '../types';

interface DeliveryRoundPanelProps {
  nodos: Nodo[];
  deposito: string;
  puntosEntrega: string[];
  retornarAlDeposito: boolean;
  loading: boolean;
  resultadoRonda: ResultadoRonda | null;
  onDepositoChange: (val: string) => void;
  onTogglePuntoEntrega: (nodoId: string) => void;
  onCargarEjemplo: () => void;
  onLimpiarPuntos: () => void;
  onRetornarDepositoChange: (val: boolean) => void;
  onCalcularRonda: () => void;
}

export const DeliveryRoundPanel: React.FC<DeliveryRoundPanelProps> = ({
  nodos,
  deposito,
  puntosEntrega,
  retornarAlDeposito,
  loading,
  resultadoRonda,
  onDepositoChange,
  onTogglePuntoEntrega,
  onCargarEjemplo,
  onLimpiarPuntos,
  onRetornarDepositoChange,
  onCalcularRonda,
}) => {
  return (
    <div className="delivery-panel-container">
      <div className="delivery-config-box">
        <h4 className="section-title">Configuración de Ronda de Entregas</h4>

        {/* Depósito */}
        <div className="form-group">
          <label>Punto de Inicio (Depósito)</label>
          <select
            value={deposito}
            onChange={(e) => onDepositoChange(e.target.value)}
            className="select-custom"
          >
            {nodos.map((n) => (
              <option key={n.id} value={n.id}>
                {n.id} - {n.label}
              </option>
            ))}
          </select>
        </div>

        {/* Clientes a visitar */}
        <div className="form-group">
          <div className="puntos-header">
            <label>Puntos de Entrega ({puntosEntrega.length} seleccionados):</label>
            <div className="puntos-actions">
              <button type="button" className="action-link" onClick={onCargarEjemplo}>
                Cargar Ejemplo
              </button>
              {puntosEntrega.length > 0 && (
                <button type="button" className="action-link text-danger" onClick={onLimpiarPuntos}>
                  Limpiar
                </button>
              )}
            </div>
          </div>

          <div className="nodes-picker-grid">
            {nodos
              .filter((n) => n.id !== deposito)
              .map((n) => {
                const isSelected = puntosEntrega.includes(n.id);
                return (
                  <button
                    key={n.id}
                    type="button"
                    className={`node-pick-btn ${isSelected ? 'picked' : ''}`}
                    onClick={() => onTogglePuntoEntrega(n.id)}
                  >
                    <span>{isSelected ? '✓' : '+'}</span> {n.id}
                  </button>
                );
              })}
          </div>
          <span className="field-hint">Puedes hacer clic en el mapa para agregar o quitar paradas.</span>
        </div>

        {/* Retornar al depósito */}
        <div className="form-group checkbox-group">
          <label className="checkbox-container">
            <input
              type="checkbox"
              checked={retornarAlDeposito}
              onChange={(e) => onRetornarDepositoChange(e.target.checked)}
            />
            <span className="checkmark"></span>
            Retornar al depósito al finalizar
          </label>
        </div>

        {/* Botón calcular ronda */}
        <button
          className="btn-calcular btn-ronda"
          onClick={onCalcularRonda}
          disabled={loading || puntosEntrega.length === 0}
        >
          {loading ? (
            <>
              <span className="spinner-mini"></span> Optimizando Ronda...
            </>
          ) : (
            `Calcular Ronda de Entregas (${puntosEntrega.length} paradas)`
          )}
        </button>
      </div>

      {/* Resultados de la Ronda */}
      {resultadoRonda && (
        <div className="delivery-results-box">
          <div className="round-summary-header">
            <h4>Secuencia Óptima de Visita</h4>
            <span className="round-badge">Nearest Neighbor</span>
          </div>

          <div className="metrics-row">
            <div className="metric-item">
              <span className="metric-label">Distancia Total</span>
              <span className="metric-val">{resultadoRonda.total_metros} m</span>
            </div>
            <div className="metric-item">
              <span className="metric-label">Tiempo Estimado</span>
              <span className="metric-val success-val">{resultadoRonda.tiempo_formateado} ({resultadoRonda.total_minutos} min)</span>
            </div>
            <div className="metric-item">
              <span className="metric-label">Paradas</span>
              <span className="metric-val">{resultadoRonda.clientes_ordenados.length} clientes</span>
            </div>
          </div>

          {/* Secuencia visual numerada */}
          <div className="ordered-stops-list">
            <div className="stop-item stop-origin">
              <span className="stop-number">D</span>
              <div className="stop-info">
                <strong>Depósito: {resultadoRonda.deposito}</strong>
                <span>Punto de partida de la unidad</span>
              </div>
            </div>

            {resultadoRonda.etapas.map((etapa, idx) => (
              <div key={idx} className={`stop-item ${etapa.es_regreso ? 'stop-return' : 'stop-client'}`}>
                <span className="stop-number">{etapa.es_regreso ? 'R' : idx + 1}</span>
                <div className="stop-info">
                  <strong>
                    {etapa.es_regreso ? `Regreso al depósito: ${etapa.hacia}` : `Entrega ${idx + 1}: ${etapa.hacia}`}
                  </strong>
                  <span>
                    Tramo: {etapa.desde} ➔ {etapa.hacia} | Distancia: {etapa.distancia_metros}m | Tiempo: {etapa.tiempo_formateado}
                  </span>
                  <div className="sub-path">
                    Camino: {etapa.camino_nodos.join(' ➔ ')}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
