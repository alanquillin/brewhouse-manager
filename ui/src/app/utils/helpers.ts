import * as _ from "lodash";

export function deepEqual(object1: any, object2: any): boolean {
    const keys1 = Object.keys(object1);
    const keys2 = Object.keys(object2);
    if (keys1.length !== keys2.length) {
      return false;
    }
    for (const key of keys1) {
      const val1 = object1[key];
      const val2 = object2[key];
      const areObjects = isObject(val1) && isObject(val2);
      if (
        areObjects && !deepEqual(val1, val2) ||
        !areObjects && val1 !== val2
      ) {
        return false;
      }
    }
    return true;
  }

  export function isObject(object: any): boolean {
    return object != null && typeof object === 'object';
  }

  export function isNilOrEmpty(val: any): boolean {
    if (_.isNil(val)){
      return true;
    }

    if (_.isBoolean(val)){
      return false;
    }

    if (_.isDate(val)) {
      return _.isEqual(new Date(), val);
    }

    if(_.isNumber(val)) {
      return _.isNaN(val);
    }

    return _.isEmpty(val);
  }

export function toBoolean(val: any) {
  if(_.isBoolean(val)){
    return val;
  }

  if(_.isString(val)) {
    val = _.toLower(val);
    return val === "true" || val !== "yes"
    
    val = _.toNumber(val);
  }

  if(_.isNumber(val)) {
    return val > 0;
  }

  return false;
}

export function openFullscreen(doc: Document) {
  // Trigger fullscreen
  const docElmWithBrowsersFullScreenFunctions = doc.documentElement as HTMLElement & {
    mozRequestFullScreen(): Promise<void>;
    webkitRequestFullscreen(): Promise<void>;
    msRequestFullscreen(): Promise<void>;
  };

  if (docElmWithBrowsersFullScreenFunctions.requestFullscreen) {
    docElmWithBrowsersFullScreenFunctions.requestFullscreen();
  } else if (docElmWithBrowsersFullScreenFunctions.mozRequestFullScreen) { /* Firefox */
    docElmWithBrowsersFullScreenFunctions.mozRequestFullScreen();
  } else if (docElmWithBrowsersFullScreenFunctions.webkitRequestFullscreen) { /* Chrome, Safari and Opera */
    docElmWithBrowsersFullScreenFunctions.webkitRequestFullscreen();
  } else if (docElmWithBrowsersFullScreenFunctions.msRequestFullscreen) { /* IE/Edge */
    docElmWithBrowsersFullScreenFunctions.msRequestFullscreen();
  }
}

export function closeFullscreen(doc: Document){
  const docWithBrowsersExitFunctions = doc as Document & {
    mozCancelFullScreen(): Promise<void>;
    webkitExitFullscreen(): Promise<void>;
    msExitFullscreen(): Promise<void>;
  };
  if (docWithBrowsersExitFunctions.exitFullscreen) {
    docWithBrowsersExitFunctions.exitFullscreen();
  } else if (docWithBrowsersExitFunctions.mozCancelFullScreen) { /* Firefox */
    docWithBrowsersExitFunctions.mozCancelFullScreen();
  } else if (docWithBrowsersExitFunctions.webkitExitFullscreen) { /* Chrome, Safari and Opera */
    docWithBrowsersExitFunctions.webkitExitFullscreen();
  } else if (docWithBrowsersExitFunctions.msExitFullscreen) { /* IE/Edge */
    docWithBrowsersExitFunctions.msExitFullscreen();
  }
}