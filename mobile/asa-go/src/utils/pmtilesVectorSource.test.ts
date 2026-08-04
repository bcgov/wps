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

const buildTile = (sandbox: sinon.SinonSandbox) => ({
  extent: undefined,
  projection: undefined,
  setFeatures: sandbox.stub(),
  setState: sandbox.stub()
})

describe('pmTilesVectorSource', () => {
  let sandbox: sinon.SinonSandbox

  beforeEach(() => {
    sandbox = sinon.createSandbox()
    mockCaptureException.mockClear()
    mockSetContext.mockClear()
  })

  afterEach(() => {
    sandbox.restore()
  })

  it('loads pmtiles and initializes the tile grid on creation', async () => {
    const loadPMTiles = sandbox.stub().resolves(new TestPMTiles())

    const instance = await PMTilesFileVectorSource.create({ filename: 'test.pmtiles' }, loadPMTiles)
    const tileGrid = instance.getTileGrid()

    sinon.assert.calledOnce(loadPMTiles)
    assert(tileGrid !== null)
    assert(tileGrid.getMaxZoom() === testPMTilesHeader.maxZoom)
    assert(tileGrid.getMinZoom() === testPMTilesHeader.minZoom)
    assert(instance.getState() === 'ready')
  })

  it('reloads pmtiles and invalidates cached tiles', async () => {
    const loadPMTiles = sandbox.stub().resolves(new TestPMTiles())
    const instance = await PMTilesFileVectorSource.create({ filename: 'test.pmtiles' }, loadPMTiles)
    const refreshSpy = sandbox.spy(instance, 'refresh')

    await instance.reloadPMTiles()

    sinon.assert.calledTwice(loadPMTiles)
    sinon.assert.calledOnce(refreshSpy)
    assert(instance.getUrls()?.[0] === 'pmtiles://{z}/{x}/{y}?reload=1')
    assert(instance.getState() === 'ready')
  })

  it('invalidates cached tiles on foreground without reloading pmtiles', async () => {
    const loadPMTiles = sandbox.stub().resolves(new TestPMTiles())
    const instance = await PMTilesFileVectorSource.create({ filename: 'test.pmtiles' }, loadPMTiles)
    const refreshSpy = sandbox.spy(instance, 'refresh')

    await instance.refreshPMTiles()

    sinon.assert.calledOnce(loadPMTiles)
    sinon.assert.calledOnce(refreshSpy)
    assert(instance.getUrls()?.[0] === 'pmtiles://{z}/{x}/{y}?reload=1')
  })

  it('reloads pmtiles without reporting when tile recovery succeeds', async () => {
    const loadPMTiles = sandbox.stub()
    loadPMTiles.onFirstCall().resolves(new ErrorPMTiles())
    loadPMTiles.onSecondCall().resolves(new TestPMTiles())
    const instance = await PMTilesFileVectorSource.create({ filename: 'test.pmtiles' }, loadPMTiles)
    const refreshSpy = sandbox.spy(instance, 'refresh')
    const tile = buildTile(sandbox)

    instance.tileLoadFunction(tile as never, 'pmtiles://0/0/0')
    instance.tileLoadFunction(tile as never, 'pmtiles://0/0/0')
    await vi.waitFor(() => sinon.assert.calledTwice(loadPMTiles))
    await vi.waitFor(() => assert(instance.getUrls()?.[0] === 'pmtiles://{z}/{x}/{y}?reload=1'))

    sinon.assert.calledOnce(refreshSpy)
    expect(mockCaptureException).not.toHaveBeenCalled()
    expect(mockSetContext).not.toHaveBeenCalled()
  })

  it('only retries a tile error once until foregrounding enables recovery again', async () => {
    const loadPMTiles = sandbox.stub()
    loadPMTiles.onFirstCall().resolves(new ErrorPMTiles())
    loadPMTiles.onSecondCall().resolves(new ErrorPMTiles())
    loadPMTiles.onThirdCall().resolves(new TestPMTiles())
    const instance = await PMTilesFileVectorSource.create({ filename: 'test.pmtiles' }, loadPMTiles)
    const tile = buildTile(sandbox)

    instance.tileLoadFunction(tile as never, 'pmtiles://0/0/0')
    await vi.waitFor(() => sinon.assert.calledTwice(loadPMTiles))

    instance.tileLoadFunction(tile as never, 'pmtiles://0/0/0?reload=1')
    await new Promise(resolve => setTimeout(resolve, 0))

    sinon.assert.calledTwice(loadPMTiles)
    expect(mockCaptureException).toHaveBeenCalledOnce()
    expect(mockSetContext).toHaveBeenCalledWith('pmtilesTile', {
      filename: 'test.pmtiles',
      z: 0,
      x: 0,
      y: 0,
      sourceState: 'ready'
    })

    await instance.refreshPMTiles()
    instance.tileLoadFunction(tile as never, 'pmtiles://0/0/0?reload=2')
    await vi.waitFor(() => sinon.assert.calledThrice(loadPMTiles))

    expect(mockCaptureException).toHaveBeenCalledOnce()
  })

  it('retries source initialization when foregrounding', async () => {
    const loadPMTiles = sandbox.stub()
    loadPMTiles.onFirstCall().rejects(new Error('Initial load failed'))
    loadPMTiles.onSecondCall().resolves(new TestPMTiles())
    const instance = await PMTilesFileVectorSource.create({ filename: 'test.pmtiles' }, loadPMTiles)
    const refreshSpy = sandbox.spy(instance, 'refresh')

    await instance.refreshPMTiles()

    sinon.assert.calledTwice(loadPMTiles)
    sinon.assert.calledOnce(refreshSpy)
    assert(instance.getState() === 'ready')
  })

  it('reports when recovery from a timed out tile load fails', async () => {
    vi.useFakeTimers()
    try {
      const hangingPMTiles = new HangingPMTiles()
      const reloadError = new Error('Reader reload failed')
      const loadPMTiles = sandbox.stub()
      loadPMTiles.onFirstCall().resolves(hangingPMTiles)
      loadPMTiles.onSecondCall().rejects(reloadError)
      const instance = await PMTilesFileVectorSource.create({ filename: 'test.pmtiles' }, loadPMTiles)
      const tile = buildTile(sandbox)

      instance.tileLoadFunction(tile as never, 'pmtiles://1/2/3')
      await vi.advanceTimersByTimeAsync(10_000)
      await Promise.resolve()

      sinon.assert.calledTwice(loadPMTiles)
      assert(hangingPMTiles.signal?.aborted)
      expect(mockCaptureException).toHaveBeenCalledOnce()
      expect(mockCaptureException).toHaveBeenCalledWith(reloadError)
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
