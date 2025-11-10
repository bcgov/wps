import { RunType } from "@/api/fbaAPI";
import { fetchHFIPMTiles, fetchStaticPMTiles } from "@/api/pmtilesAPI";
import {
  Directory,
  Encoding,
  FilesystemPlugin,
  ReadFileResult,
} from "@capacitor/filesystem";
import { DateTime } from "luxon";
import { FileSource, PMTiles } from "pmtiles";

const base64ToBlob = (
  base64: string,
  contentType = "application/octet-stream"
) => {
  const byteCharacters = atob(base64.split(",")[1]); // Remove Base64 prefix
  const byteNumbers = new Array(byteCharacters.length)
    .fill(0)
    .map((_, i) => byteCharacters.charCodeAt(i));
  const byteArray = new Uint8Array(byteNumbers);
  return new Blob([byteArray], { type: contentType });
};

const blobToBase64 = async (blob: Blob): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(blob);
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = reject;
  });
};

const serialize = async (blob: Blob) => {
  // Mobile devices require string data
  const base64Data = await blobToBase64(blob);
  return base64Data;
};

const deserialize = (text: string): Blob => {
  return base64ToBlob(text);
};

const toPMTiles = (file: ReadFileResult, filename: string) => {
  const deserialized = deserialize(file.data as string);

  // Initialize PMTiles with local blob
  const pmtiles = new PMTiles(
    new FileSource(new File([deserialized], filename))
  );
  return pmtiles;
};

const fetchAndStoreStaticPMTiles = (
  filename: string,
  fileSystem: FilesystemPlugin
) => {
  return async () => {
    try {
      const blob = await fetchStaticPMTiles(filename);
      const serialized = await serialize(blob);

      await fileSystem.writeFile({
        path: filename,
        data: serialized,
        directory: Directory.Data,
        encoding: Encoding.UTF8,
      });

      const file = await fileSystem.readFile({
        path: filename,
        directory: Directory.Data,
        encoding: Encoding.UTF8,
      });

      return toPMTiles(file, filename);
    } catch (error) {
      console.error("Error storing PMTiles:", error);
    }
  };
};

const fetchAndStoreHFIPMTiles = (
  for_date: DateTime,
  run_type: RunType,
  run_date: DateTime,
  filename: string,
  fileSystem: FilesystemPlugin
) => {
  return async () => {
    try {
      const blob = await fetchHFIPMTiles(for_date, run_type, run_date);
      const serialized = await serialize(blob);

      await fileSystem.writeFile({
        path: filename,
        data: serialized,
        directory: Directory.Data,
        encoding: Encoding.UTF8,
      });

      const file = await fileSystem.readFile({
        path: filename,
        directory: Directory.Data,
        encoding: Encoding.UTF8,
      });

      return toPMTiles(file, filename);
    } catch (error) {
      console.error("Error storing PMTiles:", error);
    }
  };
};

export interface IPMTilesCache {
  loadPMTiles: (
    filename: string,
    fetchAndStoreCallback?: () => Promise<PMTiles | undefined>
  ) => Promise<PMTiles | undefined>;
  loadHFIPMTiles: (
    for_date: DateTime,
    run_type: RunType,
    run_date: DateTime,
    filename: string
  ) => Promise<PMTiles | undefined>;
}

export class PMTilesCache implements IPMTilesCache {
  constructor(
    private readonly fileSystem: FilesystemPlugin,
    private retries: number = 3
  ) {}
  public readonly loadPMTiles = async (
    filename: string,
    fetchAndStoreCallback?: () => Promise<PMTiles | undefined>
  ) => {
    const fetchAndStore =
      fetchAndStoreCallback ??
      fetchAndStoreStaticPMTiles(filename, this.fileSystem);
    try {
      const file = await this.fileSystem.readFile({
        path: filename,
        directory: Directory.Data,
        encoding: Encoding.UTF8,
      });

      return toPMTiles(file, filename);
    } catch (e) {
      console.log("Error reading file, attempting to re-fetch", e);
      let retriesLeft = this.retries;
      while (retriesLeft-- > 0) {
        try {
          const pmTiles = await fetchAndStore();
          return pmTiles;
        } catch (error) {
          console.log(
            `Re-fetch attempted, ${retriesLeft + 1} retries left:`,
            error
          );
        }
      }
    }
  };

  public readonly loadHFIPMTiles = async (
    for_date: DateTime,
    run_type: RunType,
    run_date: DateTime,
    filename: string,
    fetchAndStoreCallback?: () => Promise<PMTiles | undefined>
  ) => {
    const cachedFilename = `${for_date.toISODate()}_${run_type}_${run_date.toISODate()}_${filename}`;
    const fetchAndStore =
      fetchAndStoreCallback ??
      fetchAndStoreHFIPMTiles(
        for_date,
        run_type,
        run_date,
        cachedFilename,
        this.fileSystem
      );
    return this.loadPMTiles(cachedFilename, fetchAndStore);
  };
}
