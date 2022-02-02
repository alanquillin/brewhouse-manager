export class ExtendedFile extends File {
    progress: number = 0;
    path:string | undefined;
    hasError: boolean = false
    errorMessage: string | undefined
  }