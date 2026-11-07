import React, { useState, useRef, useMemo } from 'react';
import { GrafoData, Nodo, ResultadoComparacion, ResultadoRonda } from '../types';

interface CityMapProps {
  grafo: GrafoData | null;
  origen: string;
  destino: string;
  onSelectNodo: (nodoId: string, tipo: 'origen' | 'destino' | 'entrega') => void;
  resultadoRuta: ResultadoComparacion | null;
  resultadoRonda: ResultadoRonda | null;
  modo: 'punto_a_punto' | 'ronda_entregas';
  puntosEntrega: string[];
  deposito: string;
}

export const CityMap: React.FC<CityMapProps> = ({
  grafo,
  origen,
  destino,
  onSelectNodo,
  resultadoRuta,
  resultadoRonda,
  modo,
  puntosEntrega,
  deposito,
}) => {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [hoveredNodo, setHoveredNodo] = useState<Nodo | null>(null);
  const [hoveredEdge, setHoveredEdge] = useState<any | null>(null);
  const [menuNodo, setMenuNodo] = useState<{ id: string; x: number; y: number } | null>(null);

  const svgRef = useRef<SVGSVGElement | null>(null);

  const MAP_WIDTH = 900;
  const MAP_HEIGHT = 650;
  const PADDING = 90;

  const { coordsMap } = useMemo(() => {
    if (!grafo || grafo.nodos.length === 0) {
      return { coordsMap: new Map<string, { x: number; y: number }>() };
    }

    let minLat = Infinity, maxLat = -Infinity;
    let minLon = Infinity, maxLon = -Infinity;

    grafo.nodos.forEach((n) => {
      if (n.lat < minLat) minLat = n.lat;
      if (n.lat > maxLat) maxLat = n.lat;
      if (n.lon < minLon) minLon = n.lon;
      if (n.lon > maxLon) maxLon = n.lon;
    });

    const latSpan = maxLat - minLat || 0.001;
    const lonSpan = maxLon - minLon || 0.001;

    const map = new Map<string, { x: number; y: number }>();
    grafo.nodos.forEach((n) => {
      const x = PADDING + ((n.lon - minLon) / lonSpan) * (MAP_WIDTH - 2 * PADDING);
      const y = PADDING + ((maxLat - n.lat) / latSpan) * (MAP_HEIGHT - 2 * PADDING);
      map.set(n.id, { x, y });
    });

    return { coordsMap: map };
  }, [grafo]);

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.target === svgRef.current || (e.target as HTMLElement).tagName === 'svg') {
      setIsDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
      setMenuNodo(null);
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const resetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setMenuNodo(null);
  };

  const construirRutaPath = (nodos: string[]): string => {
    if (!nodos || nodos.length < 2) return '';
    const points = nodos
      .map((id) => coordsMap.get(id))
      .filter((pt): pt is { x: number; y: number } => pt !== undefined);
    if (points.length < 2) return '';
    return points.reduce((acc, curr, idx) => {
      return idx === 0 ? `M ${curr.x} ${curr.y}` : `${acc} L ${curr.x} ${curr.y}`;
    }, '');
  };

  const pathRutaEstatica = useMemo(() => {
    if (modo !== 'punto_a_punto' || !resultadoRuta) return '';
    return construirRutaPath(resultadoRuta.ruta_estatica.camino_nodos);
  }, [resultadoRuta, modo, coordsMap]);

  const pathRutaDinamica = useMemo(() => {
    if (modo !== 'punto_a_punto' || !resultadoRuta) return '';
    return construirRutaPath(resultadoRuta.ruta_dinamica.camino_nodos);
  }, [resultadoRuta, modo, coordsMap]);

  const pathRonda = useMemo(() => {
    if (modo !== 'ronda_entregas' || !resultadoRonda) return '';
    return construirRutaPath(resultadoRonda.camino_completo_nodos);
  }, [resultadoRonda, modo, coordsMap]);

  const ordenEntregasMap = useMemo(() => {
    const map = new Map<string, number>();
    if (resultadoRonda && resultadoRonda.clientes_ordenados) {
      resultadoRonda.clientes_ordenados.forEach((cliente, idx) => {
        map.set(cliente, idx + 1);
      });
    }
    return map;
  }, [resultadoRonda]);

  if (!grafo) {
    return (
      <div className="map-placeholder">
        <div className="spinner"></div>
        <p>Cargando grafo de la ciudad...</p>
      </div>
    );
  }

  return (
    <div className="map-wrapper" onMouseUp={handleMouseUp} onMouseLeave={handleMouseUp}>
      {/* Controles de Zoom */}
      <div className="map-toolbar">
        <button onClick={() => setZoom((z) => Math.min(z + 0.2, 2.5))} title="Acercar">+</button>
        <button onClick={() => setZoom((z) => Math.max(z - 0.2, 0.6))} title="Alejar">-</button>
        <button onClick={resetView} title="Centrar">Reset</button>
        <span className="zoom-indicator">{Math.round(zoom * 100)}%</span>
      </div>

      {/* Leyenda */}
      <div className="map-legend">
        <div className="legend-title">Referencias</div>
        <div className="legend-items">
          <div className="legend-item">
            <span className="line-sample calle"></span> Calle barrial
          </div>
          <div className="legend-item">
            <span className="line-sample avenida"></span> Avenida
          </div>
          {modo === 'punto_a_punto' && resultadoRuta && (
            <>
              <div className="legend-item">
                <span className="line-sample estatica"></span> Ruta Estática (Distancia)
              </div>
              <div className="legend-item">
                <span className="line-sample dinamica"></span> Ruta Dinámica (Tráfico IA)
              </div>
            </>
          )}
          {modo === 'ronda_entregas' && resultadoRonda && (
            <div className="legend-item">
              <span className="line-sample ronda"></span> Ronda Nearest Neighbor
            </div>
          )}
        </div>
      </div>

      {/* Menú contextual */}
      {menuNodo && (
        <div
          className="node-context-menu"
          style={{ left: `${menuNodo.x}px`, top: `${menuNodo.y}px` }}
        >
          <div className="menu-header">Nodo {menuNodo.id}</div>
          {modo === 'punto_a_punto' ? (
            <>
              <button
                onClick={() => {
                  onSelectNodo(menuNodo.id, 'origen');
                  setMenuNodo(null);
                }}
              >
                Definir como Origen
              </button>
              <button
                onClick={() => {
                  onSelectNodo(menuNodo.id, 'destino');
                  setMenuNodo(null);
                }}
              >
                Definir como Destino
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => {
                  onSelectNodo(menuNodo.id, 'origen');
                  setMenuNodo(null);
                }}
              >
                Definir como Depósito
              </button>
              <button
                onClick={() => {
                  onSelectNodo(menuNodo.id, 'entrega');
                  setMenuNodo(null);
                }}
              >
                {puntosEntrega.includes(menuNodo.id) ? 'Quitar entrega' : 'Agregar entrega'}
              </button>
            </>
          )}
          <button className="close-btn" onClick={() => setMenuNodo(null)}>Cerrar</button>
        </div>
      )}

      {/* SVG Interactivo */}
      <svg
        ref={svgRef}
        viewBox={`0 0 ${MAP_WIDTH} ${MAP_HEIGHT}`}
        className="city-svg-map"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
      >
        <defs>
          <marker
            id="arrowhead-calle"
            markerWidth="13"
            markerHeight="13"
            refX="22"
            refY="6.5"
            orient="auto"
            markerUnits="userSpaceOnUse"
          >
            <polygon points="0 0, 11 6.5, 0 13" fill="#1e293b" />
          </marker>
          <marker
            id="arrowhead-avenida"
            markerWidth="13"
            markerHeight="13"
            refX="22"
            refY="6.5"
            orient="auto"
            markerUnits="userSpaceOnUse"
          >
            <polygon points="0 0, 11 6.5, 0 13" fill="#1e293b" />
          </marker>
        </defs>

        <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
          {/* Fondo blanco limpio */}
          <rect
            x={0}
            y={0}
            width={MAP_WIDTH}
            height={MAP_HEIGHT}
            fill="#ffffff"
            rx="8"
          />

          {/* Aristas Base (Calles y Avenidas) */}
          <g className="edges-layer">
            {grafo.aristas.map((edge) => {
              const p1 = coordsMap.get(edge.origen);
              const p2 = coordsMap.get(edge.destino);
              if (!p1 || !p2) return null;

              const isAvenida = edge.tipo === 'avenida';
              const markerId = isAvenida ? 'url(#arrowhead-avenida)' : 'url(#arrowhead-calle)';

              return (
                <g key={edge.tramo_id} className="edge-group">
                  <line
                    x1={p1.x}
                    y1={p1.y}
                    x2={p2.x}
                    y2={p2.y}
                    stroke="transparent"
                    strokeWidth="18"
                    onMouseEnter={() => setHoveredEdge(edge)}
                    onMouseLeave={() => setHoveredEdge(null)}
                    style={{ cursor: 'pointer' }}
                  />
                  <line
                    x1={p1.x}
                    y1={p1.y}
                    x2={p2.x}
                    y2={p2.y}
                    stroke={isAvenida ? '#94a3b8' : '#e2e8f0'}
                    strokeWidth={isAvenida ? '6' : '3'}
                    strokeLinecap="round"
                    markerEnd={markerId}
                  />
                  {isAvenida && (
                    <line
                      x1={p1.x}
                      y1={p1.y}
                      x2={p2.x}
                      y2={p2.y}
                      stroke="#ffffff"
                      strokeWidth="1.5"
                      strokeDasharray="5,4"
                    />
                  )}
                </g>
              );
            })}
          </g>

          {/* Ruta Estática (Naranja) */}
          {pathRutaEstatica && (
            <path
              d={pathRutaEstatica}
              fill="none"
              stroke="#ea580c"
              strokeWidth="6"
              strokeDasharray="8,5"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="route-path-static"
            />
          )}

          {/* Ruta Dinámica con IA (Verde) */}
          {pathRutaDinamica && (
            <path
              d={pathRutaDinamica}
              fill="none"
              stroke="#059669"
              strokeWidth="6"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="route-path-dynamic"
            />
          )}

          {/* Ronda de Entregas (Violeta) */}
          {pathRonda && (
            <path
              d={pathRonda}
              fill="none"
              stroke="#7c3aed"
              strokeWidth="5"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeDasharray="6,3"
              className="route-path-ronda"
            />
          )}

          {/* Nodos (Esquinas) */}
          <g className="nodes-layer">
            {grafo.nodos.map((nodo) => {
              const pt = coordsMap.get(nodo.id);
              if (!pt) return null;

              const isOrigen = nodo.id === origen || (modo === 'ronda_entregas' && nodo.id === deposito);
              const isDestino = nodo.id === destino && modo === 'punto_a_punto';
              const ordenEntrega = modo === 'ronda_entregas' ? ordenEntregasMap.get(nodo.id) : undefined;
              const isPuntoEntrega = modo === 'ronda_entregas' && puntosEntrega.includes(nodo.id);

              let nodeFill = '#ffffff';
              let nodeStroke = '#94a3b8';
              let nodeRadius = 14;

              if (isOrigen) {
                nodeFill = '#2563eb';
                nodeStroke = '#1d4ed8';
                nodeRadius = 16;
              } else if (isDestino) {
                nodeFill = '#dc2626';
                nodeStroke = '#b91c1c';
                nodeRadius = 16;
              } else if (ordenEntrega !== undefined) {
                nodeFill = '#7c3aed';
                nodeStroke = '#6d28d9';
                nodeRadius = 16;
              } else if (isPuntoEntrega) {
                nodeFill = '#c084fc';
                nodeStroke = '#7c3aed';
                nodeRadius = 15;
              }

              const textColor = isOrigen || isDestino || ordenEntrega !== undefined ? '#ffffff' : '#475569';

              return (
                <g
                  key={nodo.id}
                  className="node-group"
                  transform={`translate(${pt.x}, ${pt.y})`}
                  onClick={(e) => {
                    const rect = svgRef.current?.getBoundingClientRect();
                    if (rect) {
                      setMenuNodo({
                        id: nodo.id,
                        x: e.clientX - rect.left,
                        y: e.clientY - rect.top,
                      });
                    }
                  }}
                  onMouseEnter={() => setHoveredNodo(nodo)}
                  onMouseLeave={() => setHoveredNodo(null)}
                  style={{ cursor: 'pointer' }}
                >
                  <circle
                    r={nodeRadius}
                    fill={nodeFill}
                    stroke={nodeStroke}
                    strokeWidth="2"
                  />

                  {ordenEntrega !== undefined ? (
                    <text
                      textAnchor="middle"
                      dy="4"
                      fill={textColor}
                      fontSize="12"
                      fontWeight="700"
                    >
                      {ordenEntrega}
                    </text>
                  ) : isOrigen ? (
                    <text
                      textAnchor="middle"
                      dy="4"
                      fill={textColor}
                      fontSize="11"
                      fontWeight="700"
                    >
                      {modo === 'ronda_entregas' ? 'D' : 'A'}
                    </text>
                  ) : isDestino ? (
                    <text
                      textAnchor="middle"
                      dy="4"
                      fill={textColor}
                      fontSize="11"
                      fontWeight="700"
                    >
                      B
                    </text>
                  ) : (
                    <text
                      textAnchor="middle"
                      dy="3.5"
                      fill={textColor}
                      fontSize="8"
                      fontWeight="600"
                    >
                      {nodo.id.replace('N_', '')}
                    </text>
                  )}

                  <text
                    y={nodeRadius + 12}
                    textAnchor="middle"
                    fill="#64748b"
                    fontSize="9.5"
                    fontWeight="500"
                    className="node-label"
                  >
                    {nodo.id}
                  </text>
                </g>
              );
            })}
          </g>
        </g>
      </svg>

      {hoveredNodo && (
        <div className="map-tooltip">
          <strong>{hoveredNodo.label}</strong> ({hoveredNodo.id})<br />
          <span>Lat: {hoveredNodo.lat.toFixed(4)}, Lon: {hoveredNodo.lon.toFixed(4)}</span>
        </div>
      )}

      {hoveredEdge && (
        <div className="map-tooltip">
          <strong>Tramo {hoveredEdge.tramo_id}</strong> ({hoveredEdge.tipo})<br />
          <span>{hoveredEdge.origen} ➔ {hoveredEdge.destino}</span><br />
          <span>Distancia: {hoveredEdge.distancia_metros}m | Vel: {hoveredEdge.velocidad_base_kmh} km/h</span>
        </div>
      )}
    </div>
  );
};
