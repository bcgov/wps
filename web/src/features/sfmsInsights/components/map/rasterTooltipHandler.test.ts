import {
  getRasterTooltipData,
  findRasterLayer,
  getRasterType,
  getRasterData,
  getDataAtPixel
} from './rasterTooltipHandler'
import { NODATA_THRESHOLD } from './sfmsFeatureStylers'

describe('getRasterTooltipData', () => {
  describe('should return null value for invalid data', () => {
    it.each([
      ['null data', null, undefined, 'FWI'],
      ['empty array', new Float32Array([]), undefined, 'FWI'],
      ['undefined first element', new Float32Array([undefined as any]), undefined, 'FWI'],
      ['null data with raster type', null, 'fwi' as const, 'FWI'],
      ['empty array with raster type', new Float32Array([]), 'dmc' as const, 'DMC']
    ])('%s', (_description, data, rasterType, expectedLabel) => {
      const result = getRasterTooltipData(data, rasterType)
      expect(result.value).toBeNull()
      expect(result.label).toBe(expectedLabel)
    })
  })

  describe('should return null value for nodata values', () => {
    it.each([
      ['large positive nodata', new Float32Array([NODATA_THRESHOLD + 1000]), 'fwi' as const],
      ['GeoTIFF nodata', new Float32Array([-3.4028235e38]), 'dmc' as const],
      ['large negative nodata', new Float32Array([-NODATA_THRESHOLD - 1000]), 'dc' as const],
      ['positive infinity', new Float32Array([Infinity]), 'ffmc' as const],
      ['negative infinity', new Float32Array([-Infinity]), 'bui' as const]
    ])('%s', (_description, data, rasterType) => {
      const result = getRasterTooltipData(data, rasterType)
      expect(result.value).toBeNull()
      expect(result.label).toBeDefined()
    })
  })

  describe('should return rounded value for valid data', () => {
    it.each([
      ['zero', new Float32Array([0]), undefined, 0, 'FWI'],
      ['small integer', new Float32Array([5]), 'fwi' as const, 5, 'FWI'],
      ['decimal value rounds down', new Float32Array([42.3]), 'dmc' as const, 42, 'DMC'],
      ['decimal value rounds up', new Float32Array([42.7]), 'dc' as const, 43, 'DC'],
      ['negative value', new Float32Array([-5]), 'ffmc' as const, -5, 'FFMC'],
      ['large valid value', new Float32Array([9999]), 'bui' as const, 9999, 'BUI'],
      ['at positive threshold', new Float32Array([NODATA_THRESHOLD]), 'isi' as const, NODATA_THRESHOLD, 'ISI'],
      ['at negative threshold', new Float32Array([-NODATA_THRESHOLD]), 'fwi' as const, -NODATA_THRESHOLD, 'FWI']
    ])('%s: %f', (_description, data, rasterType, expectedValue, expectedLabel) => {
      const result = getRasterTooltipData(data, rasterType)
      expect(result.value).toBe(expectedValue)
      expect(result.label).toBe(expectedLabel)
    })
  })

  describe('should handle different raster types correctly', () => {
    it.each([
      ['fwi', 'fwi' as const, 'FWI'],
      ['dmc', 'dmc' as const, 'DMC'],
      ['dc', 'dc' as const, 'DC'],
      ['ffmc', 'ffmc' as const, 'FFMC'],
      ['bui', 'bui' as const, 'BUI'],
      ['isi', 'isi' as const, 'ISI'],
      ['undefined defaults to FWI', undefined, 'FWI']
    ])('%s -> %s', (_description, rasterType, expectedLabel) => {
      const data = new Float32Array([50])
      const result = getRasterTooltipData(data, rasterType)
      expect(result.label).toBe(expectedLabel)
    })
  })

  describe('should use Uint8Array data', () => {
    it('should handle Uint8Array data', () => {
      const data = new Uint8Array([100])
      const result = getRasterTooltipData(data, 'fwi')
      expect(result.value).toBe(100)
      expect(result.label).toBe('FWI')
    })
  })
})

