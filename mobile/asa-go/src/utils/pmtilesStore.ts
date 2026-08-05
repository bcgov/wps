import { Directory, Filesystem, type FilesystemPlugin, type ReadFileResult } from '@capacitor/filesystem'
import type { DateTime } from 'luxon'
import { FileSource, PMTiles } from 'pmtiles'
import type { RunType } from '@/api/fbaAPI'
import { fetchHFIPMTiles, fetchStaticPMTiles } from '@/api/pmtilesAPI'
import { getHFIRunDateKey } from '@/utils/pmtilesUtils'

type FetchPMTiles = (signal: AbortSignal) => Promise<Blob>

const FILE_OPERATION_TIMEOUT_MS = 10_000
const DOWNLOAD_TIMEOUT_MS = 30_000

// keep native filesystem and download promises from blocking later recovery indefinitely
const settleWithin = async <T>(operation: Promise<T>, timeoutMs: number, message: string, onTimeout?: () => void) => {
  let timeoutId: ReturnType<typeof setTimeout> | undefined
  const timeout = new Promise<never>((_, reject) => {
    timeoutId = setTimeout(() => {
      onTimeout?.()
      reject(new Error(message))
    }, timeoutMs)
  })

  try {
    return await Promise.race([operation, timeout])
  } finally {
    if (timeoutId) {
      clearTimeout(timeoutId)
    }
  }
}

const binaryStringToBytes = (value: string) => {
  const bytes = new Uint8Array(value.length)
  for (let index = 0; index < value.length; index += 1) {
    bytes[index] = value.charCodeAt(index)
  }
  return bytes
}

const dataUrlToBlob = (dataUrl: string) => {
  const separatorIndex = dataUrl.indexOf(',')
  if (separatorIndex === -1) {
    throw new Error('Invalid PMTiles data URL')
  }
  const binary = atob(dataUrl.slice(separatorIndex + 1))
  return new Blob([binaryStringToBytes(binary)], { type: 'application/octet-stream' })
}

const storedFileToBlob = (file: ReadFileResult) => {
  if (file.data instanceof Blob) {
    return file.data
  }

  const binary = atob(file.data)
  // support files written by the previous cache, which stored a data URL as UTF-8 text
  if (binary.startsWith('data:')) {
    return dataUrlToBlob(binary)
  }
  return new Blob([binaryStringToBytes(binary)], { type: 'application/octet-stream' })
}

const blobToBase64 = async (blob: Blob) =>
  new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.readAsDataURL(blob)
    reader.onload = () => resolve((reader.result as string).split(',')[1])
    reader.onerror = reject
  })

/**
 * holds one decoded archive file and creates disposable PMTiles readers from it.
 * each fresh reader gets an independent PMTiles header and directory promise cache.
 */
export class PMTilesArchive {
  private validatedReader?: PMTiles

  constructor(private readonly file: File) {}

  createReader() {
    if (this.validatedReader) {
      const reader = this.validatedReader
      this.validatedReader = undefined
      return reader
    }
    return new PMTiles(new FileSource(this.file))
  }

  async validate() {
    const reader = new PMTiles(new FileSource(this.file))
    await reader.getHeader()
    // reuse the validated reader for the first consumer so the header is not read twice
    this.validatedReader = reader
  }
}

/**
 * owns persistent PMTiles files and the downloads needed to populate them.
 * reader lifetime and OpenLayers tile caching intentionally live outside this store.
 */
export class PMTilesStore {
  private readonly pendingDownloads = new Map<string, Promise<PMTilesArchive>>()

  constructor(private readonly fileSystem: FilesystemPlugin) {}

  /** ensures an archive exists for preloading without decoding a stored file into memory. */
  async ensurePMTiles(filename: string, fetchPMTiles: FetchPMTiles = signal => fetchStaticPMTiles(filename, signal)) {
    try {
      await settleWithin(
        this.fileSystem.stat({ path: filename, directory: Directory.Data }),
        FILE_OPERATION_TIMEOUT_MS,
        `Timed out checking for ${filename}`
      )
    } catch {
      await this.downloadPMTiles(filename, fetchPMTiles)
    }
  }

  /** opens and validates an archive, replacing a missing or invalid stored file from the network. */
  async openPMTiles(filename: string, fetchPMTiles: FetchPMTiles = signal => fetchStaticPMTiles(filename, signal)) {
    try {
      return await this.readPMTiles(filename)
    } catch {
      return this.downloadPMTiles(filename, fetchPMTiles)
    }
  }

  async ensureHFIPMTiles(forDate: DateTime, runType: RunType, runDate: DateTime, filename: string) {
    const cachedFilename = this.getHFICachedFileName(forDate, runType, runDate, filename)
    await this.ensurePMTiles(cachedFilename, signal => fetchHFIPMTiles(forDate, runType, runDate, signal))
  }

  async openHFIPMTiles(forDate: DateTime, runType: RunType, runDate: DateTime, filename: string) {
    const cachedFilename = this.getHFICachedFileName(forDate, runType, runDate, filename)
    return this.openPMTiles(cachedFilename, signal => fetchHFIPMTiles(forDate, runType, runDate, signal))
  }

  private async readPMTiles(filename: string) {
    return settleWithin(
      this.readAndValidatePMTiles(filename),
      FILE_OPERATION_TIMEOUT_MS,
      `Timed out reading ${filename}`
    )
  }

  private async readAndValidatePMTiles(filename: string) {
    const file = await this.fileSystem.readFile({
      path: filename,
      directory: Directory.Data
    })
    const archive = new PMTilesArchive(new File([storedFileToBlob(file)], filename))
    await archive.validate()
    return archive
  }

  private async downloadPMTiles(filename: string, fetchPMTiles: FetchPMTiles) {
    // share downloads only; archive reads and PMTiles readers remain independent
    const pendingDownload = this.pendingDownloads.get(filename)
    if (pendingDownload) {
      return pendingDownload
    }

    const download = this.fetchValidateAndStore(filename, fetchPMTiles)
    this.pendingDownloads.set(filename, download)
    try {
      return await download
    } finally {
      if (this.pendingDownloads.get(filename) === download) {
        this.pendingDownloads.delete(filename)
      }
    }
  }

  private async fetchValidateAndStore(filename: string, fetchPMTiles: FetchPMTiles) {
    const abortController = new AbortController()
    return settleWithin(
      this.fetchValidateAndStorePMTiles(filename, fetchPMTiles, abortController.signal),
      DOWNLOAD_TIMEOUT_MS,
      `Timed out downloading ${filename}`,
      () => abortController.abort()
    )
  }

  private async fetchValidateAndStorePMTiles(filename: string, fetchPMTiles: FetchPMTiles, signal: AbortSignal) {
    const blob = await fetchPMTiles(signal)
    const archive = new PMTilesArchive(new File([blob], filename))
    await archive.validate()

    // omit UTF-8 encoding so Capacitor persists the decoded binary rather than base64 text
    await this.fileSystem.writeFile({
      path: filename,
      data: await blobToBase64(blob),
      directory: Directory.Data
    })
    return archive
  }

  readonly getHFICachedFileName = (forDate: DateTime, runType: string, runDate: DateTime, filename: string) =>
    this.getHFIFileName(forDate.toISODate()!, runType, getHFIRunDateKey(runDate), filename)

  readonly getHFIFileName = (forDate: string, runType: string, runDate: string, filename: string) =>
    `${forDate}_${runType}_${runDate}_${filename}`
}

export const pmtilesStore = new PMTilesStore(Filesystem)
