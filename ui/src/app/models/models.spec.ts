import { Batch, Beer } from './models';

describe('models', () => {
  describe('ExtToolBase.getVal', () => {
    describe('without batch', () => {
      it('returns own local value', () => {
        const beer = new Beer({ name: 'IPA' });
        expect(beer.getVal('name')).toBe('IPA');
      });

      it('falls back to own ext tool value when no local value', () => {
        const beer = new Beer({
          externalBrewingTool: 'brewfather',
          externalBrewingToolMeta: { details: { name: 'Brewer IPA' } },
        });
        expect(beer.getVal('name')).toBe('Brewer IPA');
      });

      it('returns null when neither local nor ext tool has value', () => {
        const beer = new Beer({});
        expect(beer.getVal('name')).toBeNull();
      });

      it('applies transformFn to own local value', () => {
        const beer = new Beer({ name: 'ipa' });
        expect(beer.getVal('name', undefined, (v: string) => v.toUpperCase())).toBe('IPA');
      });
    });

    describe('with batch', () => {
      it('batch local value takes priority over own local value', () => {
        const beer = new Beer({ name: 'Beer Name' });
        const batch = new Batch({ name: 'Batch Name' });
        expect(beer.getVal('name', batch)).toBe('Batch Name');
      });

      it('own local value used when batch has no local value', () => {
        const beer = new Beer({ name: 'Beer Name' });
        const batch = new Batch({});
        expect(beer.getVal('name', batch)).toBe('Beer Name');
      });

      it('own local value beats batch ext tool value', () => {
        const beer = new Beer({ name: 'Beer Name' });
        const batch = new Batch({
          externalBrewingTool: 'brewfather',
          externalBrewingToolMeta: { details: { name: 'Batch Tool Name' } },
        });
        expect(beer.getVal('name', batch)).toBe('Beer Name');
      });

      it('batch ext tool value beats own ext tool value', () => {
        const beer = new Beer({
          externalBrewingTool: 'brewfather',
          externalBrewingToolMeta: { details: { name: 'Beer Tool Name' } },
        });
        const batch = new Batch({
          externalBrewingTool: 'brewfather',
          externalBrewingToolMeta: { details: { name: 'Batch Tool Name' } },
        });
        expect(beer.getVal('name', batch)).toBe('Batch Tool Name');
      });

      it('falls back to own ext tool value when batch has no ext tool value', () => {
        const beer = new Beer({
          externalBrewingTool: 'brewfather',
          externalBrewingToolMeta: { details: { name: 'Beer Tool Name' } },
        });
        const batch = new Batch({});
        expect(beer.getVal('name', batch)).toBe('Beer Tool Name');
      });

      it('applies transformFn to batch local value', () => {
        const beer = new Beer({ name: 'beer name' });
        const batch = new Batch({ name: 'batch name' });
        expect(beer.getVal('name', batch, (v: string) => v.toUpperCase())).toBe('BATCH NAME');
      });

      it('returns null when no source has value', () => {
        const beer = new Beer({});
        const batch = new Batch({});
        expect(beer.getVal('name', batch)).toBeNull();
      });
    });
  });
});
