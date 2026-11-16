/* Wraps MapLibre GL JS behind the small MapHandle interface (adapter pattern), so the
   components never touch the map library and the provider can be swapped in this one file. */
import type { ExpressionSpecification, GeoJSONSource, Map as MapLibreMap, Marker } from 'maplibre-gl';

import { environment } from '../../environments/environment';
import { FeatureCollection } from './models';

export type LonLat = [number, number];
export type MapMode = 'clusters' | 'heat';

/** Everything the components need from a map. */
export interface MapHandle {
  showSightings(data: FeatureCollection): void;
  setMode(mode: MapMode): void;
  addDraggablePin(position: LonLat, onMove: (position: LonLat) => void): void;
  movePin(position: LonLat): void;
  dispose(): void;
}

export const DEFAULT_CENTRE: LonLat = [-9.7026, 52.2713]; // Tralee

// Point colour by priority: High = red, Medium = amber, anything else = blue
const PRIORITY_COLOUR: ExpressionSpecification = [
  'match', ['get', 'priority'], 'High', '#d64545', 'Medium', '#e8a93a', '#4a78b0',
];
const CLUSTER_LAYERS = ['clusters', 'cluster-count', 'points'];

// Our FeatureCollection model is GeoJSON, but typed for our API, so convert it to the type MapLibre expects
type MapData = Parameters<GeoJSONSource['setData']>[0];
const toMapData = (data: FeatureCollection) => data as unknown as MapData;
const EMPTY = toMapData({ type: 'FeatureCollection', features: [] });

export function mapsConfigured(): boolean {
  return !!environment.mapStyleUrl;
}

/** Loads MapLibre only when a map is actually shown, and returns a ready map. */
export async function createMap(host: HTMLElement, centre: LonLat = DEFAULT_CENTRE, zoom = 12): Promise<MapHandle> {
  // MapLibre ships as a UMD bundle, so the API can end up on the module itself or on .default
  const mod = await import('maplibre-gl');
  const maplibregl = (mod as unknown as { default?: typeof mod }).default ?? mod;
  // Angular's bundler can't find MapLibre's worker by itself, so point it at the copy angular.json puts in the site root
  maplibregl.setWorkerUrl(new URL('maplibre-gl-worker.mjs', document.baseURI).href);
  
  const map: MapLibreMap = new maplibregl.Map({ container: host, style: environment.mapStyleUrl, center: centre, zoom });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
  await new Promise<void>((resolve) => map.once('load', () => resolve()));

  // Two copies of the data: clustered for the cluster view, raw points for the heat map
  map.addSource('sightings', { type: 'geojson', data: EMPTY, cluster: true, clusterRadius: 45 });
  map.addSource('sightings-heat', { type: 'geojson', data: EMPTY });

  // Cluster view: green bubble with a count, single sightings coloured by priority
  map.addLayer({
    id: 'clusters', type: 'circle', source: 'sightings', filter: ['has', 'point_count'],
    paint: { 'circle-color': '#176b4a', 'circle-radius': 18 },
  });
  map.addLayer({
    id: 'cluster-count', type: 'symbol', source: 'sightings', filter: ['has', 'point_count'],
    layout: { 'text-field': ['get', 'point_count_abbreviated'], 'text-font': ['Noto Sans Bold'], 'text-size': 12 },
    paint: { 'text-color': '#ffffff' },
  });
  map.addLayer({
    id: 'points', type: 'circle', source: 'sightings', filter: ['!', ['has', 'point_count']],
    paint: { 'circle-color': PRIORITY_COLOUR, 'circle-radius': 7, 'circle-stroke-color': '#ffffff', 'circle-stroke-width': 1 },
  });

  // Heat map view, hidden until the user switches to it
  map.addLayer({
    id: 'heat', type: 'heatmap', source: 'sightings-heat', layout: { visibility: 'none' },
    paint: { 'heatmap-weight': ['get', 'heat_weight'], 'heatmap-radius': 25 },
  });

  const show = (layerId: string, visible: boolean) =>
    map.setLayoutProperty(layerId, 'visibility', visible ? 'visible' : 'none');

  let mode: MapMode = 'clusters';
  let pin: Marker | null = null;

  const handle: MapHandle = {
    showSightings(data) {
      (map.getSource('sightings') as GeoJSONSource).setData(toMapData(data));
      (map.getSource('sightings-heat') as GeoJSONSource).setData(toMapData(data));
    },
    setMode(next) {
      if (next === mode) {
        return;
      }
      CLUSTER_LAYERS.forEach((layerId) => show(layerId, next === 'clusters'));
      show('heat', next === 'heat');
      mode = next;
    },
    addDraggablePin(position, onMove) {
      const marker = new maplibregl.Marker({ draggable: true, color: '#176b4a' }).setLngLat(position).addTo(map);
      marker.on('dragend', () => {
        const { lng, lat } = marker.getLngLat();
        onMove([lng, lat]);
      });
      // Clicking anywhere on the map moves the pin there too
      map.on('click', (e) => {
        marker.setLngLat(e.lngLat);
        onMove([e.lngLat.lng, e.lngLat.lat]);
      });
      pin = marker;
    },
    movePin(position) {
      pin?.setLngLat(position);
      map.easeTo({ center: position });
    },
    dispose() {
      map.remove();
    },
  };
  return handle;
}