import { MAX_PHOTO_BYTES, badgeClass, checkPhoto, errorLines, isValidLatitude, isValidLongitude, labelFor } from './report-rules';

describe('report rules', () => {
  describe('checkPhoto', () => {
    it('allows no photo, because it is optional', () => {
      expect(checkPhoto(null)).toBeNull();
    });
    it('accepts JPG and PNG', () => {
      expect(checkPhoto({ type: 'image/jpeg', size: 1000 })).toBeNull();
      expect(checkPhoto({ type: 'image/png', size: 1000 })).toBeNull();
    });
    it('rejects other types, including video and audio', () => {
      expect(checkPhoto({ type: 'image/gif', size: 1000 })).toContain('Only JPG and PNG');
      expect(checkPhoto({ type: 'video/mp4', size: 1000 })).toContain('Only JPG and PNG');
      expect(checkPhoto({ type: 'audio/mpeg', size: 1000 })).toContain('Only JPG and PNG');
    });
    it('rejects photos over 10 MB', () => {
      expect(checkPhoto({ type: 'image/png', size: MAX_PHOTO_BYTES + 1 })).toContain('10 MB');
      expect(checkPhoto({ type: 'image/png', size: MAX_PHOTO_BYTES })).toBeNull();
    });
  });

  it('checks coordinate ranges', () => {
    expect(isValidLatitude(52.27)).toBeTrue();
    expect(isValidLatitude(91)).toBeFalse();
    expect(isValidLatitude(null)).toBeFalse();
    expect(isValidLongitude(-9.7)).toBeTrue();
    expect(isValidLongitude(-181)).toBeFalse();
    expect(isValidLongitude(Number.NaN)).toBeFalse();
  });

  it('turns API errors into readable lines', () => {
    expect(errorLines({ species_id: ['Choose the pest you saw.'], photo: ['Too big.', 'Wrong type.'] })).toEqual([
      'Pest: Choose the pest you saw.',
      'Photo: Too big. Wrong type.',
    ]);
    expect(errorLines(null)).toEqual([]);
    expect(labelFor('unknown_field')).toBe('unknown_field');
  });

  it('gives each resident status its own badge', () => {
    expect(badgeClass('Awaiting review')).toContain('badge-waiting');
    expect(badgeClass('Response scheduled')).toContain('badge-scheduled');
    expect(badgeClass('Resolved')).toContain('badge-resolved');
    expect(badgeClass('Not accepted')).toBe('badge');
  });
});
