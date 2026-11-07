import React from 'react';
import { Nodo } from '../types';

interface RouteControlsProps {
  nodos: Nodo[];
  origen: string;
  destino: string;
  horaDia: number;
  diaSemana: string;
  clima: string;
  esFeriado: boolean;
  modo: 'punto_a_punto' | 'ronda_entregas';
  loading: boolean;
  onOrigenChange: (val: string) => void;
  onDestinoChange: (val: string) => void;
  onHoraChange: (val: number) => void;
  onDiaChange: (val: string) => void;
  onClimaChange: (val: string) => void;
  onFeriadoChange: (val: boolean) => void;
  onModoChange: (modo: 'punto_a_punto' | 'ronda_entregas') => void;
  onCalcular: () => void;
}

export const RouteControls: React.FC<RouteControlsProps> = ({
  nodos,
  origen,
  destino,
  horaDia,
  diaSemana,
  clima,
  esFeriado,
  modo,
  loading,
  onOrigenChange,
  onDestinoChange,
  onHoraChange,
  onDiaChange,
  onClimaChange,
  onFeriadoChange,
  onModoChange,
  onCalcular,
}) => {
  const DIAS = [
    { id: 'lunes', label: 'Lunes' },
    { id: 'martes', label: 'Martes' },
    { id: 'miercoles', label: 'Miércoles' },
    { id: 'jueves', label: 'Jueves' },
    { id: 'viernes', label: 'Viernes' },
    { id: 'sabado', label: 'Sábado (Fin de semana)' },
    { id: 'domingo', label: 'Domingo (Fin de semana)' },
  ];

  const CLIMAS = [
    { id: 'soleado', label: 'Soleado', desc: 'Tráfico estándar' },
    { id: 'lluvia', label: 'Lluvia', desc: '+25% congestión' },
    { id: 'tormenta', label: 'Tormenta', desc: '+60% congestión' },
  ];

  const getTipoHorario = (hora: number) => {
    if ((hora >= 7 && hora <= 9) || (hora >= 17 && hora <= 20)) {
      return { label: 'Hora Pico', className: 'tag-pico' };
    }
    if (hora >= 0 && hora <= 5) {
      return { label: 'Hora Valle', className: 'tag-valle' };
    }
    return { label: 'Horario Regular', className: 'tag-regular' };
  };

  const tipoHora = getTipoHorario(horaDia);

  return (
    <div className="panel-controls">
      {/* Selector de Modo */}
      <div className="modo-tabs">
        <button
          className={`tab-btn ${modo === 'punto_a_punto' ? 'active' : ''}`}
          onClick={() => onModoChange('punto_a_punto')}
        >
          Ruta Punto a Punto
        </button>
        <button
          className={`tab-btn ${modo === 'ronda_entregas' ? 'active' : ''}`}
          onClick={() => onModoChange('ronda_entregas')}
        >
          Ronda de Entregas
        </button>
      </div>

      {modo === 'punto_a_punto' && (
        <div className="locations-group">
          <div className="form-group">
            <label>Origen</label>
            <select
              value={origen}
              onChange={(e) => onOrigenChange(e.target.value)}
              className="select-custom"
            >
              {nodos.map((n) => (
                <option key={n.id} value={n.id}>
                  {n.id} - {n.label}
                </option>
              ))}
            </select>
          </div>

          <button
            type="button"
            className="swap-btn"
            title="Invertir origen y destino"
            onClick={() => {
              const temp = origen;
              onOrigenChange(destino);
              onDestinoChange(temp);
            }}
          >
            ⇄
          </button>

          <div className="form-group">
            <label>Destino</label>
            <select
              value={destino}
              onChange={(e) => onDestinoChange(e.target.value)}
              className="select-custom"
            >
              {nodos.map((n) => (
                <option key={n.id} value={n.id}>
                  {n.id} - {n.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      {/* Selector de Contexto Urbano */}
      <div className="context-box">
        <h4 className="section-title">Condiciones de Tránsito</h4>

        {/* Hora del Día con Slider */}
        <div className="form-group">
          <div className="slider-header">
            <label>Hora del Día: <strong>{horaDia.toString().padStart(2, '0')}:00 hs</strong></label>
            <span className={`badge-horario ${tipoHora.className}`}>{tipoHora.label}</span>
          </div>
          <input
            type="range"
            min="0"
            max="23"
            value={horaDia}
            onChange={(e) => onHoraChange(parseInt(e.target.value, 10))}
            className="slider-range"
          />
          <div className="slider-ticks">
            <span>00h</span>
            <span>06h</span>
            <span>12h</span>
            <span>18h</span>
            <span>23h</span>
          </div>
        </div>

        {/* Día de la semana */}
        <div className="form-group">
          <label>Día de la Semana</label>
          <select
            value={diaSemana}
            onChange={(e) => onDiaChange(e.target.value)}
            className="select-custom"
          >
            {DIAS.map((d) => (
              <option key={d.id} value={d.id}>
                {d.label}
              </option>
            ))}
          </select>
        </div>

        {/* Clima */}
        <div className="form-group">
          <label>Clima</label>
          <div className="clima-selector">
            {CLIMAS.map((c) => (
              <button
                key={c.id}
                type="button"
                className={`clima-card ${clima === c.id ? 'selected' : ''}`}
                onClick={() => onClimaChange(c.id)}
              >
                <div className="clima-name">{c.label}</div>
                <div className="clima-desc">{c.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Feriado Checkbox */}
        <div className="form-group checkbox-group">
          <label className="checkbox-container">
            <input
              type="checkbox"
              checked={esFeriado}
              onChange={(e) => onFeriadoChange(e.target.checked)}
            />
            <span className="checkmark"></span>
            Día feriado
          </label>
        </div>
      </div>

      {/* Botón de Cálculo */}
      {modo === 'punto_a_punto' && (
        <button
          className="btn-calcular"
          onClick={onCalcular}
          disabled={loading || origen === destino}
        >
          {loading ? (
            <>
              <span className="spinner-mini"></span> Calculando Rutas...
            </>
          ) : (
            'Calcular Ruta Más Rápida'
          )}
        </button>
      )}
    </div>
  );
};
