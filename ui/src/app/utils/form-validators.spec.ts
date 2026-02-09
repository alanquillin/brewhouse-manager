import { FormControl, FormGroup } from '@angular/forms';
import { Validation } from './form-validators';

describe('Validation', () => {
  describe('match', () => {
    let formGroup: FormGroup;

    beforeEach(() => {
      formGroup = new FormGroup({
        password: new FormControl(''),
        confirmPassword: new FormControl(''),
      });
    });

    it('should return null when both fields match', () => {
      formGroup.patchValue({
        password: 'testPassword123',
        confirmPassword: 'testPassword123',
      });

      const validator = Validation.match('password', 'confirmPassword');
      const result = validator(formGroup);

      expect(result).toBeNull();
    });

    it('should return matching error when fields do not match', () => {
      formGroup.patchValue({
        password: 'testPassword123',
        confirmPassword: 'differentPassword',
      });

      const validator = Validation.match('password', 'confirmPassword');
      const result = validator(formGroup);

      expect(result).toEqual({ matching: true });
    });

    it('should set matching error on the check control when values differ', () => {
      formGroup.patchValue({
        password: 'testPassword123',
        confirmPassword: 'differentPassword',
      });

      const validator = Validation.match('password', 'confirmPassword');
      validator(formGroup);

      const confirmPasswordErrors = formGroup.get('confirmPassword')?.errors;
      expect(confirmPasswordErrors).toEqual({ matching: true });
    });

    it('should return null when both fields are empty', () => {
      formGroup.patchValue({
        password: '',
        confirmPassword: '',
      });

      const validator = Validation.match('password', 'confirmPassword');
      const result = validator(formGroup);

      expect(result).toBeNull();
    });

    it('should return matching error when one field is empty and the other is not', () => {
      formGroup.patchValue({
        password: 'testPassword123',
        confirmPassword: '',
      });

      const validator = Validation.match('password', 'confirmPassword');
      const result = validator(formGroup);

      expect(result).toEqual({ matching: true });
    });

    it('should return null if checkControl already has other errors', () => {
      formGroup.patchValue({
        password: 'testPassword123',
        confirmPassword: 'differentPassword',
      });

      // Set another error on the check control
      formGroup.get('confirmPassword')?.setErrors({ required: true });

      const validator = Validation.match('password', 'confirmPassword');
      const result = validator(formGroup);

      expect(result).toBeNull();
    });

    it('should work with different control names', () => {
      const customFormGroup = new FormGroup({
        email: new FormControl('test@example.com'),
        confirmEmail: new FormControl('test@example.com'),
      });

      const validator = Validation.match('email', 'confirmEmail');
      const result = validator(customFormGroup);

      expect(result).toBeNull();
    });

    it('should handle case-sensitive comparison', () => {
      formGroup.patchValue({
        password: 'TestPassword',
        confirmPassword: 'testpassword',
      });

      const validator = Validation.match('password', 'confirmPassword');
      const result = validator(formGroup);

      expect(result).toEqual({ matching: true });
    });

    it('should handle whitespace differences', () => {
      formGroup.patchValue({
        password: 'testPassword',
        confirmPassword: 'testPassword ',
      });

      const validator = Validation.match('password', 'confirmPassword');
      const result = validator(formGroup);

      expect(result).toEqual({ matching: true });
    });

    it('should handle special characters', () => {
      formGroup.patchValue({
        password: 'test@Password#123!',
        confirmPassword: 'test@Password#123!',
      });

      const validator = Validation.match('password', 'confirmPassword');
      const result = validator(formGroup);

      expect(result).toBeNull();
    });

    it('should handle unicode characters', () => {
      formGroup.patchValue({
        password: 'пароль🔐',
        confirmPassword: 'пароль🔐',
      });

      const validator = Validation.match('password', 'confirmPassword');
      const result = validator(formGroup);

      expect(result).toBeNull();
    });

    it('should clear matching error when values become equal', () => {
      // First, create a mismatch
      formGroup.patchValue({
        password: 'testPassword123',
        confirmPassword: 'differentPassword',
      });

      const validator = Validation.match('password', 'confirmPassword');
      validator(formGroup);

      // Verify error was set
      expect(formGroup.get('confirmPassword')?.errors).toEqual({ matching: true });

      // Now make them match - but note the validator doesn't clear errors automatically
      // The form needs to be re-validated
      formGroup.patchValue({
        confirmPassword: 'testPassword123',
      });

      const newResult = validator(formGroup);
      expect(newResult).toBeNull();
    });
  });
});
