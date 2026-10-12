import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { ApiService } from './api.service';
import { SightingDraft } from './models';

describe('ApiService', () => {
  let api: ApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    api = TestBed.inject(ApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('loads the species list', () => {
    api.getSpecies().subscribe((list) => expect(list.length).toBe(1));
    http.expectOne('/api/species/').flush([{ id: 1, common_name: 'Brown rat' }]);
  });

  it('posts a sighting', () => {
    const draft = { species_id: 1, count: '2-5' } as SightingDraft;
    api.submitSighting(draft).subscribe();
    const req = http.expectOne('/api/sightings/');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(draft);
    req.flush({ id: 7 });
  });

  it('uploads a photo with the anonymous upload token', () => {
    const file = new File(['x'], 'p.png', { type: 'image/png' });
    api.uploadPhoto(7, file, 'token-123').subscribe();
    const req = http.expectOne('/api/sightings/7/photo/');
    expect(req.request.headers.get('X-Upload-Token')).toBe('token-123');
    expect(req.request.body instanceof FormData).toBeTrue();
    req.flush({ id: 1 });
  });

  it('uploads a photo without a token when signed in', () => {
    api.uploadPhoto(7, new File(['x'], 'p.png', { type: 'image/png' })).subscribe();
    const req = http.expectOne('/api/sightings/7/photo/');
    expect(req.request.headers.has('X-Upload-Token')).toBeFalse();
    req.flush({ id: 1 });
  });

  it('sends only the map filters that are set', () => {
    api.mapFeatures({ species_id: null, family: 'Muridae', days: 30, genus: '' }).subscribe();
    const req = http.expectOne((r) => r.url === '/api/map/');
    expect(req.request.params.keys().sort()).toEqual(['days', 'family']);
    req.flush({ type: 'FeatureCollection', features: [] });
  });

  it('asks for a page of my sightings', () => {
    api.mySightings(2).subscribe();
    const req = http.expectOne((r) => r.url === '/api/sightings/mine/');
    expect(req.request.params.get('page')).toBe('2');
    req.flush({ count: 0, next: null, previous: null, results: [] });
  });
});