describe('findRasterLayer', () => {
  const createMockLayer = (hasRasterType: boolean, rasterType?: string) => ({
    getProperties: () => (hasRasterType ? { rasterType } : {})
  })

  it('should find layer with rasterType property', () => {
    const layers = [
      createMockLayer(false),
      createMockLayer(true, 'fwi'),
      createMockLayer(false)
    ]
    const result = findRasterLayer(layers)
    expect(result).toBeDefined()
    expect(result?.getProperties().rasterType).toBe('fwi')
  })

  it('should return undefined when no raster layer exists', () => {
    const layers = [
      createMockLayer(false),
      createMockLayer(false)
    ]
    const result = findRasterLayer(layers)
    expect(result).toBeUndefined()
  })

  it('should return first raster layer when multiple exist', () => {
    const layers = [
      createMockLayer(false),
      createMockLayer(true, 'fwi'),
      createMockLayer(true, 'dmc')
    ]
    const result = findRasterLayer(layers)
    expect(result?.getProperties().rasterType).toBe('fwi')
  })

  it('should handle empty layers array', () => {
    const result = findRasterLayer([])
    expect(result).toBeUndefined()
  })
})

describe('getRasterType', () => {
  const createMockLayer = (rasterType?: string) => ({
    getProperties: () => ({ rasterType })
  }) as any

  it.each([
    ['fwi', 'fwi'],
    ['dmc', 'dmc'],
    ['dc', 'dc'],
    ['ffmc', 'ffmc'],
    ['bui', 'bui'],
    ['isi', 'isi']
  ])('should extract rasterType: %s', (_description, rasterType) => {
    const layer = createMockLayer(rasterType)
    const result = getRasterType(layer)
    expect(result).toBe(rasterType)
  })

  it('should return undefined when rasterType not present', () => {
    const layer = createMockLayer()
    const result = getRasterType(layer)
    expect(result).toBeUndefined()
  })
})

describe('getRasterData', () => {
  const createMockLayer = (data: Float32Array | Uint8Array | null) => ({
    getData: vi.fn(() => data)
  }) as any

  it('should get data from layer at pixel coordinate', () => {
    const data = new Float32Array([42])
    const layer = createMockLayer(data)
    const pixel: [number, number] = [100, 200]

    const result = getRasterData(layer, pixel)

    expect(layer.getData).toHaveBeenCalledWith(pixel)
    expect(result).toBe(data)
  })

  it('should return null when no data available', () => {
    const layer = createMockLayer(null)
    const pixel: [number, number] = [100, 200]

    const result = getRasterData(layer, pixel)

    expect(result).toBeNull()
  })

  it('should handle Uint8Array data', () => {
    const data = new Uint8Array([100])
    const layer = createMockLayer(data)
    const pixel: [number, number] = [50, 75]

    const result = getRasterData(layer, pixel)

    expect(result).toBe(data)
  })
})

describe('getDataAtPixel', () => {
  const createMockLayer = (data: Float32Array | Uint8Array | null, rasterType?: string) => ({
    getData: vi.fn(() => data),
    getProperties: () => ({ rasterType })
  }) as any

  it('should get tooltip data from layer with valid data', () => {
    const data = new Float32Array([42.7])
    const layer = createMockLayer(data, 'fwi')
    const pixel: [number, number] = [100, 200]

    const result = getDataAtPixel(layer, pixel)

    expect(result.value).toBe(43) // Rounded
    expect(result.label).toBe('FWI')
  })

  it('should filter out nodata values', () => {
    const data = new Float32Array([-3.4028235e38])
    const layer = createMockLayer(data, 'dmc')
    const pixel: [number, number] = [100, 200]

    const result = getDataAtPixel(layer, pixel)

    expect(result.value).toBeNull()
    expect(result.label).toBe('DMC')
  })

  it('should handle null data', () => {
    const layer = createMockLayer(null, 'dc')
    const pixel: [number, number] = [100, 200]

    const result = getDataAtPixel(layer, pixel)

    expect(result.value).toBeNull()
    expect(result.label).toBe('DC')
  })

  it('should handle different raster types', () => {
    const data = new Float32Array([50])
    const pixel: [number, number] = [100, 200]

    const testCases = [
      ['fwi', 'FWI'],
      ['dmc', 'DMC'],
      ['dc', 'DC'],
      ['ffmc', 'FFMC'],
      ['bui', 'BUI'],
      ['isi', 'ISI']
    ] as const

    testCases.forEach(([rasterType, expectedLabel]) => {
      const layer = createMockLayer(data, rasterType)
      const result = getDataAtPixel(layer, pixel)
      expect(result.label).toBe(expectedLabel)
    })
  })

  it('should call getData with correct pixel coordinates', () => {
    const data = new Float32Array([25])
    const layer = createMockLayer(data, 'fwi')
    const pixel: [number, number] = [123, 456]

    getDataAtPixel(layer, pixel)

    expect(layer.getData).toHaveBeenCalledWith(pixel)
    expect(layer.getData).toHaveBeenCalledTimes(1)
  })
})
