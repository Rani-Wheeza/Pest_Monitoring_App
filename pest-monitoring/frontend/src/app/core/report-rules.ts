// Client-side checks for the report form. They match the server rules in
// backend/domain/validation.py and backend/domain/images.py, so users get the
// same message before they submit. The server still checks everything.
// Plain TypeScript: no Angular imports, so these are simple to unit test.

export const MAX_PHOTO_BYTES = 10 * 1024 * 1024;
export const ALLOWED_PHOTO_TYPES = ['image/jpeg', 'image/png'];
export const COUNT_OPTIONS = ['1', '2-5', '6-10', '11-20', '20+'];

/** Returns an error message, or null if the photo is acceptable. */
export function checkPhoto(file: { type: string; size: number } | null): string | null {
  if (!file) {
    return null; // a photo is optional
  }
  if (!ALLOWED_PHOTO_TYPES.includes(file.type)) {
    return 'Only JPG and PNG photos are accepted.';
  }
  if (file.size > MAX_PHOTO_BYTES) {
    return 'Photos must be 10 MB or smaller.';
  }
  return null;
}

export function isValidLatitude(value: number | null | undefined): boolean {
  return typeof value === 'number' && !Number.isNaN(value) && value >= -90 && value <= 90;
}

export function isValidLongitude(value: number | null | undefined): boolean {
  return typeof value === 'number' && !Number.isNaN(value) && value >= -180 && value <= 180;
}

/** Turns API field errors into one readable line per field. */
export function errorLines(errors: Record<string, string[]> | null | undefined): string[] {
  if (!errors) {
    return [];
  }
  return Object.entries(errors).map(([field, messages]) => `${labelFor(field)}: ${messages.join(' ')}`);
}

const LABELS: Record<string, string> = {
  species_id: 'Pest',
  count: 'How many',
  description: 'Description',
  location: 'Location',
  latitude: 'Location',
  longitude: 'Location',
  street_or_landmark: 'Street or landmark',
  suburb_or_postcode: 'Suburb or postcode',
  observed_at: 'Time',
  reporter_confirmed: 'Confirmation',
  contact_email: 'Contact email',
  photo: 'Photo',
};

export function labelFor(field: string): string {
  return LABELS[field] ?? field;
}

/** Colour class for a status badge (Task 6: colour plus text, never colour alone). */
export function badgeClass(residentStatus: string): string {
  switch (residentStatus) {
    case 'Awaiting review':
      return 'badge badge-waiting';
    case 'Response scheduled':
      return 'badge badge-scheduled';
    case 'Resolved':
      return 'badge badge-resolved';
    default:
      return 'badge';
  }
}
