import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import { FeatureCollection, MapFilters, Page, Photo, Sighting, SightingDraft, Species, Tag } from './models';

/** All calls to the Django REST API go through this service. */
@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiUrl;

  getSpecies(): Observable<Species[]> {
    return this.http.get<Species[]>(`${this.base}/species/`);
  }

  getTags(): Observable<Tag[]> {
    return this.http.get<Tag[]>(`${this.base}/tags/`);
  }

  submitSighting(draft: SightingDraft): Observable<Sighting> {
    return this.http.post<Sighting>(`${this.base}/sightings/`, draft);
  }

  uploadPhoto(sightingId: number, file: File, uploadToken?: string): Observable<Photo> {
    const body = new FormData();
    body.append('photo', file, file.name);
    const headers = uploadToken ? new HttpHeaders({ 'X-Upload-Token': uploadToken }) : undefined;
    return this.http.post<Photo>(`${this.base}/sightings/${sightingId}/photo/`, body, { headers });
  }

  mySightings(page = 1): Observable<Page<Sighting>> {
    return this.http.get<Page<Sighting>>(`${this.base}/sightings/mine/`, {
      params: new HttpParams().set('page', page),
    });
  }

  mapFeatures(filters: MapFilters = {}): Observable<FeatureCollection> {
    let params = new HttpParams();
    for (const [key, value] of Object.entries(filters)) {
      if (value !== null && value !== undefined && value !== '') {
        params = params.set(key, String(value));
      }
    }
    return this.http.get<FeatureCollection>(`${this.base}/map/`, { params });
  }
}
