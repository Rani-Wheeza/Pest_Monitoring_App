import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { finalize, of, switchMap } from 'rxjs';

import { ApiService } from '../../core/api.service';
import { ApiErrors, Sighting, SightingDraft, Species, Tag } from '../../core/models';
import { COUNT_OPTIONS, checkPhoto, errorLines } from '../../core/report-rules';
import { LocationPicker } from './location-picker';

type Step = 1 | 2 | 3 | 'done';

/**
 * Report a pest sighting in three steps: Details -> Location -> Review (Task 6.3, US-02, US-03).
 * Wireframes: Figma frames 14-3, 17-312, 17-379 and 14-80.
 */
@Component({
  selector: 'app-report-sighting',
  imports: [ReactiveFormsModule, RouterLink, LocationPicker],
  templateUrl: './report-sighting.html',
})
export class ReportSighting implements OnInit {
  private readonly api = inject(ApiService);
  private readonly fb = inject(FormBuilder);

  readonly countOptions = COUNT_OPTIONS;
  readonly species = signal<Species[]>([]);
  readonly tags = signal<Tag[]>([]);
  readonly step = signal<Step>(1);
  readonly submitting = signal(false);
  readonly serverErrors = signal<string[]>([]);
  readonly photoError = signal<string | null>(null);
  readonly result = signal<Sighting | null>(null);
  readonly photo = signal<File | null>(null);

  readonly details = this.fb.group({
    species_id: this.fb.control<number | null>(null, Validators.required),
    count: this.fb.nonNullable.control('', Validators.required),
    description: this.fb.nonNullable.control('', [Validators.required, Validators.maxLength(1000)]),
    tag_ids: this.fb.nonNullable.control<number[]>([]),
    contact_email: this.fb.nonNullable.control('', Validators.email),
  });

  readonly location = this.fb.group({
    latitude: this.fb.control<number | null>(null, [Validators.required, Validators.min(-90), Validators.max(90)]),
    longitude: this.fb.control<number | null>(null, [Validators.required, Validators.min(-180), Validators.max(180)]),
    location_accuracy_m: this.fb.control<number | null>(null),
    street_or_landmark: this.fb.nonNullable.control('', [Validators.required, Validators.maxLength(200)]),
    suburb_or_postcode: this.fb.nonNullable.control('', [Validators.required, Validators.maxLength(100)]),
  });

  readonly confirmed = this.fb.nonNullable.control(false, Validators.requiredTrue);

  ngOnInit(): void {
    this.api.getSpecies().subscribe((list) => this.species.set(list));
    this.api.getTags().subscribe((list) => this.tags.set(list));
  }

  speciesName(): string {
    const id = Number(this.details.controls.species_id.value);
    return this.species().find((s) => s.id === id)?.common_name ?? '';
  }

  tagNames(): string {
    return this.tags()
      .filter((t) => this.isTagSelected(t.id))
      .map((t) => t.name)
      .join(' · ');
  }

  isTagSelected(id: number): boolean {
    return this.details.controls.tag_ids.value.includes(id);
  }

  toggleTag(id: number): void {
    const current = this.details.controls.tag_ids.value;
    this.details.controls.tag_ids.setValue(current.includes(id) ? current.filter((t) => t !== id) : [...current, id]);
  }

  onPhotoSelected(event: Event): void {
    const file = (event.target as HTMLInputElement).files?.[0] ?? null;
    const error = checkPhoto(file);
    this.photoError.set(error);
    this.photo.set(error ? null : file);
  }

  onPinMoved(pin: { latitude: number; longitude: number; accuracy?: number | null }): void {
    this.location.patchValue({
      latitude: pin.latitude,
      longitude: pin.longitude,
      location_accuracy_m: pin.accuracy ?? null,
    });
  }

  next(): void {
    const form = this.step() === 1 ? this.details : this.location;
    if (form.invalid) {
      form.markAllAsTouched();
      return;
    }
    this.step.set(this.step() === 1 ? 2 : 3);
  }

  back(): void {
    this.step.set(this.step() === 3 ? 2 : 1);
  }

  edit(step: 1 | 2): void {
    this.step.set(step);
  }

  buildDraft(): SightingDraft {
    const d = this.details.getRawValue();
    const l = this.location.getRawValue();
    return {
      species_id: d.species_id,
      count: d.count,
      description: d.description,
      tag_ids: d.tag_ids,
      contact_email: d.contact_email || undefined,
      latitude: l.latitude,
      longitude: l.longitude,
      location_accuracy_m: l.location_accuracy_m,
      street_or_landmark: l.street_or_landmark,
      suburb_or_postcode: l.suburb_or_postcode,
      observed_at: new Date().toISOString(),
      reporter_confirmed: this.confirmed.value,
    };
  }

  submit(): void {
    if (this.confirmed.invalid) {
      this.confirmed.markAsTouched();
      return;
    }
    this.submitting.set(true);
    this.serverErrors.set([]);
    const photo = this.photo();

    this.api
      .submitSighting(this.buildDraft())
      .pipe(
        switchMap((sighting) => {
          this.result.set(sighting);
          return photo ? this.api.uploadPhoto(sighting.id, photo, sighting.upload_token) : of(null);
        }),
        finalize(() => this.submitting.set(false)),
      )
      .subscribe({
        next: () => this.step.set('done'),
        error: (err: HttpErrorResponse) => this.showErrors(err),
      });
  }

  startAgain(): void {
    this.details.reset({ species_id: null, count: '', description: '', tag_ids: [], contact_email: '' });
    this.location.reset();
    this.confirmed.reset(false);
    this.photo.set(null);
    this.result.set(null);
    this.step.set(1);
  }

  private showErrors(err: HttpErrorResponse): void {
    if (this.result()) {
      // The report was saved but the photo failed: still show the confirmation.
      this.step.set('done');
      this.photoError.set(errorLines(err.error?.errors as ApiErrors).join(' ') || 'The photo could not be uploaded.');
      return;
    }
    const lines = errorLines(err.error?.errors as ApiErrors);
    this.serverErrors.set(lines.length ? lines : ['Something went wrong. Please try again.']);
  }
}
