import {
  type Cache,
  Compression,
  type DecompressFunc,
  type Header,
  type PMTiles,
  type RangeResponse,
  type Source,
  TileType
} from 'pmtiles'
import sinon from 'sinon'
import { assert, vi } from 'vitest'
import type { PMTilesArchive } from '@/utils/pmtilesStore'
import { PMTilesFileVectorSource } from '@/utils/pmtilesVectorSource'

const { mockCaptureException, mockSetContext } = vi.hoisted(() => ({
  mockCaptureException: vi.fn(),
  mockSetContext: vi.fn()
}))
vi.mock('@sentry/capacitor', () => ({
  captureException: mockCaptureException,
  withScope: (callback: (scope: { setContext: typeof mockSetContext }) => unknown) =>
    callback({ setContext: mockSetContext })
}))

const testPMTilesHeader: Header = {
  specVersion: 0,
  rootDirectoryOffset: 0,
  rootDirectoryLength: 0,
  jsonMetadataOffset: 0,
  jsonMetadataLength: 0,
  leafDirectoryOffset: 0,
  tileDataOffset: 0,
  numAddressedTiles: 0,
  numTileEntries: 0,
  numTileContents: 0,
  clustered: false,
  internalCompression: Compression.Unknown,
  tileCompression: Compression.Unknown,
  tileType: TileType.Unknown,
  minZoom: 0,
  maxZoom: 0,
  minLon: 0,
  minLat: 0,
  maxLon: 0,
  maxLat: 0,
  centerZoom: 0,
  centerLon: 0,
  centerLat: 0
}

class TestPMTiles implements PMTiles {
  source!: Source
  cache!: Cache
  decompress!: DecompressFunc

  getHeader(): Promise<Header> {
    return Promise.resolve(testPMTilesHeader)
  }

  getZxyAttempt(_z: number, _x: number, _y: number, _signal?: AbortSignal): Promise<RangeResponse | undefined> {
    return Promise.resolve(undefined)
  }

  getZxy(_z: number, _x: number, _y: number, _signal?: AbortSignal): Promise<RangeResponse | undefined> {
    return Promise.resolve(undefined)
  }

  getMetadataAttempt(): Promise<unknown> {
    return Promise.resolve()
  }

  getMetadata(): Promise<unknown> {
    return Promise.resolve()
  }

  getTileJson(_baseTilesUrl: string): Promise<unknown> {
    return Promise.resolve()
  }
}

class ErrorPMTiles extends TestPMTiles {
  getZxy(_z: number, _x: number, _y: number, _signal?: AbortSignal): Promise<RangeResponse | undefined> {
    return Promise.reject(new Error('Tile read failed'))
  }
}

class HangingPMTiles extends TestPMTiles {
  signal?: AbortSignal

  getZxy(_z: number, _x: number, _y: number, signal?: AbortSignal): Promise<RangeResponse | undefined> {
    this.signal = signal
    return new Promise(() => {})
  }
}

class DeferredErrorPMTiles extends TestPMTiles {
  rejectTile!: (error: Error) => void

  getZxy(_z: number, _x: number, _y: number, _signal?: AbortSignal): Promise<RangeResponse | undefined> {
    return new Promise((_, reject) => {
      this.rejectTile = reject
    })
  }
}

const buildArchive = (sandbox: sinon.SinonSandbox, ...readers: PMTiles[]) => {
  const createReader = sandbox.stub()
  readers.forEach((reader, index) => {
    createReader.onCall(index).returns(reader)
  })
  return {
    archive: { createReader } as unknown as PMTilesArchive,
    createReader
  }
}

const buildTile = (sandbox: sinon.SinonSandbox) => ({
  extent: undefined,
  projection: undefined,
  setFeatures: sandbox.stub(),
  setState: sandbox.stub()
})

