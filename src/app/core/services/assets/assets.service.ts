import {Injectable} from '@angular/core';

/**
 * Service for loading bundled assets from the local assets folder.
 * All models are now bundled with the app for offline use.
 */

export type AssetState = {
  name?: string;
  label?: string;
  path: string;
  exists: boolean;
  size?: number;
  progress?: number;
  modified?: Date;
  children?: AssetState[];
};

// Known bundled model directories and their files
const BUNDLED_MODELS: {[path: string]: string[]} = {
  'models/browsermt/spoken-to-signed/spoken-signed/': [
    'lex.50.50.spokensigned.s2t.bin',
    'model.spokensigned.intgemm.alphas.bin',
    'vocab.spokensigned.spm',
  ],
};

@Injectable({
  providedIn: 'root',
})
export class AssetsService {
  stat(path: string): AssetState {
    if (path.endsWith('/')) {
      const files = BUNDLED_MODELS[path];
      if (!files) {
        return {path, exists: false, children: []};
      }
      return {
        path,
        exists: true,
        children: files.map(f => ({path: path + f, exists: true})),
      };
    }

    // Check if the file is part of a known bundled model
    for (const [dir, files] of Object.entries(BUNDLED_MODELS)) {
      if (path.startsWith(dir)) {
        const fileName = path.replace(dir, '');
        if (files.includes(fileName)) {
          return {path, exists: true};
        }
      }
    }

    return {path, exists: false};
  }

  async getDirectory(path: string): Promise<Map<string, string>> {
    if (!path.endsWith('/')) {
      throw new Error('Directory path must end with /');
    }

    const files = BUNDLED_MODELS[path];
    if (!files) {
      throw new Error(`Unknown model directory: ${path}`);
    }

    const map = new Map<string, string>();
    for (const file of files) {
      map.set(file, `assets/${path}${file}`);
    }
    return map;
  }

  async download(path: string): Promise<string | Map<string, string>> {
    if (path.endsWith('/')) {
      return this.getDirectory(path);
    }
    return `assets/${path}`;
  }
}
