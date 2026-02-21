import { DndDirective } from './dnd.directive';

describe('DndDirective', () => {
  let directive: DndDirective;

  beforeEach(() => {
    directive = new DndDirective();
  });

  it('should create an instance', () => {
    expect(directive).toBeTruthy();
  });

  describe('default values', () => {
    it('should have disabled default to false', () => {
      expect(directive.disabled).toBe(false);
    });

    it('should have fileOver default to false', () => {
      expect(directive.fileOver).toBe(false);
    });

    it('should have fileDropped EventEmitter', () => {
      expect(directive.fileDropped).toBeTruthy();
    });
  });

  describe('onDragOver', () => {
    it('should set fileOver to true when not disabled', () => {
      const event = createMockEvent();
      directive.onDragOver(event);

      expect(directive.fileOver).toBe(true);
    });

    it('should not set fileOver to true when disabled', () => {
      directive.disabled = true;
      const event = createMockEvent();
      directive.onDragOver(event);

      expect(directive.fileOver).toBe(false);
    });

    it('should call preventDefault on event', () => {
      const event = createMockEvent();
      directive.onDragOver(event);

      expect(event.preventDefault).toHaveBeenCalled();
    });

    it('should call stopPropagation on event', () => {
      const event = createMockEvent();
      directive.onDragOver(event);

      expect(event.stopPropagation).toHaveBeenCalled();
    });
  });

  describe('onDragLeave', () => {
    it('should set fileOver to false', () => {
      directive.fileOver = true;
      const event = createMockEvent();
      directive.onDragLeave(event);

      expect(directive.fileOver).toBe(false);
    });

    it('should call preventDefault on event', () => {
      const event = createMockEvent();
      directive.onDragLeave(event);

      expect(event.preventDefault).toHaveBeenCalled();
    });

    it('should call stopPropagation on event', () => {
      const event = createMockEvent();
      directive.onDragLeave(event);

      expect(event.stopPropagation).toHaveBeenCalled();
    });
  });

  describe('ondrop', () => {
    it('should set fileOver to false', () => {
      directive.fileOver = true;
      const event = createDropEvent([new File([''], 'test.png')]);
      directive.ondrop(event);

      expect(directive.fileOver).toBe(false);
    });

    it('should call preventDefault on event', () => {
      const event = createDropEvent([new File([''], 'test.png')]);
      directive.ondrop(event);

      expect(event.preventDefault).toHaveBeenCalled();
    });

    it('should call stopPropagation on event', () => {
      const event = createDropEvent([new File([''], 'test.png')]);
      directive.ondrop(event);

      expect(event.stopPropagation).toHaveBeenCalled();
    });

    it('should emit fileDropped when files are present', () => {
      const files = [new File([''], 'test.png')];
      const event = createDropEvent(files);
      spyOn(directive.fileDropped, 'emit');

      directive.ondrop(event);

      expect(directive.fileDropped.emit).toHaveBeenCalled();
    });

    it('should not emit fileDropped when no files are present', () => {
      const event = createDropEvent([]);
      spyOn(directive.fileDropped, 'emit');

      directive.ondrop(event);

      expect(directive.fileDropped.emit).not.toHaveBeenCalled();
    });

    it('should emit files from dataTransfer', () => {
      const files = [
        new File(['content1'], 'test1.png', { type: 'image/png' }),
        new File(['content2'], 'test2.png', { type: 'image/png' }),
      ];
      const event = createDropEvent(files);
      let emittedFiles: FileList | null = null;
      directive.fileDropped.subscribe((f: FileList) => (emittedFiles = f));

      directive.ondrop(event);

      expect(emittedFiles).toBeTruthy();
      expect((emittedFiles as any).length).toBe(2);
    });
  });

  describe('disabled state', () => {
    it('should accept disabled input', () => {
      directive.disabled = true;
      expect(directive.disabled).toBe(true);
    });

    it('should not highlight when disabled and dragging over', () => {
      directive.disabled = true;
      directive.onDragOver(createMockEvent());

      expect(directive.fileOver).toBe(false);
    });

    it('should still reset fileOver on drag leave even when disabled', () => {
      directive.fileOver = true;
      directive.disabled = true;
      directive.onDragLeave(createMockEvent());

      expect(directive.fileOver).toBe(false);
    });
  });
});

function createMockEvent(): any {
  return {
    preventDefault: jasmine.createSpy('preventDefault'),
    stopPropagation: jasmine.createSpy('stopPropagation'),
  };
}

function createDropEvent(files: File[]): any {
  const fileList = {
    length: files.length,
    item: (index: number) => files[index],
  };

  // Add index accessors
  files.forEach((file, index) => {
    (fileList as any)[index] = file;
  });

  return {
    preventDefault: jasmine.createSpy('preventDefault'),
    stopPropagation: jasmine.createSpy('stopPropagation'),
    dataTransfer: {
      files: fileList,
    },
  };
}