describe('PMTilesFileVectorSource', () => {
  let sandbox: sinon.SinonSandbox

  beforeEach(() => {
    sandbox = sinon.createSandbox()
    mockCaptureException.mockClear()
    mockSetContext.mockClear()
  })

  afterEach(() => {
    sandbox.restore()
  })

  it('loads an archive and initializes the tile grid on creation', async () => {
    const { archive, createReader } = buildArchive(sandbox, new TestPMTiles())
    const loadArchive = sandbox.stub().resolves(archive)

    const instance = await PMTilesFileVectorSource.create({ filename: 'test.pmtiles' }, loadArchive)
    const tileGrid = instance.getTileGrid()

    sinon.assert.calledOnce(loadArchive)
    sinon.assert.calledOnce(createReader)
    assert(tileGrid !== null)
    assert(tileGrid.getMaxZoom() === testPMTilesHeader.maxZoom)
    assert(tileGrid.getMinZoom() === testPMTilesHeader.minZoom)
    assert(instance.getState() === 'ready')
  })

  it('creates a fresh reader and invalidates cached tiles on foreground', async () => {
    const { archive, createReader } = buildArchive(sandbox, new TestPMTiles(), new TestPMTiles())
    const loadArchive = sandbox.stub().resolves(archive)
    const instance = await PMTilesFileVectorSource.create({ filename: 'test.pmtiles' }, loadArchive)
    const refreshSpy = sandbox.spy(instance, 'refresh')

    await instance.refreshPMTiles()

    sinon.assert.calledOnce(loadArchive)
    sinon.assert.calledTwice(createReader)
    sinon.assert.calledOnce(refreshSpy)
    assert(instance.getUrls()?.[0] === 'pmtiles://{z}/{x}/{y}?reload=1')
  })

  it('reports at most one tile error until foregrounding creates a new reader', async () => {
    const { archive } = buildArchive(sandbox, new ErrorPMTiles(), new ErrorPMTiles())
    const instance = await PMTilesFileVectorSource.create({ filename: 'test.pmtiles' }, () => Promise.resolve(archive))
    const tile = buildTile(sandbox)

    instance.tileLoadFunction(tile as never, 'pmtiles://0/0/0')
    instance.tileLoadFunction(tile as never, 'pmtiles://0/0/0')
    await vi.waitFor(() => expect(mockCaptureException).toHaveBeenCalledOnce())

    await instance.refreshPMTiles()
    instance.tileLoadFunction(tile as never, 'pmtiles://0/0/0?reload=1')
    await vi.waitFor(() => expect(mockCaptureException).toHaveBeenCalledTimes(2))

    expect(mockSetContext).toHaveBeenLastCalledWith('pmtilesTile', {
      filename: 'test.pmtiles',
      z: 0,
      x: 0,
      y: 0,
      sourceState: 'ready'
    })
  })

  it('ignores a late tile failure from the reader replaced on foreground', async () => {
    const staleReader = new DeferredErrorPMTiles()
    const { archive } = buildArchive(sandbox, staleReader, new TestPMTiles())
    const instance = await PMTilesFileVectorSource.create({ filename: 'test.pmtiles' }, () => Promise.resolve(archive))
    const tile = buildTile(sandbox)

    instance.tileLoadFunction(tile as never, 'pmtiles://0/0/0')
    await instance.refreshPMTiles()
    staleReader.rejectTile(new Error('Stale tile failed'))
    await new Promise(resolve => setTimeout(resolve, 0))

    expect(mockCaptureException).not.toHaveBeenCalled()
  })

  it('retries archive loading on foreground after initialization fails', async () => {
    const { archive } = buildArchive(sandbox, new TestPMTiles())
    const loadArchive = sandbox.stub()
    loadArchive.onFirstCall().rejects(new Error('Initial load failed'))
    loadArchive.onSecondCall().resolves(archive)
    const instance = await PMTilesFileVectorSource.create({ filename: 'test.pmtiles' }, loadArchive)

    await instance.refreshPMTiles()

    sinon.assert.calledTwice(loadArchive)
    assert(instance.getState() === 'ready')
    assert(instance.getUrls()?.[0] === 'pmtiles://{z}/{x}/{y}?reload=1')
  })

  it('times out and reports a hanging tile read', async () => {
    vi.useFakeTimers()
    try {
      const hangingReader = new HangingPMTiles()
      const { archive } = buildArchive(sandbox, hangingReader)
      const instance = await PMTilesFileVectorSource.create({ filename: 'test.pmtiles' }, () =>
        Promise.resolve(archive)
      )
      const tile = buildTile(sandbox)

      instance.tileLoadFunction(tile as never, 'pmtiles://1/2/3')
      await vi.advanceTimersByTimeAsync(10_000)
      await Promise.resolve()

      assert(hangingReader.signal?.aborted)
      expect(mockCaptureException).toHaveBeenCalledOnce()
      expect(mockSetContext).toHaveBeenCalledWith('pmtilesTile', {
        filename: 'test.pmtiles',
        z: 1,
        x: 2,
        y: 3,
        sourceState: 'ready'
      })
    } finally {
      vi.useRealTimers()
    }
  })
})
