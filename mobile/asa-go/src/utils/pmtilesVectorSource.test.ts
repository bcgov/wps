import { DateTime } from 'luxon'
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
import { RunType } from '@/api/fbaAPI'
import type { IPMTilesCache } from '@/utils/pmtilesCache'
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
    console.log('getHeader called')
    return Promise.resolve(testPMTilesHeader)
  }
  getZxyAttempt(z: number, x: number, y: number, signal?: AbortSignal): Promise<RangeResponse | undefined> {
    console.log('getZxyAttempt called', z, x, y, signal)
    return Promise.resolve(undefined)
  }
  getZxy(z: number, x: number, y: number, signal?: AbortSignal): Promise<RangeResponse | undefined> {
    console.log('getZxy called', z, x, y, signal)
    return Promise.resolve(undefined)
  }
  getMetadataAttempt(): Promise<unknown> {
    console.log('getMetadataAttempt called')
    return Promise.resolve()
  }
  getMetadata(): Promise<unknown> {
    console.log('getMetadata called')
    return Promise.resolve()
  }
  getTileJson(baseTilesUrl: string): Promise<unknown> {
    console.log('getTileJSON called', baseTilesUrl)
    return Promise.resolve()
  }
}

class ErrorPMTiles extends TestPMTiles {
  getZxy(z: number, x: number, y: number, signal?: AbortSignal): Promise<RangeResponse | undefined> {
    console.log('getZxy called', z, x, y, signal)
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

  const buildPMTilesTestCache = (pmtiles?: PMTiles) => {
    return {
      loadPMTiles: (
        filename: string,
        fetchAndStoreCallback?: () => Promise<PMTiles | undefined>
      ): Promise<PMTiles | undefined> => {
        console.log('loadPMTiles called', filename, fetchAndStoreCallback)
        return Promise.resolve(pmtiles)
      },
      loadHFIPMTiles: (
        for_date: DateTime,
        run_type: RunType,
        run_date: DateTime,
        filename: string
      ): Promise<PMTiles | undefined> => {
        console.log('loadPMTiles called', for_date, run_type, run_date, filename)
        return Promise.resolve(pmtiles)
      }
    }
  }
  it('should attempt to load static pmtiles upon creation', async () => {
    const testCache: IPMTilesCache = buildPMTilesTestCache(new TestPMTiles())
    const pmTilesCacheSpy = sandbox.spy(testCache)

    await PMTilesFileVectorSource.createStaticLayer(testCache, {
      filename: 'test.pmtiles'
    })
    sinon.assert.calledOnce(pmTilesCacheSpy.loadPMTiles)
    sinon.assert.notCalled(pmTilesCacheSpy.loadHFIPMTiles)
  })

  it('should attempt to load hfi pmtiles upon creation', async () => {
    const testCache: IPMTilesCache = buildPMTilesTestCache(new TestPMTiles())
    const pmTilesCacheSpy = sandbox.spy(testCache)

    await PMTilesFileVectorSource.createHFILayer(testCache, {
      filename: 'test.pmtiles',
      for_date: DateTime.fromISO('2016-05-25T09:08:34.123'),
      run_type: RunType.FORECAST,
      run_date: DateTime.fromISO('2016-05-25T09:08:34.123')
    })
    sinon.assert.calledOnce(pmTilesCacheSpy.loadHFIPMTiles)
    sinon.assert.notCalled(pmTilesCacheSpy.loadPMTiles)
  })

  it('should attempt to load basemap pmtiles upon creation', async () => {
    const testCache: IPMTilesCache = buildPMTilesTestCache(new TestPMTiles())
    const pmTilesCacheSpy = sandbox.spy(testCache)

    await PMTilesFileVectorSource.createBasemapSource(testCache, {
      filename: 'test.pmtiles'
    })
    sinon.assert.calledOnce(pmTilesCacheSpy.loadPMTiles)
    sinon.assert.notCalled(pmTilesCacheSpy.loadHFIPMTiles)
  })

  it('should set tile status ready once initialized', async () => {
    const testCache: IPMTilesCache = buildPMTilesTestCache(new TestPMTiles())
    const instance = await PMTilesFileVectorSource.createHFILayer(testCache, {
      filename: 'test.pmtiles',
      for_date: DateTime.fromISO('2016-05-25T09:08:34.123'),
      run_type: RunType.FORECAST,
      run_date: DateTime.fromISO('2016-05-25T09:08:34.123')
    })
    const tileGrid = instance.getTileGrid()
    assert(tileGrid !== null)
    assert(tileGrid.getMaxZoom() === testPMTilesHeader.maxZoom)
    assert(tileGrid.getMinZoom() === testPMTilesHeader.minZoom)
    assert(instance.getState() === 'ready')
  })

  it('should set tile status ready once basemap initialized', async () => {
    const testCache: IPMTilesCache = buildPMTilesTestCache(new TestPMTiles())
    const instance = await PMTilesFileVectorSource.createBasemapSource(testCache, {
      filename: 'test.pmtiles'
    })
    const tileGrid = instance.getTileGrid()
    assert(tileGrid !== null)
    assert(tileGrid.getMaxZoom() === testPMTilesHeader.maxZoom)
    assert(tileGrid.getMinZoom() === testPMTilesHeader.minZoom)
    assert(instance.getState() === 'ready')
  })

  it('should reload pmtiles and refresh cached tiles', async () => {
    const testCache: IPMTilesCache = buildPMTilesTestCache(new TestPMTiles())
    const pmTilesCacheSpy = sandbox.spy(testCache)
    const instance = await PMTilesFileVectorSource.createStaticLayer(testCache, {
      filename: 'test.pmtiles'
    })
    const refreshSpy = sandbox.spy(instance, 'refresh')

    await instance.reloadPMTiles()

    sinon.assert.calledTwice(pmTilesCacheSpy.loadPMTiles)
    sinon.assert.calledOnce(refreshSpy)
    assert(instance.getUrls()?.[0] === 'pmtiles://{z}/{x}/{y}?reload=1')
    assert(instance.getState() === 'ready')
  })

  it('should refresh cached tiles without reloading pmtiles', async () => {
    const testCache: IPMTilesCache = buildPMTilesTestCache(new TestPMTiles())
    const pmTilesCacheSpy = sandbox.spy(testCache)
    const instance = await PMTilesFileVectorSource.createStaticLayer(testCache, {
      filename: 'test.pmtiles'
    })
    const refreshSpy = sandbox.spy(instance, 'refresh')

    await instance.refreshPMTiles()

    sinon.assert.calledOnce(pmTilesCacheSpy.loadPMTiles)
    sinon.assert.calledOnce(refreshSpy)
    assert(instance.getUrls()?.[0] === 'pmtiles://{z}/{x}/{y}?reload=1')
  })

  it('should reload pmtiles without reporting when recovery succeeds', async () => {
    const loadPMTiles = sandbox.stub()
    loadPMTiles.onFirstCall().resolves(new ErrorPMTiles())
    loadPMTiles.onSecondCall().resolves(new TestPMTiles())
    const testCache: IPMTilesCache = {
      loadPMTiles,
      loadHFIPMTiles: sandbox.stub()
    }
    const instance = await PMTilesFileVectorSource.createStaticLayer(testCache, {
      filename: 'test.pmtiles'
    })
    const refreshSpy = sandbox.spy(instance, 'refresh')
    const tile = {
      extent: undefined,
      projection: undefined,
      setFeatures: sandbox.stub(),
      setState: sandbox.stub()
    }

    instance.tileLoadFunction(tile as never, 'pmtiles://0/0/0')
    instance.tileLoadFunction(tile as never, 'pmtiles://0/0/0')
    await vi.waitFor(() => sinon.assert.calledTwice(loadPMTiles))
    await vi.waitFor(() => assert(instance.getUrls()?.[0] === 'pmtiles://{z}/{x}/{y}?reload=1'))

    sinon.assert.calledTwice(loadPMTiles)
    sinon.assert.calledOnce(refreshSpy)
    expect(mockCaptureException).not.toHaveBeenCalled()
    expect(mockSetContext).not.toHaveBeenCalled()
  })

  it('should only retry a tile load error once until retries are enabled again', async () => {
    const loadPMTiles = sandbox.stub()
    loadPMTiles.onFirstCall().resolves(new ErrorPMTiles())
    loadPMTiles.onSecondCall().resolves(new ErrorPMTiles())
    loadPMTiles.onThirdCall().resolves(new TestPMTiles())
    const testCache: IPMTilesCache = {
      loadPMTiles,
      loadHFIPMTiles: sandbox.stub()
    }
    const instance = await PMTilesFileVectorSource.createStaticLayer(testCache, {
      filename: 'test.pmtiles'
    })
    const tile = {
      extent: undefined,
      projection: undefined,
      setFeatures: sandbox.stub(),
      setState: sandbox.stub()
    }

    instance.tileLoadFunction(tile as never, 'pmtiles://0/0/0')
    await vi.waitFor(() => sinon.assert.calledTwice(loadPMTiles))
    await vi.waitFor(() => assert(instance.getUrls()?.[0] === 'pmtiles://{z}/{x}/{y}?reload=1'))

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
    instance.tileLoadFunction(tile as never, 'pmtiles://0/0/0?reload=1')
    await vi.waitFor(() => sinon.assert.calledThrice(loadPMTiles))

    sinon.assert.calledThrice(loadPMTiles)
    expect(mockCaptureException).toHaveBeenCalledOnce()
  })

  it('should reload pmtiles when source initialization has errored', async () => {
    const loadPMTiles = sandbox.stub()
    loadPMTiles.onFirstCall().resolves(undefined)
    loadPMTiles.onSecondCall().resolves(new TestPMTiles())
    const testCache: IPMTilesCache = {
      loadPMTiles,
      loadHFIPMTiles: sandbox.stub()
    }
    const instance = await PMTilesFileVectorSource.createStaticLayer(testCache, {
      filename: 'test.pmtiles'
    })
    const refreshSpy = sandbox.spy(instance, 'refresh')

    await instance.refreshPMTiles()

    sinon.assert.calledTwice(loadPMTiles)
    sinon.assert.calledOnce(refreshSpy)
    assert(instance.getState() === 'ready')
  })

  it('should report when recovery from a timed out tile load fails', async () => {
    vi.useFakeTimers()
    try {
      const hangingPMTiles = new HangingPMTiles()
      const reloadError = new Error('Reader reload failed')
      const loadPMTiles = sandbox.stub()
      loadPMTiles.onFirstCall().resolves(hangingPMTiles)
      loadPMTiles.onSecondCall().rejects(reloadError)
      const testCache: IPMTilesCache = {
        loadPMTiles,
        loadHFIPMTiles: sandbox.stub()
      }
      const instance = await PMTilesFileVectorSource.createStaticLayer(testCache, {
        filename: 'test.pmtiles'
      })
      const tile = {
        extent: undefined,
        projection: undefined,
        setFeatures: sandbox.stub(),
        setState: sandbox.stub()
      }

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
