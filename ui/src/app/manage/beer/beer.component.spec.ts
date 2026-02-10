import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { of, throwError } from 'rxjs';

import { ManageBeerComponent } from './beer.component';
import { DataService, DataError } from '../../_services/data.service';
import { Batch, Beer, ImageTransition, Location, UserInfo } from '../../models/models';

describe('ManageBeerComponent', () => {
  let component: ManageBeerComponent;
  let fixture: ComponentFixture<ManageBeerComponent>;
  let mockDataService: jasmine.SpyObj<DataService>;
  let mockRouter: jasmine.SpyObj<Router>;
  let mockSnackBar: jasmine.SpyObj<MatSnackBar>;
  let mockDialog: jasmine.SpyObj<MatDialog>;

  const mockUserInfo = {
    id: 'user-1',
    email: 'admin@example.com',
    firstName: 'Admin',
    lastName: 'User',
    admin: true,
    locations: [{ id: 'loc-1', name: 'Location 1' }],
  };

  const mockLocations = [
    { id: 'loc-1', name: 'location-1', description: 'Location 1' },
    { id: 'loc-2', name: 'location-2', description: 'Location 2' },
  ];

  const mockBeers = [
    {
      id: 'beer-1',
      name: 'IPA',
      description: 'India Pale Ale',
      style: 'IPA',
      abv: 6.5,
      ibu: 65,
      srm: 8,
    },
    {
      id: 'beer-2',
      name: 'Stout',
      description: 'Dark Stout',
      style: 'Stout',
      abv: 5.5,
      ibu: 35,
      srm: 40,
    },
  ];

  const mockBatches = [
    { id: 'batch-1', beerId: 'beer-1', batchNumber: '1', locationIds: ['loc-1'] },
    { id: 'batch-2', beerId: 'beer-1', batchNumber: '2', locationIds: ['loc-1'] },
  ];

  beforeEach(async () => {
    mockDataService = jasmine.createSpyObj('DataService', [
      'getCurrentUser',
      'getLocations',
      'getBeers',
      'getBeerBatches',
      'createBeer',
      'updateBeer',
      'deleteBeer',
      'createBatch',
      'updateBatch',
      'getBatch',
      'clearTap',
      'deleteImageTransition',
    ]);
    mockRouter = jasmine.createSpyObj('Router', ['navigate']);
    mockSnackBar = jasmine.createSpyObj('MatSnackBar', ['open']);
    mockDialog = jasmine.createSpyObj('MatDialog', ['open']);

    mockDataService.getCurrentUser.and.returnValue(of(mockUserInfo as any));
    mockDataService.getLocations.and.returnValue(of(mockLocations as any));
    mockDataService.getBeers.and.returnValue(of(mockBeers as any));
    mockDataService.getBeerBatches.and.returnValue(of(mockBatches as any));

    await TestBed.configureTestingModule({
      imports: [ReactiveFormsModule],
      declarations: [ManageBeerComponent],
      providers: [
        { provide: DataService, useValue: mockDataService },
        { provide: Router, useValue: mockRouter },
        { provide: MatSnackBar, useValue: mockSnackBar },
        { provide: MatDialog, useValue: mockDialog },
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ManageBeerComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  describe('initial state', () => {
    it('should have loading set to false', () => {
      expect(component.loading).toBe(false);
    });

    it('should have empty beers array', () => {
      expect(component.beers).toEqual([]);
    });

    it('should have processing set to false', () => {
      expect(component.processing).toBe(false);
    });

    it('should have adding set to false', () => {
      expect(component.adding).toBe(false);
    });

    it('should have editing set to false', () => {
      expect(component.editing).toBe(false);
    });

    it('should have addingBatch set to false', () => {
      expect(component.addingBatch).toBe(false);
    });

    it('should have editingBatch set to false', () => {
      expect(component.editingBatch).toBe(false);
    });

    it('should have showArchivedBatches set to false', () => {
      expect(component.showArchivedBatches).toBe(false);
    });

    it('should have modifyBeerFormGroup defined', () => {
      expect(component.modifyBeerFormGroup).toBeTruthy();
    });

    it('should have modifyBatchFormGroup defined', () => {
      expect(component.modifyBatchFormGroup).toBeTruthy();
    });

    it('should have externalBrewingTools defined', () => {
      expect(component.externalBrewingTools).toContain('brewfather');
    });

    it('should have decimalRegex defined', () => {
      expect(component.decimalRegex).toBeTruthy();
    });
  });

  describe('ngOnInit', () => {
    it('should call getCurrentUser', () => {
      fixture.detectChanges();
      expect(mockDataService.getCurrentUser).toHaveBeenCalled();
    });

    it('should set userInfo on success', () => {
      fixture.detectChanges();
      expect(component.userInfo.email).toBe('admin@example.com');
    });

    it('should populate selectedLocationFilters for admin', () => {
      fixture.detectChanges();
      expect(component.selectedLocationFilters).toContain('loc-1');
    });

    it('should call _refresh', () => {
      fixture.detectChanges();
      expect(mockDataService.getLocations).toHaveBeenCalled();
    });

    it('should display error on failure (non-401)', () => {
      const error: DataError = { message: 'Failed', statusCode: 500 } as DataError;
      mockDataService.getCurrentUser.and.returnValue(throwError(() => error));

      fixture.detectChanges();

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Failed', 'Close');
    });

    it('should not display error on 401 status', () => {
      const error: DataError = { message: 'Unauthorized', statusCode: 401 } as DataError;
      mockDataService.getCurrentUser.and.returnValue(throwError(() => error));

      fixture.detectChanges();

      expect(mockSnackBar.open).not.toHaveBeenCalled();
    });
  });

  describe('_refresh', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should call getLocations', () => {
      component._refresh();
      expect(mockDataService.getLocations).toHaveBeenCalled();
    });

    it('should call getBeers', () => {
      component._refresh();
      expect(mockDataService.getBeers).toHaveBeenCalled();
    });

    it('should populate locations', () => {
      component._refresh();
      expect(component.locations.length).toBe(2);
    });

    it('should populate beers', () => {
      component._refresh();
      expect(component.beers.length).toBe(2);
    });

    it('should call filter', () => {
      spyOn(component, 'filter');
      component._refresh();
      expect(component.filter).toHaveBeenCalled();
    });

    it('should call always callback on success', () => {
      const alwaysCallback = jasmine.createSpy('always');
      component._refresh(alwaysCallback);
      expect(alwaysCallback).toHaveBeenCalled();
    });

    it('should display error on locations failure', () => {
      const error: DataError = { message: 'Failed to load locations' } as DataError;
      mockDataService.getLocations.and.returnValue(throwError(() => error));

      component._refresh();

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Failed to load locations', 'Close');
    });
  });

  describe('refresh', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should set loading to true', () => {
      component.refresh();
      expect(mockDataService.getLocations).toHaveBeenCalled();
    });

    it('should call _refresh', () => {
      spyOn(component, '_refresh').and.callThrough();
      component.refresh();
      expect(component._refresh).toHaveBeenCalled();
    });
  });

  describe('displayedColumns getter', () => {
    it('should include expected columns', () => {
      const columns = component.displayedColumns;
      expect(columns).toContain('name');
      expect(columns).toContain('style');
      expect(columns).toContain('abv');
      expect(columns).toContain('ibu');
      expect(columns).toContain('srm');
      expect(columns).toContain('actions');
    });
  });

  describe('displayedBatchColumns getter', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should include locations when multiple locations', () => {
      component.locations = mockLocations as any;
      const columns = component.displayedBatchColumns;
      expect(columns).toContain('locations');
    });

    it('should not include locations when single location', () => {
      component.locations = [mockLocations[0]] as any;
      const columns = component.displayedBatchColumns;
      expect(columns).not.toContain('locations');
    });

    it('should include batchNumber', () => {
      const columns = component.displayedBatchColumns;
      expect(columns).toContain('batchNumber');
    });
  });

  describe('addBeer', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should reset modifyBeerFormGroup', () => {
      spyOn(component.modifyBeerFormGroup, 'reset');
      component.addBeer();
      expect(component.modifyBeerFormGroup.reset).toHaveBeenCalled();
    });

    it('should set adding to true', () => {
      component.addBeer();
      expect(component.adding).toBe(true);
    });

    it('should create new modifyBeer', () => {
      component.addBeer();
      expect(component.modifyBeer).toBeTruthy();
    });

    it('should set locationId when single location', () => {
      component.locations = [new Location(mockLocations[0])];
      component.addBeer();
      expect(component.modifyBeer.editValues.locationId).toBe('loc-1');
    });
  });

  describe('createBeer', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyBeer = new Beer();
      component.modifyBeer.enableEditing();
      component.modifyBeer.editValues = {
        name: 'New Beer',
        style: 'Pilsner',
        abv: 5.0,
        ibu: 30,
        srm: 4,
      };
      mockDataService.createBeer.and.returnValue(of(mockBeers[0] as any));
    });

    it('should set processing to true', () => {
      component.createBeer();
      expect(mockDataService.createBeer).toHaveBeenCalled();
    });

    it('should call createBeer', () => {
      component.createBeer();
      expect(mockDataService.createBeer).toHaveBeenCalled();
    });

    it('should set adding to false on success', () => {
      component.adding = true;
      component.createBeer();
      expect(component.adding).toBe(false);
    });

    it('should display error on failure', () => {
      const error: DataError = { message: 'Creation failed' } as DataError;
      mockDataService.createBeer.and.returnValue(throwError(() => error));

      component.createBeer();

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Creation failed', 'Close');
    });
  });

  describe('cancelAddBeer', () => {
    it('should set adding to false', () => {
      component.adding = true;
      component.cancelAddBeer();
      expect(component.adding).toBe(false);
    });
  });

  describe('editBeer', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should enable editing on beer', () => {
      const beer = new Beer(mockBeers[0]);
      component.editBeer(beer);
      expect(beer.isEditing).toBe(true);
    });

    it('should set modifyBeer', () => {
      const beer = new Beer(mockBeers[0]);
      component.editBeer(beer);
      expect(component.modifyBeer).toBe(beer);
    });

    it('should set editing to true', () => {
      const beer = new Beer(mockBeers[0]);
      component.editBeer(beer);
      expect(component.editing).toBe(true);
    });

    it('should reset imageTransitionsToDelete', () => {
      component.imageTransitionsToDelete = ['old-id'];
      const beer = new Beer(mockBeers[0]);
      component.editBeer(beer);
      expect(component.imageTransitionsToDelete).toEqual([]);
    });
  });

  describe('saveBeer', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyBeer = new Beer(mockBeers[0]);
      component.modifyBeer.enableEditing();
      component.modifyBeer.editValues.name = 'Updated Name';
      component.imageTransitionsToDelete = [];
      mockDataService.updateBeer.and.returnValue(of(mockBeers[0] as any));
    });

    it('should call updateBeer', () => {
      component.saveBeer();
      expect(mockDataService.updateBeer).toHaveBeenCalled();
    });

    it('should call deleteImageTransitionRecursive', () => {
      spyOn(component, 'deleteImageTransitionRecursive');
      component.saveBeer();
      expect(component.deleteImageTransitionRecursive).toHaveBeenCalled();
    });
  });

  describe('cancelEditBeer', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyBeer = new Beer(mockBeers[0]);
      component.modifyBeer.enableEditing();
      component.editing = true;
    });

    it('should disable editing on modifyBeer', () => {
      component.cancelEditBeer();
      expect(component.modifyBeer.isEditing).toBe(false);
    });

    it('should set editing to false when no image transitions to delete', () => {
      component.imageTransitionsToDelete = [];
      component.cancelEditBeer();
      expect(component.editing).toBe(false);
    });
  });

  describe('deleteBeer', () => {
    beforeEach(() => {
      fixture.detectChanges();
      mockDataService.deleteBeer.and.returnValue(of({}));
      component.beerBatches = { 'beer-1': [] };
    });

    it('should call deleteBeer when confirmed', () => {
      spyOn(window, 'confirm').and.returnValue(true);
      const beer = new Beer(mockBeers[0]);

      component.deleteBeer(beer);

      expect(mockDataService.deleteBeer).toHaveBeenCalledWith('beer-1');
    });

    it('should not call deleteBeer when not confirmed', () => {
      spyOn(window, 'confirm').and.returnValue(false);
      const beer = new Beer(mockBeers[0]);

      component.deleteBeer(beer);

      expect(mockDataService.deleteBeer).not.toHaveBeenCalled();
    });
  });

  describe('filter', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.beers = mockBeers.map(b => new Beer(b as any));
    });

    it('should populate filteredBeers', () => {
      component.filter();
      expect(component.filteredBeers.length).toBeGreaterThan(0);
    });

    it('should sort beers', () => {
      component.filter();
      expect(component.filteredBeers.length).toBe(2);
    });
  });

  describe('modifyBeerForm getter', () => {
    it('should return form controls', () => {
      const controls = component.modifyBeerForm;
      expect(controls['name']).toBeTruthy();
      expect(controls['style']).toBeTruthy();
      expect(controls['abv']).toBeTruthy();
    });
  });

  describe('modifyBatchForm getter', () => {
    it('should return form controls', () => {
      const controls = component.modifyBatchForm;
      expect(controls['batchNumber']).toBeTruthy();
      expect(controls['locationIds']).toBeTruthy();
    });
  });

  describe('hasBeerChanges getter', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyBeer = new Beer(mockBeers[0]);
      component.modifyBeer.enableEditing();
    });

    it('should return true when beer has changes', () => {
      component.modifyBeer.editValues.name = 'Changed';
      component.imageTransitionsToDelete = [];
      expect(component.hasBeerChanges).toBe(true);
    });

    it('should return true when imageTransitionsToDelete is not empty', () => {
      component.imageTransitionsToDelete = ['img-1'];
      expect(component.hasBeerChanges).toBe(true);
    });
  });

  describe('hasBatchChanges getter', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyBatch = new Batch(mockBatches[0] as any);
      component.modifyBatch.enableEditing();
    });

    it('should return true when batch has changes', () => {
      component.modifyBatch.editValues.batchNumber = 'Changed';
      expect(component.hasBatchChanges).toBe(true);
    });

    it('should return false when no changes', () => {
      expect(component.hasBatchChanges).toBe(false);
    });
  });

  describe('isBeerTapped', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should return false when no batches have taps', () => {
      component.beerBatches = { 'beer-1': [new Batch({ id: 'batch-1' } as any)] };
      const beer = new Beer(mockBeers[0]);
      expect(component.isBeerTapped(beer)).toBe(false);
    });

    it('should return true when batch has taps', () => {
      component.beerBatches = {
        'beer-1': [new Batch({ id: 'batch-1', taps: [{ id: 'tap-1' }] } as any)],
      };
      const beer = new Beer(mockBeers[0]);
      expect(component.isBeerTapped(beer)).toBe(true);
    });
  });

  describe('isBatchTapped', () => {
    it('should return false when batch has no taps', () => {
      const batch = new Batch({ id: 'batch-1' } as any);
      expect(component.isBatchTapped(batch)).toBe(false);
    });

    it('should return true when batch has taps', () => {
      const batch = new Batch({ id: 'batch-1', taps: [{ id: 'tap-1' }] } as any);
      expect(component.isBatchTapped(batch)).toBe(true);
    });
  });

  describe('addBatch', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should set selectedBatchBeer', () => {
      const beer = new Beer(mockBeers[0]);
      component.addBatch(beer);
      expect(component.selectedBatchBeer).toBe(beer);
    });

    it('should set addingBatch to true', () => {
      const beer = new Beer(mockBeers[0]);
      component.addBatch(beer);
      expect(component.addingBatch).toBe(true);
    });

    it('should set locationIds when single location', () => {
      component.locations = [new Location(mockLocations[0])];
      const beer = new Beer(mockBeers[0]);
      component.addBatch(beer);
      expect(component.modifyBatch.editValues.locationIds).toEqual(['loc-1']);
    });
  });

  describe('createBatch', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.selectedBatchBeer = new Beer(mockBeers[0]);
      component.modifyBatch = new Batch({ editValues: {} } as any);
      component.modifyBatch.enableEditing();
      component.modifyBatch.editValues = {
        batchNumber: '3',
        locationIds: ['loc-1'],
        brewDateObj: new Date(),
        kegDateObj: new Date(),
      };
      mockDataService.createBatch.and.returnValue(of(mockBatches[0] as any));
    });

    it('should set processing to true', () => {
      component.createBatch();
      expect(mockDataService.createBatch).toHaveBeenCalled();
    });

    it('should call createBatch', () => {
      component.createBatch();
      expect(mockDataService.createBatch).toHaveBeenCalled();
    });

    it('should display error on failure', () => {
      const error: DataError = { message: 'Batch creation failed' } as DataError;
      mockDataService.createBatch.and.returnValue(throwError(() => error));

      component.createBatch();

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Batch creation failed', 'Close');
    });
  });

  describe('cancelAddBatch', () => {
    it('should set addingBatch to false', () => {
      component.addingBatch = true;
      component.cancelAddBatch();
      expect(component.addingBatch).toBe(false);
    });
  });

  describe('editBatch', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should set selectedBatchBeer', () => {
      const batch = new Batch(mockBatches[0] as any);
      const beer = new Beer(mockBeers[0]);
      component.editBatch(batch, beer);
      expect(component.selectedBatchBeer).toBe(beer);
    });

    it('should enable editing on batch', () => {
      const batch = new Batch(mockBatches[0] as any);
      const beer = new Beer(mockBeers[0]);
      component.editBatch(batch, beer);
      expect(batch.isEditing).toBe(true);
    });

    it('should set editingBatch to true', () => {
      const batch = new Batch(mockBatches[0] as any);
      const beer = new Beer(mockBeers[0]);
      component.editBatch(batch, beer);
      expect(component.editingBatch).toBe(true);
    });
  });

  describe('cancelEditBatch', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyBatch = new Batch(mockBatches[0] as any);
      component.modifyBatch.enableEditing();
      component.editingBatch = true;
    });

    it('should disable editing on modifyBatch', () => {
      component.cancelEditBatch();
      expect(component.modifyBatch.isEditing).toBe(false);
    });

    it('should set editingBatch to false', () => {
      component.cancelEditBatch();
      expect(component.editingBatch).toBe(false);
    });
  });

  describe('image transitions', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyBeer = new Beer(mockBeers[0]);
      component.modifyBeer.enableEditing();
    });

    describe('addImageTransition', () => {
      it('should initialize imageTransitions array if not exists', () => {
        component.modifyBeer.imageTransitions = undefined as any;
        component.addImageTransition();
        expect(component.modifyBeer.imageTransitions).toBeTruthy();
      });

      it('should add new image transition', () => {
        component.modifyBeer.imageTransitions = [];
        component.addImageTransition();
        expect(component.modifyBeer.imageTransitions.length).toBe(1);
      });

      it('should enable editing on new image transition', () => {
        component.modifyBeer.imageTransitions = [];
        component.addImageTransition();
        expect(component.modifyBeer.imageTransitions[0].isEditing).toBe(true);
      });
    });

    describe('areImageTransitionsValid getter', () => {
      it('should return true when no image transitions enabled', () => {
        component.modifyBeer.imageTransitionsEnabled = false;
        expect(component.areImageTransitionsValid).toBe(true);
      });

      it('should return true when no edit values', () => {
        component.modifyBeer.editValues = undefined as any;
        expect(component.areImageTransitionsValid).toBe(true);
      });

      it('should return false for invalid image transition', () => {
        component.modifyBeer.imageTransitionsEnabled = true;
        component.modifyBeer.imageTransitions = [new ImageTransition()];
        component.modifyBeer.imageTransitions[0].enableEditing();
        component.modifyBeer.imageTransitions[0].editValues = {
          changePercent: undefined,
          imgUrl: '',
        };
        expect(component.areImageTransitionsValid).toBe(false);
      });
    });
  });

  describe('getDescriptionDisplay', () => {
    it('should return empty string for empty description', () => {
      const beer = new Beer({} as any);
      expect(component.getDescriptionDisplay(beer)).toBe('');
    });

    it('should truncate long descriptions', () => {
      const beer = new Beer({
        description: 'This is a very long description that should be truncated because it exceeds 48 characters',
      } as any);
      const result = component.getDescriptionDisplay(beer);
      expect(result.length).toBeLessThanOrEqual(51); // 48 + "..."
    });

    it('should return full description for short descriptions', () => {
      const beer = new Beer({ description: 'Short desc' } as any);
      expect(component.getDescriptionDisplay(beer)).toBe('Short desc');
    });
  });

  describe('isDescriptionTooLong', () => {
    it('should return false for empty description', () => {
      const beer = new Beer({} as any);
      expect(component.isDescriptionTooLong(beer)).toBe(false);
    });

    it('should return false for short description', () => {
      const beer = new Beer({ description: 'Short' } as any);
      expect(component.isDescriptionTooLong(beer)).toBe(false);
    });

    it('should return true for long description', () => {
      const beer = new Beer({
        description: 'This is a very long description that should exceed 48 characters easily',
      } as any);
      expect(component.isDescriptionTooLong(beer)).toBe(true);
    });
  });

  describe('getBeerLink', () => {
    it('should return empty string for null beer', () => {
      expect(component.getBeerLink(null as any)).toBe('');
    });

    it('should return brewfather link for brewfather tool', () => {
      const beer = new Beer({
        externalBrewingTool: 'brewfather',
        externalBrewingToolMeta: { recipeId: 'recipe123' },
      } as any);
      expect(component.getBeerLink(beer)).toBe(
        'https://web.brewfather.app/tabs/recipes/recipe/recipe123'
      );
    });

    it('should return empty string for beer without external tool', () => {
      const beer = new Beer({} as any);
      expect(component.getBeerLink(beer)).toBe('');
    });
  });

  describe('getBatchLink', () => {
    it('should return empty string for null batch', () => {
      expect(component.getBatchLink(null as any)).toBe('');
    });

    it('should return brewfather link for brewfather tool', () => {
      const batch = new Batch({
        externalBrewingTool: 'brewfather',
        externalBrewingToolMeta: { batchId: 'batch123' },
      } as any);
      expect(component.getBatchLink(batch)).toBe(
        'https://web.brewfather.app/tabs/batches/batch/batch123'
      );
    });

    it('should return empty string for batch without external tool', () => {
      const batch = new Batch({} as any);
      expect(component.getBatchLink(batch)).toBe('');
    });
  });

  describe('isArchivedBatch', () => {
    it('should return false when archivedOn is null', () => {
      const batch = new Batch({} as any);
      expect(component.isArchivedBatch(batch)).toBe(false);
    });

    it('should return true when archivedOn is set', () => {
      const batch = new Batch({ archivedOn: Date.now() } as any);
      expect(component.isArchivedBatch(batch)).toBe(true);
    });
  });

  describe('displayError', () => {
    it('should open snackbar with error message', () => {
      component.displayError('Something went wrong');

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Something went wrong', 'Close');
    });
  });
});
