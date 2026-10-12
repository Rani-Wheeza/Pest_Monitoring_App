import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { ApiService } from '../../core/api.service';
import { FeatureCollection } from '../../core/models';
import { PestMap } from './pest-map';

const DATA: FeatureCollection = {
  type: 'FeatureCollection',
  features: [{ type: 'Feature', geometry: { type: 'Point', coordinates: [-9.7, 52.27] },
    properties: { id: 1, species: 'Brown rat', family: 'Muridae', genus: 'Rattus', priority: 'High',
      status: 'Confirmed', observed_at: '2026-10-09T10:00:00Z', heat_weight: 3 } }],
};

describe('PestMap (US-04, US-05)', () => {
  it('lists sightings and builds the family filter from the species list', () => {
    const api = jasmine.createSpyObj<ApiService>('ApiService', ['getSpecies', 'mapFeatures']);
    api.getSpecies.and.returnValue(of([
      { id: 1, common_name: 'Brown rat', family: 'Muridae' },
      { id: 2, common_name: 'House mouse', family: 'Muridae' },
      { id: 3, common_name: 'Feral pigeon', family: 'Columbidae' },
    ] as never));
    api.mapFeatures.and.returnValue(of(DATA));

    TestBed.configureTestingModule({ imports: [PestMap], providers: [{ provide: ApiService, useValue: api }] });
    const fixture = TestBed.createComponent(PestMap);
    fixture.detectChanges();
    const c = fixture.componentInstance;

    expect(c.families()).toEqual(['Columbidae', 'Muridae']);
    expect(c.features().length).toBe(1);
    expect(fixture.nativeElement.textContent).toContain('1 sightings');

    c.filters.family = 'Muridae';
    c.load();
    expect(api.mapFeatures).toHaveBeenCalledWith(jasmine.objectContaining({ family: 'Muridae' }));
  });
});
