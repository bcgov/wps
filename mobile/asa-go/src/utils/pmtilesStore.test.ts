import type { FilesystemPlugin } from '@capacitor/filesystem'
import { DateTime, Settings } from 'luxon'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { RunType } from '@/api/fbaAPI'
import { PMTilesStore } from '@/utils/pmtilesStore'

const { mockGetHeader } = vi.hoisted(() => ({
  mockGetHeader: vi.fn()
}))

vi.mock('pmtiles', () => {
  class FileSource {
    constructor(readonly file: File) {}
  }

  class PMTiles {
    constructor(readonly source: FileSource) {}

    getHeader() {
      return mockGetHeader(this.source.file)
    }
  }

  return { FileSource, PMTiles }
})

const buildFilesystem = () =>
  ({
    stat: vi.fn(),
    readFile: vi.fn(),
    writeFile: vi.fn()
  }) as unknown as FilesystemPlugin

describe('PMTilesStore', () => {
  beforeEach(() => {
    mockGetHeader.mockReset()
    mockGetHeader.mockResolvedValue({})
    Settings.defaultZone = 'system'
  })

  it('opens and validates a stored archive', async () => {
    const fileSystem = buildFilesystem()
    vi.mocked(fileSystem.readFile).mockResolvedValue({ data: btoa('stored archive') })
    const store = new PMTilesStore(fileSystem)

    const archive = await store.openPMTiles('test.pmtiles')
    const reader = archive.createReader()
    const freshReader = archive.createReader()
    const file = (reader.source as unknown as { file: File }).file

    expect(await file.text()).toBe('stored archive')
    expect(freshReader).not.toBe(reader)
    expect((freshReader.source as unknown as { file: File }).file).toBe(file)
    expect(fileSystem.readFile).toHaveBeenCalledOnce()
    expect(fileSystem.writeFile).not.toHaveBeenCalled()
    expect(mockGetHeader).toHaveBeenCalledOnce()
  })

  it('reads archives written by the previous UTF-8 cache', async () => {
    const fileSystem = buildFilesystem()
    const previousDataUrl = `data:application/octet-stream;base64,${btoa('legacy archive')}`
    vi.mocked(fileSystem.readFile).mockResolvedValue({ data: btoa(previousDataUrl) })
    const store = new PMTilesStore(fileSystem)

    const archive = await store.openPMTiles('test.pmtiles')
    const file = (archive.createReader().source as unknown as { file: File }).file

    expect(await file.text()).toBe('legacy archive')
  })

  it('downloads, validates, and stores missing archives as binary', async () => {
    const fileSystem = buildFilesystem()
    vi.mocked(fileSystem.readFile).mockRejectedValueOnce(new Error('File missing'))
    const fetchPMTiles = vi.fn().mockResolvedValue(new Blob(['downloaded archive']))
    const store = new PMTilesStore(fileSystem)

    await store.openPMTiles('test.pmtiles', fetchPMTiles)

    expect(fetchPMTiles).toHaveBeenCalledOnce()
    expect(fileSystem.writeFile).toHaveBeenCalledWith({
      path: 'test.pmtiles',
      data: btoa('downloaded archive'),
      directory: 'DATA'
    })
    expect(mockGetHeader).toHaveBeenCalledOnce()
  })

  it('replaces a stored archive that fails validation', async () => {
    const fileSystem = buildFilesystem()
    vi.mocked(fileSystem.readFile).mockResolvedValueOnce({ data: btoa('corrupt archive') })
    mockGetHeader.mockRejectedValueOnce(new Error('Invalid header')).mockResolvedValue({})
    const fetchPMTiles = vi.fn().mockResolvedValue(new Blob(['valid archive']))
    const store = new PMTilesStore(fileSystem)

    await store.openPMTiles('test.pmtiles', fetchPMTiles)

    expect(fetchPMTiles).toHaveBeenCalledOnce()
    expect(fileSystem.writeFile).toHaveBeenCalledOnce()
  })

  it('preloads an existing archive without reading it into memory', async () => {
    const fileSystem = buildFilesystem()
    vi.mocked(fileSystem.stat).mockResolvedValue({
      type: 'file',
      size: 1,
      mtime: 0,
      uri: '',
      name: 'test.pmtiles'
    })
    const store = new PMTilesStore(fileSystem)

    await store.ensurePMTiles('test.pmtiles')

    expect(fileSystem.stat).toHaveBeenCalledOnce()
    expect(fileSystem.readFile).not.toHaveBeenCalled()
    expect(fileSystem.writeFile).not.toHaveBeenCalled()
  })

  it('shares an in-flight download and clears it after failure', async () => {
    const fileSystem = buildFilesystem()
    vi.mocked(fileSystem.stat).mockRejectedValue(new Error('File missing'))
    let rejectDownload!: (error: Error) => void
    const pendingDownload = new Promise<Blob>((_, reject) => {
      rejectDownload = reject
    })
    const fetchPMTiles = vi
      .fn()
      .mockReturnValueOnce(pendingDownload)
      .mockResolvedValueOnce(new Blob(['archive']))
    const store = new PMTilesStore(fileSystem)

    const firstEnsure = store.ensurePMTiles('test.pmtiles', fetchPMTiles)
    const secondEnsure = store.ensurePMTiles('test.pmtiles', fetchPMTiles)
    await vi.waitFor(() => expect(fetchPMTiles).toHaveBeenCalledOnce())
    rejectDownload(new Error('Download failed'))

    await expect(firstEnsure).rejects.toThrow('Download failed')
    await expect(secondEnsure).rejects.toThrow('Download failed')
    await store.ensurePMTiles('test.pmtiles', fetchPMTiles)

    expect(fetchPMTiles).toHaveBeenCalledTimes(2)
  })

  it('times out a stalled download and allows the next open to retry', async () => {
    vi.useFakeTimers()
    try {
      const fileSystem = buildFilesystem()
      vi.mocked(fileSystem.readFile).mockRejectedValue(new Error('File missing'))
      const stalledDownload = new Promise<Blob>(() => {})
      const fetchPMTiles = vi
        .fn()
        .mockReturnValueOnce(stalledDownload)
        .mockResolvedValueOnce(new Blob(['downloaded archive']))
      const store = new PMTilesStore(fileSystem)

      const firstOpen = store.openPMTiles('test.pmtiles', fetchPMTiles)
      const firstOpenResult = expect(firstOpen).rejects.toThrow('Timed out downloading test.pmtiles')
      await vi.advanceTimersByTimeAsync(30_000)
      await firstOpenResult

      vi.useRealTimers()
      await store.openPMTiles('test.pmtiles', fetchPMTiles)

      expect(fetchPMTiles).toHaveBeenCalledTimes(2)
    } finally {
      vi.useRealTimers()
    }
  })

  it('uses the ASA Go timezone for HFI filenames', async () => {
    Settings.defaultZone = 'Pacific/Auckland'
    const fileSystem = buildFilesystem()
    vi.mocked(fileSystem.stat).mockResolvedValue({
      type: 'file',
      size: 1,
      mtime: 0,
      uri: '',
      name: 'hfi.pmtiles'
    })
    const store = new PMTilesStore(fileSystem)

    await store.ensureHFIPMTiles(
      DateTime.fromISO('2025-08-27'),
      RunType.FORECAST,
      DateTime.fromISO('2025-08-27T15:30:00Z'),
      'hfi.pmtiles'
    )

    expect(fileSystem.stat).toHaveBeenCalledWith({
      path: '2025-08-27_FORECAST_2025-08-27_hfi.pmtiles',
      directory: 'DATA'
    })
  })
})
