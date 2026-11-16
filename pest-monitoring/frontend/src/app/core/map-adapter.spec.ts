import { environment } from '../../environments/environment';
import { mapsConfigured } from './map-adapter';

describe('mapsConfigured', () => {
  const original = environment.mapStyleUrl;

  afterEach(() => {
    environment.mapStyleUrl = original;
  });

  it('is on when a map style URL is set', () => {
    environment.mapStyleUrl = 'https://example.test/style.json';
    expect(mapsConfigured()).toBeTrue();
  });

  it('is off when the style URL is empty', () => {
    environment.mapStyleUrl = '';
    expect(mapsConfigured()).toBeFalse();
  });
});