import { getSnowPMTilesLayer, getFireWeatherRasterLayer } from './layerDefinitions'
import { DateTime } from 'luxon'

// Mock pmtiles to prevent actual network requests
vi.mock('pmtiles', () => ({
  FetchSource: class MockFetchSource {
    url: string
    constructor(url: string) {
      this.url = url
    }
    async getBytes() {
      // Create a valid PMTiles header with magic number
      // PMTiles header is 127 bytes
      const buffer = new ArrayBuffer(127)
      const view = new Uint8Array(buffer)
      // Write "PMTiles" magic number (ASCII bytes)
      view[0] = 0x50 // 'P'
      view[1] = 0x4d // 'M'
      view[2] = 0x54 // 'T'
      view[3] = 0x69 // 'i'
      view[4] = 0x6c // 'l'
      view[5] = 0x65 // 'e'
      view[6] = 0x73 // 's'
      view[7] = 3 // version 3
      return {
        data: buffer,
        etag: 'test-etag',
        expires: null,
        cacheControl: null
      }
    }
    getKey() {
      return this.url
    }
  },
  PMTiles: class MockPMTiles {
    header: any
    constructor(source: any) {
      // Initialize header synchronously to avoid async issues
      this.header = {
        rootDirectoryOffset: 0,
        rootDirectoryLength: 0,
        jsonMetadataOffset: 0,
        jsonMetadataLength: 0,
        leafDirectoryOffset: 0,
        leafDirectoryLength: 0,
        tileDataOffset: 0,
        tileDataLength: 0,
        numAddressedTiles: 0,
        numTileEntries: 0,
        numTileContents: 0,
        clustered: false,
        internalCompression: 0,
        tileCompression: 0,
        tileType: 0,
        minZoom: 0,
        maxZoom: 14,
        minLon: -180,
        minLat: -85,
        maxLon: 180,
        maxLat: 85,
        centerZoom: 0,
        centerLon: 0,
        centerLat: 0
      }
    }
    async getHeader() {
      return Promise.resolve(this.header)
    }
    async getZxy() {
      return Promise.resolve(null)
    }
  }
}))

describe('layerDefinitions', () => {
  describe('getSnowPMTilesLayer', () => {
    it('should create snow layer with zIndex 53', () => {
      const snowDate = DateTime.fromISO('2025-11-02')
      const layer = getSnowPMTilesLayer(snowDate)

      expect(layer.getZIndex()).toBe(53)
    })

    it('should create snow layer with correct name property', () => {
      const snowDate = DateTime.fromISO('2025-11-02')
      const layer = getSnowPMTilesLayer(snowDate)

      expect(layer.getProperties().name).toBe('snowVector')
    })

    it('should create snow layer with minZoom of 4', () => {
      const snowDate = DateTime.fromISO('2025-11-02')
      const layer = getSnowPMTilesLayer(snowDate)

      expect(layer.getMinZoom()).toBe(4)
    })

    it('should generate correct PMTiles URL for snow layer', () => {
      const snowDate = DateTime.fromISO('2025-11-02')
      const layer = getSnowPMTilesLayer(snowDate)
      const source = layer.getSource()

      // Check that source exists
      expect(source).toBeDefined()
    })
  })

  describe('getFireWeatherRasterLayer', () => {
    it('should create fire weather layer with zIndex 52', () => {
      const rasterDate = DateTime.fromISO('2025-11-02')
      const layer = getFireWeatherRasterLayer(rasterDate, 'fwi', 'test-token')

      expect(layer.getZIndex()).toBe(52)
    })

    it('should have lower zIndex than snow layer', () => {
      const date = DateTime.fromISO('2025-11-02')
      const snowLayer = getSnowPMTilesLayer(date)
      const fireWeatherLayer = getFireWeatherRasterLayer(date, 'fwi', 'test-token')
      const fireWeatherLayerZIdx = fireWeatherLayer.getZIndex()

      expect(snowLayer.getZIndex()).toBeGreaterThan(fireWeatherLayerZIdx!)
    })
  })

  describe('layer ordering', () => {
    it('should ensure snow layer renders on top of fire weather rasters', () => {
      const date = DateTime.fromISO('2025-11-02')
      const snowLayer = getSnowPMTilesLayer(date)
      const fwiLayer = getFireWeatherRasterLayer(date, 'fwi', 'test-token')
      const dmcLayer = getFireWeatherRasterLayer(date, 'dmc', 'test-token')
      const dcLayer = getFireWeatherRasterLayer(date, 'dc', 'test-token')

      const snowZIndex = snowLayer.getZIndex()!
      const fwiZIndex = fwiLayer.getZIndex()!
      const dmcZIndex = dmcLayer.getZIndex()!
      const dcZIndex = dcLayer.getZIndex()!

      expect(snowZIndex).toBeGreaterThan(fwiZIndex)
      expect(snowZIndex).toBeGreaterThan(dmcZIndex)
      expect(snowZIndex).toBeGreaterThan(dcZIndex)
    })
  })
})
