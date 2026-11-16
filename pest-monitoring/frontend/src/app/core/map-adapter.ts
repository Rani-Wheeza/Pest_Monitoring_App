/* eslint-disable @typescript-eslint/no-explicit-any -- the Azure Maps SDK is wrapped here (adapter) so the
   rest of the app only uses the small typed MapHandle interface below. */
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
const PRIORITY_COLOUR = ['match', ['get', 'priority'], 'High', '#d64545', 'Medium', '#e8a93a', '#4a78b0'];

export function mapsConfigured(): boolean {
  return !!environment.azureMapsKey;
}

/** Loads the Azure Maps SDK only when needed and returns a ready map. */
export async function createMap(host: HTMLElement, centre: LonLat = DEFAULT_CENTRE, zoom = 12): Promise<MapHandle> {
  const atlas: any = await import('azure-maps-control');
  const map: any = new atlas.Map(host, {
    center: centre,
    zoom,
    authOptions: { authType: atlas.AuthenticationType.subscriptionKey, subscriptionKey: environment.azureMapsKey },
  });
  await new Promise<void>((resolve) => map.events.add('ready', () => resolve()));

  const source: any = new atlas.source.DataSource(undefined, { cluster: true, clusterRadius: 45 });
  map.sources.add(source);
  const clusterLayers: any[] = [
    new atlas.layer.BubbleLayer(source, undefined, { filter: ['has', 'point_count'], radius: 18, color: '#176b4a' }),
    new atlas.layer.SymbolLayer(source, undefined, {
      filter: ['has', 'point_count'],
      iconOptions: { image: 'none' },
      textOptions: { textField: ['get', 'point_count_abbreviated'], color: '#ffffff' },
    }),
    new atlas.layer.BubbleLayer(source, undefined, { filter: ['!', ['has', 'point_count']], color: PRIORITY_COLOUR, radius: 7 }),
  ];
  const heatLayer: any = new atlas.layer.HeatMapLayer(source, undefined, { weight: ['get', 'heat_weight'], radius: 25 });
  let mode: MapMode | null = null;
  let pin: any = null;

  const handle: MapHandle = {
    showSightings(data) {
      if (mode === null) {
        handle.setMode('clusters');
      }
      source.setShapes(data);
    },
    setMode(next) {
      if (next === mode) {
        return;
      }
      if (next === 'heat') {
        clusterLayers.forEach((l) => map.layers.remove(l));
        map.layers.add(heatLayer);
      } else {
        if (mode === 'heat') {
          map.layers.remove(heatLayer);
        }
        clusterLayers.forEach((l) => map.layers.add(l));
      }
      mode = next;
    },
    addDraggablePin(position, onMove) {
      pin = new atlas.HtmlMarker({ position, draggable: true });
      map.markers.add(pin);
      map.events.add('dragend', pin, () => onMove(pin.getOptions().position as LonLat));
      map.events.add('click', (e: any) => {
        if (e.position) {
          pin.setOptions({ position: e.position });
          onMove(e.position as LonLat);
        }
      });
    },
    movePin(position) {
      pin?.setOptions({ position });
      map.setCamera({ center: position });
    },
    dispose() {
      map.dispose();
    },
  };
  return handle;
}
