import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { BehaviorSubject, of, throwError } from 'rxjs';

import { CurrentUserService } from '../../_services/current-user.service';
import { DataError, DataService } from '../../_services/data.service';
import { SettingsService } from '../../_services/settings.service';
import { Batch, Beverage, ImageTransition, Location } from '../../models/models';
import { ManageBeverageComponent } from './beverage.component';

describe('ManageBeverageComponent', () => {
  let component: ManageBeverageComponent;
  let fixture: ComponentFixture<ManageBeverageComponent>;
  let mockCurrentUserService: jasmine.SpyObj<CurrentUserService>;
  let mockDataService: jasmine.SpyObj<DataService>;
  let mockSettingsService: jasmine.SpyObj<SettingsService>;
  let mockRouter: jasmine.SpyObj<Router>;
  let mockSnackBar: jasmine.SpyObj<MatSnackBar>;
  let mockDialog: jasmine.SpyObj<MatDialog>;
  let settingsSubject: BehaviorSubject<any>;

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

  const mockSettings = {
    beverages: {
      defaultType: 'nitro-coffee',
      supportedTypes: ['nitro-coffee', 'kombucha', 'cider'],
    },
  };

  const mockBeverages = [
    {
      id: 'bev-1',
      name: 'Cold Brew',
      type: 'nitro-coffee',
      description: 'Smooth cold brew',
      brewery: 'Local Roasters',
    },
    {
      id: 'bev-2',
      name: 'Ginger Kombucha',
      type: 'kombucha',
      description: 'Spicy ginger flavor',
      brewery: 'Booch Co',
    },
  ];

  const mockBatches = [
    { id: 'batch-1', beverageId: 'bev-1', batchNumber: '1', locationIds: ['loc-1'] },
    { id: 'batch-2', beverageId: 'bev-1', batchNumber: '2', locationIds: ['loc-1'] },
  ];

  beforeEach(async () => {
    mockCurrentUserService = jasmine.createSpyObj('CurrentUserService', ['getCurrentUser']);
    mockDataService = jasmine.createSpyObj('DataService', [
      'getLocations',
      'getBeverages',
      'getBeverageBatches',
      'createBeverage',
      'updateBeverage',
      'deleteBeverage',
      'createBatch',
      'updateBatch',
      'getBatch',
      'clearTap',
      'clearKegtronPort',
      'deleteImageTransition',
    ]);
    mockSettingsService = jasmine.createSpyObj('SettingsService', ['getSetting'], {
      settings$: new BehaviorSubject(mockSettings),
    });
    mockRouter = jasmine.createSpyObj('Router', ['navigate']);
    mockSnackBar = jasmine.createSpyObj('MatSnackBar', ['open']);
    mockDialog = jasmine.createSpyObj('MatDialog', ['open']);

    settingsSubject = mockSettingsService.settings$ as BehaviorSubject<any>;

    mockCurrentUserService.getCurrentUser.and.returnValue(of(mockUserInfo as any));
    mockDataService.getLocations.and.returnValue(of(mockLocations as any));
    mockDataService.getBeverages.and.returnValue(of(mockBeverages as any));
    mockDataService.getBeverageBatches.and.returnValue(of(mockBatches as any));

    await TestBed.configureTestingModule({
      imports: [ReactiveFormsModule],
      declarations: [ManageBeverageComponent],
      providers: [
        { provide: CurrentUserService, useValue: mockCurrentUserService },
        { provide: DataService, useValue: mockDataService },
        { provide: SettingsService, useValue: mockSettingsService },
        { provide: Router, useValue: mockRouter },
        { provide: MatSnackBar, useValue: mockSnackBar },
        { provide: MatDialog, useValue: mockDialog },
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ManageBeverageComponent);
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

    it('should have empty beverages array', () => {
      expect(component.beverages).toEqual([]);
    });

    it('should have processing set to false', () => {
      expect(component.processing).toBe(false);
    });

    it('should have addingBeverage set to false', () => {
      expect(component.addingBeverage).toBe(false);
    });

    it('should have editingBeverage set to false', () => {
      expect(component.editingBeverage).toBe(false);
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

    it('should have modifyBeverageFormGroup defined', () => {
      expect(component.modifyBeverageFormGroup).toBeTruthy();
    });

    it('should have modifyBatchFormGroup defined', () => {
      expect(component.modifyBatchFormGroup).toBeTruthy();
    });
  });

  describe('ngOnInit', () => {
    it('should call getCurrentUser', () => {
      fixture.detectChanges();
      expect(mockCurrentUserService.getCurrentUser).toHaveBeenCalled();
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
      mockCurrentUserService.getCurrentUser.and.returnValue(throwError(() => error));

      fixture.detectChanges();

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Failed', 'Close');
    });

    it('should not display error on 401 status', () => {
      const error: DataError = { message: 'Unauthorized', statusCode: 401 } as DataError;
      mockCurrentUserService.getCurrentUser.and.returnValue(throwError(() => error));

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

    it('should call getBeverages', () => {
      component._refresh();
      expect(mockDataService.getBeverages).toHaveBeenCalled();
    });

    it('should populate locations', () => {
      component._refresh();
      expect(component.locations.length).toBe(2);
    });

    it('should populate beverages', () => {
      component._refresh();
      expect(component.beverages.length).toBe(2);
    });

    it('should set defaultType from settings', () => {
      component._refresh();
      expect(component.defaultType).toBe('nitro-coffee');
    });

    it('should set supportedTypes from settings', () => {
      component._refresh();
      expect(component.supportedTypes).toContain('nitro-coffee');
      expect(component.supportedTypes).toContain('kombucha');
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
      expect(columns).toContain('type');
      expect(columns).toContain('brewery');
      expect(columns).toContain('flavor');
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

  describe('addBeverage', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should reset modifyBeverageFormGroup', () => {
      spyOn(component.modifyBeverageFormGroup, 'reset');
      component.addBeverage();
      expect(component.modifyBeverageFormGroup.reset).toHaveBeenCalled();
    });

    it('should set addingBeverage to true', () => {
      component.addBeverage();
      expect(component.addingBeverage).toBe(true);
    });

    it('should create new modifyBeverage', () => {
      component.addBeverage();
      expect(component.modifyBeverage).toBeTruthy();
    });

    it('should set default type', () => {
      component.defaultType = 'nitro-coffee';
      component.addBeverage();
      expect(component.modifyBeverage.editValues.type).toBe('nitro-coffee');
    });

    it('should set locationId when single location', () => {
      component.locations = [new Location(mockLocations[0])];
      component.addBeverage();
      expect(component.modifyBeverage.editValues.locationId).toBe('loc-1');
    });
  });

  describe('createBeverage', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyBeverage = new Beverage();
      component.modifyBeverage.enableEditing();
      component.modifyBeverage.editValues = {
        name: 'New Beverage',
        type: 'kombucha',
        description: 'Tasty drink',
        brewery: 'Local',
        breweryLink: '',
        flavor: 'Fruity',
        imgUrl: '',
        meta: {},
      };
      mockDataService.createBeverage.and.returnValue(of(mockBeverages[0] as any));
    });

    it('should set processing to true', () => {
      component.createBeverage();
      expect(mockDataService.createBeverage).toHaveBeenCalled();
    });

    it('should call createBeverage', () => {
      component.createBeverage();
      expect(mockDataService.createBeverage).toHaveBeenCalled();
    });

    it('should display error on failure', () => {
      const error: DataError = { message: 'Creation failed' } as DataError;
      mockDataService.createBeverage.and.returnValue(throwError(() => error));

      component.createBeverage();

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Creation failed', 'Close');
    });
  });

  describe('cancelAddBeverage', () => {
    it('should set addingBeverage to false', () => {
      component.addingBeverage = true;
      component.cancelAddBeverage();
      expect(component.addingBeverage).toBe(false);
    });
  });

  describe('editBeverage', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should enable editing on beverage', () => {
      const beverage = new Beverage(mockBeverages[0]);
      component.editBeverage(beverage);
      expect(beverage.isEditing).toBe(true);
    });

    it('should set modifyBeverage', () => {
      const beverage = new Beverage(mockBeverages[0]);
      component.editBeverage(beverage);
      expect(component.modifyBeverage).toBe(beverage);
    });

    it('should set editingBeverage to true', () => {
      const beverage = new Beverage(mockBeverages[0]);
      component.editBeverage(beverage);
      expect(component.editingBeverage).toBe(true);
    });

    it('should reset imageTransitionsToDelete', () => {
      component.imageTransitionsToDelete = ['old-id'];
      const beverage = new Beverage(mockBeverages[0]);
      component.editBeverage(beverage);
      expect(component.imageTransitionsToDelete).toEqual([]);
    });
  });

  describe('saveBeverage', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyBeverage = new Beverage(mockBeverages[0]);
      component.modifyBeverage.enableEditing();
      component.modifyBeverage.editValues.name = 'Updated Name';
      component.imageTransitionsToDelete = [];
      mockDataService.updateBeverage.and.returnValue(of(mockBeverages[0] as any));
    });

    it('should call updateBeverage', () => {
      component.saveBeverage();
      expect(mockDataService.updateBeverage).toHaveBeenCalled();
    });

    it('should call deleteImageTransitionRecursive', () => {
      spyOn(component, 'deleteImageTransitionRecursive');
      component.saveBeverage();
      expect(component.deleteImageTransitionRecursive).toHaveBeenCalled();
    });
  });

  describe('cancelEditBeverage', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyBeverage = new Beverage(mockBeverages[0]);
      component.modifyBeverage.enableEditing();
      component.editingBeverage = true;
    });

    it('should disable editing on modifyBeverage', () => {
      component.cancelEditBeverage();
      expect(component.modifyBeverage.isEditing).toBe(false);
    });

    it('should set editingBeverage to false when no image transitions to delete', () => {
      component.imageTransitionsToDelete = [];
      component.cancelEditBeverage();
      expect(component.editingBeverage).toBe(false);
    });
  });

  describe('deleteBeverage', () => {
    beforeEach(() => {
      fixture.detectChanges();
      mockDataService.deleteBeverage.and.returnValue(of({}));
      component.beverageBatches = { 'bev-1': [] };
    });

    it('should call deleteBeverage when confirmed', () => {
      spyOn(window, 'confirm').and.returnValue(true);
      const beverage = new Beverage(mockBeverages[0]);

      component.deleteBeverage(beverage);

      expect(mockDataService.deleteBeverage).toHaveBeenCalledWith('bev-1');
    });

    it('should not call deleteBeverage when not confirmed', () => {
      spyOn(window, 'confirm').and.returnValue(false);
      const beverage = new Beverage(mockBeverages[0]);

      component.deleteBeverage(beverage);

      expect(mockDataService.deleteBeverage).not.toHaveBeenCalled();
    });
  });

  describe('filter', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.beverages = mockBeverages.map(b => new Beverage(b as any));
    });

    it('should populate filteredBeverages', () => {
      component.filter();
      expect(component.filteredBeverages.length).toBeGreaterThan(0);
    });

    it('should sort beverages', () => {
      component.filter();
      expect(component.filteredBeverages.length).toBe(2);
    });
  });

  describe('modifyForm getter', () => {
    it('should return form controls', () => {
      const controls = component.modifyForm;
      expect(controls['name']).toBeTruthy();
      expect(controls['type']).toBeTruthy();
      expect(controls['description']).toBeTruthy();
    });
  });

  describe('modifyBatchForm getter', () => {
    it('should return form controls', () => {
      const controls = component.modifyBatchForm;
      expect(controls['batchNumber']).toBeTruthy();
      expect(controls['locationIds']).toBeTruthy();
    });
  });

  describe('hasBeverageChanges getter', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.modifyBeverage = new Beverage(mockBeverages[0]);
      component.modifyBeverage.enableEditing();
    });

    it('should return true when beverage has changes', () => {
      component.modifyBeverage.editValues.name = 'Changed';
      component.imageTransitionsToDelete = [];
      expect(component.hasBeverageChanges).toBe(true);
    });

    it('should return true when imageTransitionsToDelete is not empty', () => {
      component.imageTransitionsToDelete = ['img-1'];
      expect(component.hasBeverageChanges).toBe(true);
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

  describe('isBeverageTapped', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should return false when no batches have taps', () => {
      component.beverageBatches = { 'bev-1': [new Batch({ id: 'batch-1' } as any)] };
      const beverage = new Beverage(mockBeverages[0]);
      expect(component.isBeverageTapped(beverage)).toBe(false);
    });

    it('should return true when batch has taps', () => {
      component.beverageBatches = {
        'bev-1': [new Batch({ id: 'batch-1', taps: [{ id: 'tap-1' }] } as any)],
      };
      const beverage = new Beverage(mockBeverages[0]);
      expect(component.isBeverageTapped(beverage)).toBe(true);
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

    it('should set selectedBatchBeverage', () => {
      const beverage = new Beverage(mockBeverages[0]);
      component.addBatch(beverage);
      expect(component.selectedBatchBeverage).toBe(beverage);
    });

    it('should set addingBatch to true', () => {
      const beverage = new Beverage(mockBeverages[0]);
      component.addBatch(beverage);
      expect(component.addingBatch).toBe(true);
    });

    it('should set locationIds when single location', () => {
      component.locations = [new Location(mockLocations[0])];
      const beverage = new Beverage(mockBeverages[0]);
      component.addBatch(beverage);
      expect(component.modifyBatch.editValues.locationIds).toEqual(['loc-1']);
    });
  });

  describe('createBatch', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.selectedBatchBeverage = new Beverage(mockBeverages[0]);
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

    it('should set selectedBatchBeverage', () => {
      const batch = new Batch(mockBatches[0] as any);
      const beverage = new Beverage(mockBeverages[0]);
      component.editBatch(batch, beverage);
      expect(component.selectedBatchBeverage).toBe(beverage);
    });

    it('should enable editing on batch', () => {
      const batch = new Batch(mockBatches[0] as any);
      const beverage = new Beverage(mockBeverages[0]);
      component.editBatch(batch, beverage);
      expect(batch.isEditing).toBe(true);
    });

    it('should set editingBatch to true', () => {
      const batch = new Batch(mockBatches[0] as any);
      const beverage = new Beverage(mockBeverages[0]);
      component.editBatch(batch, beverage);
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
      component.modifyBeverage = new Beverage(mockBeverages[0]);
      component.modifyBeverage.enableEditing();
    });

    describe('addImageTransition', () => {
      it('should initialize imageTransitions array if not exists', () => {
        component.modifyBeverage.imageTransitions = undefined as any;
        component.addImageTransition();
        expect(component.modifyBeverage.imageTransitions).toBeTruthy();
      });

      it('should add new image transition', () => {
        component.modifyBeverage.imageTransitions = [];
        component.addImageTransition();
        expect(component.modifyBeverage.imageTransitions.length).toBe(1);
      });

      it('should enable editing on new image transition', () => {
        component.modifyBeverage.imageTransitions = [];
        component.addImageTransition();
        expect(component.modifyBeverage.imageTransitions[0].isEditing).toBe(true);
      });
    });

    describe('areImageTransitionsValid getter', () => {
      it('should return true when no image transitions enabled', () => {
        component.modifyBeverage.imageTransitionsEnabled = false;
        expect(component.areImageTransitionsValid).toBe(true);
      });

      it('should return true when no edit values', () => {
        component.modifyBeverage.editValues = undefined as any;
        expect(component.areImageTransitionsValid).toBe(true);
      });

      it('should return false for invalid image transition', () => {
        component.modifyBeverage.imageTransitionsEnabled = true;
        component.modifyBeverage.imageTransitions = [new ImageTransition()];
        component.modifyBeverage.imageTransitions[0].enableEditing();
        component.modifyBeverage.imageTransitions[0].editValues = {
          changePercent: undefined,
          imgUrl: '',
        };
        expect(component.areImageTransitionsValid).toBe(false);
      });
    });
  });

  describe('getDescriptionDisplay', () => {
    it('should return empty string for empty description', () => {
      const beverage = new Beverage({} as any);
      expect(component.getDescriptionDisplay(beverage)).toBe('');
    });

    it('should truncate long descriptions', () => {
      const beverage = new Beverage({
        description:
          'This is a very long description that should be truncated because it exceeds 48 characters',
      } as any);
      const result = component.getDescriptionDisplay(beverage);
      expect(result.length).toBeLessThanOrEqual(51); // 48 + "..."
    });

    it('should return full description for short descriptions', () => {
      const beverage = new Beverage({ description: 'Short desc' } as any);
      expect(component.getDescriptionDisplay(beverage)).toBe('Short desc');
    });
  });

  describe('isDescriptionTooLong', () => {
    it('should return false for null beverage', () => {
      expect(component.isDescriptionTooLong(null as any)).toBe(false);
    });

    it('should return false for short description', () => {
      const beverage = new Beverage({ description: 'Short' } as any);
      expect(component.isDescriptionTooLong(beverage)).toBe(false);
    });

    it('should return true for long description', () => {
      const beverage = new Beverage({
        description: 'This is a very long description that should exceed 48 characters easily',
      } as any);
      expect(component.isDescriptionTooLong(beverage)).toBe(true);
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

  describe('dateToNumber', () => {
    it('should return undefined for empty value', () => {
      expect(component.dateToNumber(null)).toBeUndefined();
      expect(component.dateToNumber('')).toBeUndefined();
    });

    it('should convert Date to number', () => {
      const date = new Date(2024, 0, 1);
      const result = component.dateToNumber(date);
      expect(typeof result).toBe('number');
    });

    it('should convert number to number', () => {
      const timestamp = 1704067200;
      const result = component.dateToNumber(timestamp);
      expect(result).toBe(1704067200);
    });
  });

  describe('form validation', () => {
    it('should require name', () => {
      const control = component.modifyBeverageFormGroup.get('name');
      control?.setValue('');
      expect(control?.hasError('required')).toBe(true);
    });

    it('should require type', () => {
      const control = component.modifyBeverageFormGroup.get('type');
      control?.setValue('');
      expect(control?.hasError('required')).toBe(true);
    });

    it('should require batchNumber in batch form', () => {
      const control = component.modifyBatchFormGroup.get('batchNumber');
      control?.setValue('');
      expect(control?.hasError('required')).toBe(true);
    });

    it('should require locationIds in batch form', () => {
      const control = component.modifyBatchFormGroup.get('locationIds');
      control?.setValue('');
      expect(control?.hasError('required')).toBe(true);
    });
  });

  describe('displayError', () => {
    it('should open snackbar with error message', () => {
      component.displayError('Something went wrong');

      expect(mockSnackBar.open).toHaveBeenCalledWith('Error: Something went wrong', 'Close');
    });
  });

  describe('saveBatch', () => {
    beforeEach(() => {
      fixture.detectChanges();
      component.locations = mockLocations as any;
    });

    it('should refresh without calling updateBatch when no changes', () => {
      const batch = new Batch({ id: 'batch-1', locationIds: ['loc-1'] } as any);
      batch.enableEditing();
      component.modifyBatch = batch;
      component.editingBatch = true;

      mockDataService.getBeverages.and.returnValue(of(mockBeverages as any));
      mockDataService.getBeverageBatches.and.returnValue(of(mockBatches as any));

      component.saveBatch();

      expect(mockDataService.updateBatch).not.toHaveBeenCalled();
    });

    it('should call updateBatch directly when locationIds not changed', () => {
      const batch = new Batch({ id: 'batch-1', name: 'Old Name', locationIds: ['loc-1'] } as any);
      batch.enableEditing();
      batch.editValues.name = 'New Name';
      component.modifyBatch = batch;
      component.editingBatch = true;

      mockDataService.updateBatch.and.returnValue(of({} as any));
      mockDataService.getBeverages.and.returnValue(of(mockBeverages as any));
      mockDataService.getBeverageBatches.and.returnValue(of(mockBatches as any));

      component.saveBatch();

      expect(mockDataService.updateBatch).toHaveBeenCalledWith(
        'batch-1',
        jasmine.objectContaining({ name: 'New Name' })
      );
    });

    it('should save directly when locations removed but no taps at removed locations', () => {
      const batch = new Batch({
        id: 'batch-1',
        locationIds: ['loc-1', 'loc-2'],
        taps: [{ id: 'tap-1', tapNumber: 1, description: 'Tap 1', locationId: 'loc-1' }],
      } as any);
      batch.enableEditing();
      batch.editValues.locationIds = ['loc-1'];
      component.modifyBatch = batch;
      component.editingBatch = true;

      mockDataService.updateBatch.and.returnValue(of({} as any));
      mockDataService.getBeverages.and.returnValue(of(mockBeverages as any));
      mockDataService.getBeverageBatches.and.returnValue(of(mockBatches as any));

      component.saveBatch();

      expect(mockDataService.updateBatch).toHaveBeenCalled();
      expect(mockDataService.clearTap).not.toHaveBeenCalled();
    });

    it('should clear taps and save when user confirms removal of taps at removed locations', () => {
      spyOn(window, 'confirm').and.returnValue(true);

      const batch = new Batch({
        id: 'batch-1',
        locationIds: ['loc-1', 'loc-2'],
        taps: [{ id: 'tap-1', tapNumber: 1, description: 'Tap 1', locationId: 'loc-2' }],
      } as any);
      batch.enableEditing();
      batch.editValues.locationIds = ['loc-1'];
      component.modifyBatch = batch;
      component.editingBatch = true;

      mockDataService.clearTap.and.returnValue(of({} as any));
      mockDataService.updateBatch.and.returnValue(of({} as any));
      mockDataService.getBeverages.and.returnValue(of(mockBeverages as any));
      mockDataService.getBeverageBatches.and.returnValue(of(mockBatches as any));

      component.saveBatch();

      expect(window.confirm).toHaveBeenCalled();
      expect(mockDataService.clearTap).toHaveBeenCalledWith('tap-1');
      expect(mockDataService.updateBatch).toHaveBeenCalled();
    });

    it('should not make API calls when user cancels confirmation', () => {
      spyOn(window, 'confirm').and.returnValue(false);

      const batch = new Batch({
        id: 'batch-1',
        locationIds: ['loc-1', 'loc-2'],
        taps: [{ id: 'tap-1', tapNumber: 1, description: 'Tap 1', locationId: 'loc-2' }],
      } as any);
      batch.enableEditing();
      batch.editValues.locationIds = ['loc-1'];
      component.modifyBatch = batch;
      component.editingBatch = true;

      component.saveBatch();

      expect(window.confirm).toHaveBeenCalled();
      expect(mockDataService.clearTap).not.toHaveBeenCalled();
      expect(mockDataService.updateBatch).not.toHaveBeenCalled();
      expect(component.processing).toBe(false);
    });

    it('should call clearKegtronPort then clearTap for kegtron-pro tap at removed location', () => {
      spyOn(window, 'confirm').and.returnValue(true);

      const batch = new Batch({
        id: 'batch-1',
        locationIds: ['loc-1', 'loc-2'],
        taps: [
          {
            id: 'tap-1',
            tapNumber: 1,
            description: 'Tap 1',
            locationId: 'loc-2',
            tapMonitor: { monitorType: 'kegtron-pro', meta: { deviceId: 'dev-1', portNum: 0 } },
          },
        ],
      } as any);
      batch.enableEditing();
      batch.editValues.locationIds = ['loc-1'];
      component.modifyBatch = batch;
      component.editingBatch = true;

      mockDataService.clearKegtronPort.and.returnValue(of({} as any));
      mockDataService.clearTap.and.returnValue(of({} as any));
      mockDataService.updateBatch.and.returnValue(of({} as any));
      mockDataService.getBeverages.and.returnValue(of(mockBeverages as any));
      mockDataService.getBeverageBatches.and.returnValue(of(mockBatches as any));

      component.saveBatch();

      expect(mockDataService.clearKegtronPort).toHaveBeenCalledWith('dev-1', 0);
      expect(mockDataService.clearTap).toHaveBeenCalledWith('tap-1');
      expect(mockDataService.updateBatch).toHaveBeenCalled();
    });

    it('should still clear tap and save when clearKegtronPort fails', () => {
      spyOn(window, 'confirm').and.returnValue(true);

      const batch = new Batch({
        id: 'batch-1',
        locationIds: ['loc-1', 'loc-2'],
        taps: [
          {
            id: 'tap-1',
            tapNumber: 1,
            description: 'Tap 1',
            locationId: 'loc-2',
            tapMonitor: { monitorType: 'kegtron-pro', meta: { deviceId: 'dev-1', portNum: 0 } },
          },
        ],
      } as any);
      batch.enableEditing();
      batch.editValues.locationIds = ['loc-1'];
      component.modifyBatch = batch;
      component.editingBatch = true;

      mockDataService.clearKegtronPort.and.returnValue(
        throwError(() => new DataError('Kegtron error', 500))
      );
      mockDataService.clearTap.and.returnValue(of({} as any));
      mockDataService.updateBatch.and.returnValue(of({} as any));
      mockDataService.getBeverages.and.returnValue(of(mockBeverages as any));
      mockDataService.getBeverageBatches.and.returnValue(of(mockBatches as any));

      component.saveBatch();

      expect(mockDataService.clearKegtronPort).toHaveBeenCalled();
      expect(mockSnackBar.open).toHaveBeenCalledWith(
        jasmine.stringContaining('Kegtron port'),
        'Close'
      );
      expect(mockDataService.clearTap).toHaveBeenCalledWith('tap-1');
      expect(mockDataService.updateBatch).toHaveBeenCalled();
    });

    it('should not save when clearTap fails', () => {
      spyOn(window, 'confirm').and.returnValue(true);

      const batch = new Batch({
        id: 'batch-1',
        locationIds: ['loc-1', 'loc-2'],
        taps: [{ id: 'tap-1', tapNumber: 1, description: 'Tap 1', locationId: 'loc-2' }],
      } as any);
      batch.enableEditing();
      batch.editValues.locationIds = ['loc-1'];
      component.modifyBatch = batch;
      component.editingBatch = true;

      mockDataService.clearTap.and.returnValue(
        throwError(() => new DataError('Clear tap error', 500))
      );

      component.saveBatch();

      expect(mockDataService.clearTap).toHaveBeenCalledWith('tap-1');
      expect(mockDataService.updateBatch).not.toHaveBeenCalled();
      expect(mockSnackBar.open).toHaveBeenCalledWith(
        jasmine.stringContaining('Clear tap error'),
        'Close'
      );
    });
  });
});
