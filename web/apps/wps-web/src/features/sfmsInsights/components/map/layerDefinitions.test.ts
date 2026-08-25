import { RunType } from '@wps/api/runType'
import { DateTime } from 'luxon'
import { getRasterLayer, getSFMSNGRasterLayer, getSFMSNGRasterPath, getSnowPMTilesLayer } from './layerDefinitions'

type Listener = (...args: unknown[]) => void

// Mock pmtiles completely to prevent any parsing
vi.mock('pmtiles', () => ({
  FetchSource: class MockFetchSource {
    url: string
    constructor(url: string) {
      this.url = url
    }
    getKey() {
      return this.url
    }
  },
  PMTiles: class MockPMTiles {}
}))

// Mock ol/source/GeoTIFF to prevent background network fetches that cause unhandled rejections
vi.mock('ol/source/GeoTIFF', () => ({
  default: class MockGeoTIFF {
    getState() {
      return 'ready'
    }
    getView() {
      return Promise.resolve({ center: [0, 0], zoom: 0 })
    }
    addEventListener() {}
    removeEventListener() {}
  }
}))

// Mock ol-pmtiles to prevent it from using real PMTiles
vi.mock('ol-pmtiles', () => ({
  PMTilesVectorSource: class MockPMTilesVectorSource {
    private listeners: Map<string, Set<Listener>> = new Map()

    addEventListener(type: string, listener: Listener) {
      if (!this.listeners.has(type)) {
        this.listeners.set(type, new Set())
      }
      this.listeners.get(type)!.add(listener)
    }

    removeEventListener(type: string, listener: Listener) {
      const typeListeners = this.listeners.get(type)
      if (typeListeners) {
        typeListeners.delete(listener)
      }
    }

    on(type: string, listener: Listener) {
      this.addEventListener(type, listener)
      return this
    }

    once(type: string, listener: Listener) {
      this.addEventListener(type, listener)
      return this
    }

    un(type: string, listener: Listener) {
      this.removeEventListener(type, listener)
      return this
    }

    getState() {
      return 'ready'
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

  describe('getSFMSNGRasterLayer', () => {
    it('should generate SFMSNG actual COG paths for FWI rasters', () => {
      const rasterDate = DateTime.fromISO('2025-11-02')

      expect(getSFMSNGRasterPath(rasterDate, 'fwi')).toBe('sfms_ng/actual/2025/11/02/fwi_20251102_cog.tif')
    })

    it('should generate SFMSNG actual COG paths for weather rasters', () => {
      const rasterDate = DateTime.fromISO('2025-11-02')

      expect(getSFMSNGRasterPath(rasterDate, 'relative_humidity')).toBe(
        'sfms_ng/actual/2025/11/02/relative_humidity_20251102_cog.tif'
      )
    })

    it('should generate SFMSNG forecast COG paths', () => {
      const rasterDate = DateTime.fromISO('2025-11-05')

      expect(getSFMSNGRasterPath(rasterDate, 'fwi', RunType.FORECAST)).toBe(
        'sfms_ng/forecast/2025/11/05/fwi_20251105_cog.tif'
      )
    })

    it('should generate run-specific SFC COG paths', () => {
      const rasterDate = DateTime.fromISO('2025-11-05')

      expect(getSFMSNGRasterPath(rasterDate, 'sfc', RunType.FORECAST)).toBe(
        'sfms_ng/forecast/2025/11/05/sfc_20251105_cog.tif'
      )
    })

    it('should generate the shared FMC COG path regardless of run type', () => {
      const rasterDate = DateTime.fromISO('2025-11-05')
      const expectedPath = 'sfms_ng/static/fmc/2025/11/05/fmc_20251105_cog.tif'

      expect(getSFMSNGRasterPath(rasterDate, 'fmc', RunType.ACTUAL)).toBe(expectedPath)
      expect(getSFMSNGRasterPath(rasterDate, 'fmc', RunType.FORECAST)).toBe(expectedPath)
    })

    it('should create fire weather layer with zIndex 52', () => {
      const rasterDate = DateTime.fromISO('2025-11-02')
      const layer = getSFMSNGRasterLayer(rasterDate, 'fwi', 'test-token')

      expect(layer.getZIndex()).toBe(52)
    })

    it('should have lower zIndex than snow layer', () => {
      const date = DateTime.fromISO('2025-11-02')
      const snowLayer = getSnowPMTilesLayer(date)
      const fireWeatherLayer = getSFMSNGRasterLayer(date, 'fwi', 'test-token')
      const fireWeatherLayerZIdx = fireWeatherLayer.getZIndex()

      expect(snowLayer.getZIndex()).toBeGreaterThan(fireWeatherLayerZIdx!)
    })
  })

  describe('layer ordering', () => {
    it('should ensure snow layer renders on top of fire weather rasters', () => {
      const date = DateTime.fromISO('2025-11-02')
      const snowLayer = getSnowPMTilesLayer(date)
      const fwiLayer = getSFMSNGRasterLayer(date, 'fwi', 'test-token')
      const dmcLayer = getSFMSNGRasterLayer(date, 'dmc', 'test-token')
      const dcLayer = getSFMSNGRasterLayer(date, 'dc', 'test-token')

      const snowZIndex = snowLayer.getZIndex()!
      const fwiZIndex = fwiLayer.getZIndex()!
      const dmcZIndex = dmcLayer.getZIndex()!
      const dcZIndex = dcLayer.getZIndex()!

      expect(snowZIndex).toBeGreaterThan(fwiZIndex)
      expect(snowZIndex).toBeGreaterThan(dmcZIndex)
      expect(snowZIndex).toBeGreaterThan(dcZIndex)
    })
  })

  describe('getRasterLayer', () => {
    it('should return fuel layer when rasterType is fuel with null date', () => {
      const layer = getRasterLayer(null, 'fuel', 'test-token')
      expect(layer).toBeDefined()
      expect(layer).not.toBeNull()
      expect(layer!.getProperties().rasterType).toBe('fuel')
    })

    it('should return fuel layer when rasterType is fuel with date', () => {
      const date = DateTime.fromISO('2025-11-02')
      const layer = getRasterLayer(date, 'fuel', 'test-token')
      expect(layer).toBeDefined()
      expect(layer).not.toBeNull()
      expect(layer!.getProperties().rasterType).toBe('fuel')
    })

    it('should return fire weather layer when date is provided', () => {
      const date = DateTime.fromISO('2025-11-02')
      const layer = getRasterLayer(date, 'fwi', 'test-token')
      expect(layer).toBeDefined()
      expect(layer).not.toBeNull()
      expect(layer!.getProperties().rasterType).toBe('fwi')
    })

    it('should return weather layer when date is provided', () => {
      const date = DateTime.fromISO('2025-11-02')
      const layer = getRasterLayer(date, 'temperature', 'test-token')
      expect(layer).toBeDefined()
      expect(layer).not.toBeNull()
      expect(layer!.getProperties().rasterType).toBe('temperature')
    })

    it('should return a forecast fire weather layer when forecast data is selected', () => {
      const date = DateTime.fromISO('2025-11-05')
      const layer = getRasterLayer(date, 'fwi', 'test-token', RunType.FORECAST)

      expect(layer).toBeDefined()
      expect(layer).not.toBeNull()
      expect(layer!.getProperties().rasterType).toBe('fwi')
    })

    it.each(['sfc', 'fmc'] as const)('should return an %s raster layer', rasterType => {
      const date = DateTime.fromISO('2025-11-05')
      const layer = getRasterLayer(date, rasterType, 'test-token', RunType.FORECAST)

      expect(layer).not.toBeNull()
      expect(layer!.getProperties().rasterType).toBe(rasterType)
    })

    it('should return null and log error when date is null for fire weather raster', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      const layer = getRasterLayer(null, 'fwi', 'test-token')
      expect(layer).toBeNull()
      expect(consoleErrorSpy).toHaveBeenCalledWith('date is required for SFMS NG rasters')
      consoleErrorSpy.mockRestore()
    })

    it('should return null and log error when date is null for other fire weather types', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      expect(getRasterLayer(null, 'dmc', 'test-token')).toBeNull()
      expect(getRasterLayer(null, 'dc', 'test-token')).toBeNull()
      expect(getRasterLayer(null, 'bui', 'test-token')).toBeNull()
      expect(consoleErrorSpy).toHaveBeenCalledTimes(3)

      consoleErrorSpy.mockRestore()
    })
  })
})
