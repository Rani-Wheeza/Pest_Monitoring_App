import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LocationPicker, Pin } from './location-picker';

describe('LocationPicker', () => {
  let fixture: ComponentFixture<LocationPicker>;
  let picker: LocationPicker;
  let emitted: Pin[];

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [LocationPicker] });
    fixture = TestBed.createComponent(LocationPicker);
    picker = fixture.componentInstance;
    emitted = [];
    picker.pinMoved.subscribe((pin) => emitted.push(pin));
    fixture.detectChanges();
  });

  function type(which: 'lat' | 'lon', value: string) {
    picker.typed({ target: { value } } as unknown as Event, which);
  }

  it('shows coordinate fields when no Azure Maps key is configured', () => {
    expect(picker.mapsEnabled).toBeFalse();
    expect(fixture.nativeElement.querySelector('#lat')).not.toBeNull();
  });

  it('emits a pin once both typed coordinates are valid', () => {
    fixture.componentRef.setInput('latitude', 52.2713);
    type('lon', '-9.7026');
    expect(emitted).toEqual([{ latitude: 52.2713, longitude: -9.7026, accuracy: null }]);
  });

  it('ignores out-of-range coordinates', () => {
    fixture.componentRef.setInput('longitude', -9.7);
    type('lat', '95');
    expect(emitted).toEqual([]);
  });

  it('rounds to 6 decimal places', () => {
    picker.emit(52.123456789, -9.987654321, null);
    expect(emitted[0]).toEqual({ latitude: 52.123457, longitude: -9.987654, accuracy: null });
    expect(picker.status()).toBe('Pin placed.');
  });

  it('uses the phone location and reports its accuracy', () => {
    spyOn(navigator.geolocation, 'getCurrentPosition').and.callFake((success) =>
      success({ coords: { latitude: 52.27, longitude: -9.7, accuracy: 11.6 } } as GeolocationPosition),
    );
    picker.useMyLocation();
    expect(emitted[0]).toEqual({ latitude: 52.27, longitude: -9.7, accuracy: 12 });
    expect(picker.status()).toContain('12 metres');
  });

  it('explains when location permission is refused', () => {
    spyOn(navigator.geolocation, 'getCurrentPosition').and.callFake((_success, failure) =>
      failure?.({ code: 1 } as GeolocationPositionError),
    );
    picker.useMyLocation();
    expect(emitted).toEqual([]);
    expect(picker.status()).toContain('refused');
  });
});
