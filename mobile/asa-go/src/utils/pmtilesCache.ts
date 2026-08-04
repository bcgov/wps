import { Directory, Encoding, Filesystem, type FilesystemPlugin, type ReadFileResult } from '@capacitor/filesystem'
import type { DateTime } from 'luxon'
import { FileSource, PMTiles } from 'pmtiles'
import type { RunType } from '@/api/fbaAPI'
import { fetchHFIPMTiles, fetchStaticPMTiles } from '@/api/pmtilesAPI'
import { getHFIRunDateKey } from '@/utils/pmtilesUtils'

const base64ToBlob = (base64: string, contentType = 'application/octet-stream') => {
  const byteCharacters = atob(base64.split(',')[1]) // Remove Base64 prefix
  const byteNumbers = new Array(byteCharacters.length).fill(0).map((_, i) => byteCharacters.charCodeAt(i))
  const byteArray = new Uint8Array(byteNumbers)
  return new Blob([byteArray], { type: contentType })
}

const blobToBase64 = async (blob: Blob): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.readAsDataURL(blob)
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = reject
  })
}

const serialize = async (blob: Blob) => {
  // Mobile devices require string data
  const base64Data = await blobToBase64(blob)
  return base64Data
}

const deserialize = (text: string): Blob => {
  return base64ToBlob(text)
}

const toPMTiles = (file: ReadFileResult, filename: string) => {
  const deserialized = deserialize(file.data as string)

  // Initialize PMTiles with local blob
  const pmtiles = new PMTiles(new FileSource(new File([deserialized], filename)))
  return pmtiles
}

const fetchAndStorePMTiles = async (
  filename: string,
  fileSystem: FilesystemPlugin,
  fetchPMTiles: () => Promise<Blob>
) => {
  const blob = await fetchPMTiles()
  const serialized = await serialize(blob)

  await fileSystem.writeFile({
    path: filename,
    data: serialized,
    directory: Directory.Data,
    encoding: Encoding.UTF8
  })

  const file = await fileSystem.readFile({
    path: filename,
    directory: Directory.Data,
    encoding: Encoding.UTF8
  })

  return toPMTiles(file, filename)
}

export class PMTilesCache {
  private readonly pendingLoads = new Map<string, Promise<PMTiles>>()

  constructor(
    private readonly fileSystem: FilesystemPlugin,
    private retries: number = 3
  ) {}

  public readonly loadPMTiles = (filename: string, fetchAndStoreCallback?: () => Promise<PMTiles>) => {
    const pendingLoad = this.pendingLoads.get(filename)
    if (pendingLoad) {
      return pendingLoad
    }

    // share an in-flight read so preloading and map setup cannot write the same file concurrently
    const load = this.loadPMTilesFromStorage(filename, fetchAndStoreCallback).finally(() => {
      this.pendingLoads.delete(filename)
    })
    this.pendingLoads.set(filename, load)
    return load
  }

  private readonly loadPMTilesFromStorage = async (
    filename: string,
    fetchAndStoreCallback?: () => Promise<PMTiles>
  ) => {
    const fetchAndStore =
      fetchAndStoreCallback ??
      (() => fetchAndStorePMTiles(filename, this.fileSystem, () => fetchStaticPMTiles(filename)))
    let lastError: unknown
    try {
      const file = await this.fileSystem.readFile({
        path: filename,
        directory: Directory.Data,
        encoding: Encoding.UTF8
      })

      return toPMTiles(file, filename)
    } catch (e) {
      lastError = e
      console.log('Error reading file, attempting to re-fetch', e)
      for (let attempt = 1; attempt <= this.retries; attempt += 1) {
        try {
          return await fetchAndStore()
        } catch (error) {
          lastError = error
          console.log(`Re-fetch failed, ${this.retries - attempt} retries left:`, error)
        }
      }
    }
    throw lastError
  }

  public readonly loadHFIPMTiles = async (
    for_date: DateTime,
    run_type: RunType,
    run_date: DateTime,
    filename: string,
    fetchAndStoreCallback?: () => Promise<PMTiles>
  ) => {
    const cachedFilename = this.getHFICachedFileName(for_date, run_type, run_date, filename)
    const fetchAndStore =
      fetchAndStoreCallback ??
      (() => fetchAndStorePMTiles(cachedFilename, this.fileSystem, () => fetchHFIPMTiles(for_date, run_type, run_date)))
    return this.loadPMTiles(cachedFilename, fetchAndStore)
  }

  public readonly getHFICachedFileName = (for_date: DateTime, run_type: string, run_date: DateTime, filename: string) =>
    this.getHFIFileName(for_date.toISODate()!, run_type, getHFIRunDateKey(run_date), filename)

  public readonly getHFIFileName = (for_date: string, run_type: string, run_date: string, filename: string) => {
    return `${for_date}_${run_type}_${run_date}_${filename}`
  }
}

export const pmtilesCache = new PMTilesCache(Filesystem)
