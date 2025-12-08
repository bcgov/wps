import {
  FireCenter,
  FireShapeStatusDetail,
  FireZoneHFIStatsDictionary,
  FireZoneStatus,
  FireZoneTPIStats,
  RunParameter,
} from "@/api/fbaAPI";
import { Directory, Encoding, FilesystemPlugin } from "@capacitor/filesystem";
import { DateTime } from "luxon";

export type CacheableDataType =
  | FireShapeStatusDetail[]
  | FireZoneStatus[]
  | FireZoneTPIStats[]
  | FireZoneHFIStatsDictionary;

export type CacheableData<T extends CacheableDataType> = {
  [key: string]: {
    runParameter: RunParameter;
    data: T;
  };
};

type Cacheable = FireCenter[] | { [key: string]: RunParameter };

// Type returned by readFromFilesystem function
export type CachedData<T extends CacheableData<CacheableDataType> | Cacheable> =
  {
    lastUpdated: string;
    data: T;
  };

const CACHE_KEY = "_asa_go";
export const FIRE_CENTERS_KEY = "fireCenters";
export const HFI_STATS_KEY = "hfiStats";
export const PROVINCIAL_SUMMARY_KEY = "provincialSummary";
export const RUN_PARAMETERS_CACHE_KEY = "runParameters";
export const TPI_STATS_KEY = "tpiStats";
export const FIRE_CENTERS_CACHE_EXPIRATION = 12;

export const getPath = (key: string, date?: DateTime): string => {
  if (date) {
    return `${CACHE_KEY}_${key}_${date.toISODate()}.json`;
  }
  return `${CACHE_KEY}_${key}.json`;
};

export const writeToFileSystem = async (
  filesystem: FilesystemPlugin,
  key: string,
  data: CacheableData<CacheableDataType> | Cacheable,
  lastUpdated: DateTime
) => {
  await filesystem.writeFile({
    path: getPath(key),
    data: JSON.stringify({ data, lastUpdated: lastUpdated.toISO() }),
    directory: Directory.Data,
    encoding: Encoding.UTF8,
  });
};

export const readFromFilesystem = async (
  filesystem: FilesystemPlugin,
  key: string
): Promise<CachedData<CacheableData<CacheableDataType> | Cacheable> | null> => {
  try {
    const result = await filesystem.readFile({
      path: getPath(key),
      directory: Directory.Data,
      encoding: Encoding.UTF8,
    });
    return JSON.parse(result.data as string);
  } catch {
    return null;
  }
};

export const clearStaleHFIPMTiles = async (
  filesystem: FilesystemPlugin,
  hfiFilesToKeep: string[]
) => {
  try {
    const { files } = await filesystem.readdir({
      path: "",
      directory: Directory.Data,
    });
    for (const file of files) {
      if (
        file.name.endsWith("hfi.pmtiles") &&
        !hfiFilesToKeep.includes(file.name)
      ) {
        await filesystem.deleteFile({
          path: file.name,
          directory: Directory.Data,
        });
      }
    }
  } catch (e) {
    console.error(e);
  }
};
