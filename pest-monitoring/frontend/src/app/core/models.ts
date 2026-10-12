// Shapes of the data exchanged with the Django API (see backend/sightings/serializers.py).

export interface Species {
  id: number;
  common_name: string;
  scientific_name: string;
  category: 'Rodent' | 'Avian' | 'Insect' | 'Other';
  family: string;
  genus: string;
  is_invasive: boolean;
}

export interface Tag {
  id: number;
  name: string;
}

export interface Photo {
  id: number;
  media_type: 'Image';
  content_type: string;
  size_bytes: number;
  uploaded_at: string;
  url: string;
}

export type SightingStatus =
  | 'AwaitingReview'
  | 'InReview'
  | 'Confirmed'
  | 'Assigned'
  | 'ResponseScheduled'
  | 'Deployed'
  | 'Resolved'
  | 'Rejected';

export interface Sighting {
  id: number;
  reference: string;
  species: string;
  count_min: number;
  count_max: number;
  description: string;
  latitude: string;
  longitude: string;
  location_accuracy_m: number | null;
  street_or_landmark: string;
  suburb_or_postcode: string;
  observed_at: string;
  submitted_at: string;
  status: SightingStatus;
  resident_status: string;
  priority: '' | 'Low' | 'Medium' | 'High';
  rejection_reason: string;
  tags: string[];
  photos: Photo[];
  upload_token?: string;
}

/** What the report form sends to POST /api/sightings/. */
export interface SightingDraft {
  species_id: number | null;
  count: string;
  description: string;
  latitude: number | null;
  longitude: number | null;
  location_accuracy_m?: number | null;
  street_or_landmark: string;
  suburb_or_postcode: string;
  observed_at?: string | null;
  tag_ids: number[];
  reporter_confirmed: boolean;
  contact_email?: string;
}

export interface Page<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface MapFeature {
  type: 'Feature';
  geometry: { type: 'Point'; coordinates: [number, number] };
  properties: {
    id: number;
    species: string;
    family: string;
    genus: string;
    priority: 'Low' | 'Medium' | 'High';
    status: SightingStatus;
    observed_at: string;
    heat_weight: number;
  };
}

export interface FeatureCollection {
  type: 'FeatureCollection';
  features: MapFeature[];
}

export interface MapFilters {
  species_id?: number | null;
  family?: string;
  genus?: string;
  days?: number;
  bbox?: string;
}

/** Field errors returned by the API: {"errors": {"field": ["message"]}} */
export type ApiErrors = Record<string, string[]>;
