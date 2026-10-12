import { DatePipe } from '@angular/common';
import { AfterViewInit, Component, ElementRef, OnDestroy, OnInit, inject, signal, viewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ApiService } from '../../core/api.service';
import { MapHandle, MapMode, createMap, mapsConfigured } from '../../core/azure-maps';
import { FeatureCollection, MapFeature, MapFilters, Species } from '../../core/models';

/**
 * Pest activity map with species / family filters (Task 6.4, US-04, US-05).
 * Shows clusters or a heat map with Azure Maps, and always a list of the same
 * sightings for users who find the map hard to read.
 */
@Component({
  selector: 'app-pest-map',
  imports: [FormsModule, DatePipe],
  template: `
    <section class="page">
      <h1>Pest activity map</h1>
      <form class="filters" (ngSubmit)="load()">
        <div class="field">
          <label for="f-species">Species</label>
          <select id="f-species" name="species" [(ngModel)]="filters.species_id">
            <option [ngValue]="null">All species</option>
            @for (s of species(); track s.id) {
              <option [ngValue]="s.id">{{ s.common_name }}</option>
            }
          </select>
        </div>
        <div class="field">
          <label for="f-family">Family</label>
          <select id="f-family" name="family" [(ngModel)]="filters.family">
            <option value="">All families</option>
            @for (f of families(); track f) {
              <option [value]="f">{{ f }}</option>
            }
          </select>
        </div>
        <div class="field">
          <label for="f-days">Period</label>
          <select id="f-days" name="days" [(ngModel)]="filters.days">
            <option [ngValue]="7">Last 7 days</option>
            <option [ngValue]="30">Last 30 days</option>
            <option [ngValue]="90">Last 90 days</option>
          </select>
        </div>
        <button type="submit" class="primary">Apply</button>
        @if (mapsEnabled) {
          <button type="button" (click)="toggleMode()">{{ mode() === 'heat' ? 'Show clusters' : 'Show heat map' }}</button>
        }
      </form>

      <div class="map-layout">
        @if (mapsEnabled) {
          <div #mapHost class="map" role="img" aria-label="Map of pest sightings"></div>
        }
        <div class="card list">
          <h2>{{ features().length }} sightings</h2>
          <p class="legend">
            <span class="dot high"></span> High <span class="dot medium"></span> Medium <span class="dot low"></span> Low
          </p>
          @for (f of features(); track f.properties.id) {
            <div class="list-row">
              <span [class]="'dot ' + f.properties.priority.toLowerCase()"></span>
              <strong>{{ f.properties.species }}</strong>
              <span class="badge">{{ f.properties.priority }}</span>
              <span class="hint">{{ f.properties.observed_at | date: 'd MMM' }}</span>
            </div>
          } @empty {
            <p class="hint">No sightings match these filters.</p>
          }
        </div>
      </div>
    </section>
  `,
})
export class PestMap implements OnInit, AfterViewInit, OnDestroy {
  private readonly api = inject(ApiService);
  private readonly mapHost = viewChild<ElementRef<HTMLDivElement>>('mapHost');
  private map: MapHandle | null = null;
  private lastData: FeatureCollection = { type: 'FeatureCollection', features: [] };

  readonly mapsEnabled = mapsConfigured();
  readonly species = signal<Species[]>([]);
  readonly families = signal<string[]>([]);
  readonly features = signal<MapFeature[]>([]);
  readonly mode = signal<MapMode>('clusters');
  filters: MapFilters = { species_id: null, family: '', days: 30 };

  ngOnInit(): void {
    this.api.getSpecies().subscribe((list) => {
      this.species.set(list);
      this.families.set([...new Set(list.map((s) => s.family).filter((f) => !!f))].sort());
    });
    this.load();
  }

  async ngAfterViewInit(): Promise<void> {
    const host = this.mapHost()?.nativeElement;
    if (!host) {
      return;
    }
    this.map = await createMap(host);
    this.map.showSightings(this.lastData);
  }

  ngOnDestroy(): void {
    this.map?.dispose();
  }

  load(): void {
    this.api.mapFeatures(this.filters).subscribe((data) => {
      this.lastData = data;
      this.features.set(data.features);
      this.map?.showSightings(data);
    });
  }

  toggleMode(): void {
    const next: MapMode = this.mode() === 'clusters' ? 'heat' : 'clusters';
    this.map?.setMode(next);
    this.mode.set(next);
  }
}
