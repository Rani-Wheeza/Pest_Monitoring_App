import { AfterViewInit, Component, ElementRef, OnDestroy, input, output, signal, viewChild } from '@angular/core';

import { DEFAULT_CENTRE, LonLat, MapHandle, createMap, mapsConfigured } from '../../core/azure-maps';
import { isValidLatitude, isValidLongitude } from '../../core/report-rules';

export interface Pin {
  latitude: number;
  longitude: number;
  accuracy?: number | null;
}

/**
 * Drop a pin on the map, use the phone's location, or type coordinates (Figma 17-312).
 * The map only loads when an Azure Maps key is configured, so tests and local
 * development work without one.
 */
@Component({
  selector: 'app-location-picker',
  template: `
    @if (mapsEnabled) {
      <div #mapHost class="map map-small" role="application" aria-label="Map: click or drag to place the pin"></div>
    }
    <div class="row">
      <button type="button" (click)="useMyLocation()">Use my location</button>
      @if (status()) {
        <span class="hint" role="status">{{ status() }}</span>
      }
    </div>
    <div class="row">
      <div class="field">
        <label for="lat">Latitude</label>
        <input id="lat" type="number" step="0.000001" [value]="latitude() ?? ''" (change)="typed($event, 'lat')" />
      </div>
      <div class="field">
        <label for="lon">Longitude</label>
        <input id="lon" type="number" step="0.000001" [value]="longitude() ?? ''" (change)="typed($event, 'lon')" />
      </div>
    </div>
  `,
})
export class LocationPicker implements AfterViewInit, OnDestroy {
  readonly latitude = input<number | null>(null);
  readonly longitude = input<number | null>(null);
  readonly pinMoved = output<Pin>();

  readonly status = signal('');
  readonly mapsEnabled = mapsConfigured();
  private readonly mapHost = viewChild<ElementRef<HTMLDivElement>>('mapHost');
  private map: MapHandle | null = null;

  async ngAfterViewInit(): Promise<void> {
    const host = this.mapHost()?.nativeElement;
    if (!host) {
      return;
    }
    const lat = this.latitude();
    const lon = this.longitude();
    const start: LonLat = lat !== null && lon !== null ? [lon, lat] : DEFAULT_CENTRE;
    this.map = await createMap(host, start, 15);
    this.map.addDraggablePin(start, ([pinLon, pinLat]) => this.emit(pinLat, pinLon, null));
  }

  ngOnDestroy(): void {
    this.map?.dispose();
  }

  useMyLocation(): void {
    if (!navigator.geolocation) {
      this.status.set('Your browser cannot share its location. Drop the pin instead.');
      return;
    }
    this.status.set('Finding your location…');
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        this.map?.movePin([pos.coords.longitude, pos.coords.latitude]);
        this.emit(pos.coords.latitude, pos.coords.longitude, Math.round(pos.coords.accuracy));
      },
      () => this.status.set('Location permission was refused. Drop the pin instead.'),
      { enableHighAccuracy: true, timeout: 10000 },
    );
  }

  typed(event: Event, which: 'lat' | 'lon'): void {
    const value = Number((event.target as HTMLInputElement).value);
    const lat = which === 'lat' ? value : this.latitude();
    const lon = which === 'lon' ? value : this.longitude();
    if (isValidLatitude(lat) && isValidLongitude(lon)) {
      this.map?.movePin([lon as number, lat as number]);
      this.emit(lat as number, lon as number, null);
    }
  }

  emit(latitude: number, longitude: number, accuracy: number | null): void {
    const rounded = (n: number) => Math.round(n * 1e6) / 1e6;
    this.status.set(accuracy ? `Location accuracy is approximately ${accuracy} metres.` : 'Pin placed.');
    this.pinMoved.emit({ latitude: rounded(latitude), longitude: rounded(longitude), accuracy });
  }
}
