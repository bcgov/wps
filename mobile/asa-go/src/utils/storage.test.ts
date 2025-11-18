
import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import { DateTime } from 'luxon';
import {
  getPath,
  writeToFileSystem,
  readFromFilesystem,
  clearStaleHFIPMTiles,
  CacheableDataType,
  CacheableData,
} from '@/utils/storage'; // adjust path as needed

vi.mock("@capacitor/filesystem", () => ({
  Filesystem: {
    readFile: vi.fn(),
    writeFile: vi.fn(),
    readdir: vi.fn(),
    deleteFile: vi.fn()
  },
  Directory: { Data: "DATA" },
  Encoding: { UTF8: "utf8" },
}));
import { Directory, Encoding, Filesystem} from '@capacitor/filesystem';
import { FireShapeArea, RunType } from '@/api/fbaAPI';

const mockData: FireShapeArea[] = []
const mockCacheableData: CacheableData<CacheableDataType> = {
    "2025-08-25": {
      runParameter: {
        for_date: "2025-08-25",
        run_datetime: "2025-08-24",
        run_type: RunType.FORECAST
      },
      data: mockData
    }
  }
  const mockFileData = { "data": mockCacheableData }
  const mockReadFileResult = {
    data: JSON.stringify(mockFileData)
  }

describe('Storage utils', () => {
  const key = 'testKey';
  const date = DateTime.fromISO('2025-08-26');

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('getPath returns correct path with date', () => {
    const path = getPath(key, date);
    expect(path).toBe('_asa_go_testKey_2025-08-26.json');
  });

  it('getPath returns correct path without date', () => {
    const path = getPath(key);
    expect(path).toBe('_asa_go_testKey.json');
  });

  it('writeToFileSystem writes data correctly', async () => {
    await writeToFileSystem(Filesystem, key, mockCacheableData, date);

    expect(Filesystem.writeFile).toHaveBeenCalledWith({
      path: '_asa_go_testKey.json',
      data: expect.stringContaining('"lastUpdated":"2025-08-26T'),
      directory: Directory.Data,
      encoding: Encoding.UTF8,
    });
  });

  it('readFromFilesystem returns parsed data', async () => {
    (Filesystem.readFile as Mock).mockResolvedValue(mockReadFileResult);

    const result = await readFromFilesystem(Filesystem, key);
    expect(result).toEqual(mockFileData);
    expect(Filesystem.readFile).toHaveBeenCalledWith({
      path: '_asa_go_testKey.json',
      directory: Directory.Data,
      encoding: Encoding.UTF8,
    });
  });

  it('readFromFilesystem returns null on error', async () => {
    (Filesystem.readFile as Mock).mockRejectedValue(new Error('File not found'));

    const result = await readFromFilesystem(Filesystem, key);
    expect(result).toBeNull();
  });

  it('clearStaleHFIPMTiles deletes stale files', async () => {
    (Filesystem.readdir as Mock).mockResolvedValue({
      files: [
        { name: '2025-08-25.hfi.pmtiles' },
        { name: '2025-08-26.hfi.pmtiles' },
        { name: 'otherfile.json' },
      ],
    });

    await clearStaleHFIPMTiles(Filesystem, ['2025-08-26.hfi.pmtiles']);

    expect(Filesystem.deleteFile).toHaveBeenCalledTimes(1);
    expect(Filesystem.deleteFile).toHaveBeenCalledWith({
      path: '2025-08-25.hfi.pmtiles',
      directory: Directory.Data,
    });
  });
});

