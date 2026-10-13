import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';

import { ApiService } from '../../core/api.service';
import { Sighting } from '../../core/models';
import { ReportSighting } from './report-sighting';

const SAVED = { id: 7, reference: 'PP-7', resident_status: 'Awaiting review' } as Sighting;

describe('ReportSighting (US-02, US-03)', () => {
  let fixture: ComponentFixture<ReportSighting>;
  let component: ReportSighting;
  let api: jasmine.SpyObj<ApiService>;

  beforeEach(async () => {
    api = jasmine.createSpyObj<ApiService>('ApiService', ['getSpecies', 'getTags', 'submitSighting', 'uploadPhoto']);
    api.getSpecies.and.returnValue(of([{ id: 1, common_name: 'Brown rat', scientific_name: '', category: 'Rodent',
      family: 'Muridae', genus: 'Rattus', is_invasive: false }]));
    api.getTags.and.returnValue(of([{ id: 3, name: 'Near food' }]));
    api.submitSighting.and.returnValue(of(SAVED));

    await TestBed.configureTestingModule({
      imports: [ReportSighting],
      providers: [provideRouter([]), { provide: ApiService, useValue: api }],
    }).compileComponents();
    fixture = TestBed.createComponent(ReportSighting);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  function fillDetails() {
    component.details.patchValue({ species_id: 1, count: '2-5', description: 'Rats by the bins' });
  }

  function fillLocation() {
    component.onPinMoved({ latitude: 52.2713, longitude: -9.7026, accuracy: 12 });
    component.location.patchValue({ street_or_landmark: 'Community centre', suburb_or_postcode: 'Riverside' });
  }

  it('starts on step 1 and loads species and tags', () => {
    expect(component.step()).toBe(1);
    expect(component.species().length).toBe(1);
    expect(component.tags().length).toBe(1);
  });

  it('will not leave step 1 until required details are filled in', () => {
    component.next();
    expect(component.step()).toBe(1);
    fillDetails();
    component.next();
    expect(component.step()).toBe(2);
  });

  it('will not leave step 2 without a location', () => {
    fillDetails();
    component.next();
    component.next();
    expect(component.step()).toBe(2);
    fillLocation();
    component.next();
    expect(component.step()).toBe(3);
  });

  it('back and edit move between steps', () => {
    fillDetails();
    fillLocation();
    component.step.set(3);
    component.back();
    expect(component.step()).toBe(2);
    component.edit(1);
    expect(component.step()).toBe(1);
  });

  it('toggles tags on and off', () => {
    component.toggleTag(3);
    expect(component.isTagSelected(3)).toBeTrue();
    expect(component.tagNames()).toBe('Near food');
    component.toggleTag(3);
    expect(component.isTagSelected(3)).toBeFalse();
  });

  it('shows the species name on the review step', () => {
    fillDetails();
    expect(component.speciesName()).toBe('Brown rat');
  });

  it('needs the accuracy confirmation before submitting', () => {
    fillDetails();
    fillLocation();
    component.submit();
    expect(api.submitSighting).not.toHaveBeenCalled();
  });

  it('submits the draft and shows the reference number', () => {
    fillDetails();
    fillLocation();
    component.confirmed.setValue(true);
    component.submit();

    const draft = api.submitSighting.calls.mostRecent().args[0];
    expect(draft.species_id).toBe(1);
    expect(draft.count).toBe('2-5');
    expect(draft.latitude).toBe(52.2713);
    expect(draft.location_accuracy_m).toBe(12);
    expect(draft.reporter_confirmed).toBeTrue();
    expect(component.step()).toBe('done');
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('PP-7');
  });

  it('uploads the photo after the report is saved, using the upload token', () => {
    api.submitSighting.and.returnValue(of({ ...SAVED, upload_token: 'tok' }));
    api.uploadPhoto.and.returnValue(
      of({
        id: 1,
        media_type: 'Image',
        content_type: 'image/png',
        size_bytes: 1,
        uploaded_at: '2026-10-13T08:00:00Z',
        url: '/media/rat.png',
    }),
  );

    
    const file = new File(['x'], 'rat.png', { type: 'image/png' });
    component.onPhotoSelected({ target: { files: [file] } } as unknown as Event);
    fillDetails();
    fillLocation();
    component.confirmed.setValue(true);
    component.submit();
    expect(api.uploadPhoto).toHaveBeenCalledWith(7, file, 'tok');
  });

  it('refuses a GIF before upload', () => {
    const gif = new File(['x'], 'a.gif', { type: 'image/gif' });
    component.onPhotoSelected({ target: { files: [gif] } } as unknown as Event);
    expect(component.photo()).toBeNull();
    expect(component.photoError()).toContain('Only JPG and PNG');
  });

  it('shows server validation errors', () => {
    api.submitSighting.and.returnValue(throwError(() => ({ status: 400, error: { errors: { contact_email: ['Needed.'] } } })));
    fillDetails();
    fillLocation();
    component.confirmed.setValue(true);
    component.submit();
    expect(component.step()).toBe(3);
    expect(component.serverErrors()).toEqual(['Contact email: Needed.']);
    expect(component.submitting()).toBeFalse();
  });

  it('start again resets the form', () => {
    fillDetails();
    component.step.set('done');
    component.startAgain();
    expect(component.step()).toBe(1);
    expect(component.details.controls.description.value).toBe('');
  });
});
