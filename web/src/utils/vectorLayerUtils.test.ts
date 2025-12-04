import { afterEach, describe, expect, it, vi } from 'vitest'

// Mock applyStyle from ol-mapbox-style
vi.mock('ol-mapbox-style', () => ({
  applyStyle: vi.fn()
}))

// Strong type for our axios.get mock
type AxiosGet = (url: string) => Promise<{ data: unknown }>

// Mock axios before each run (hoisted by Vitest)
vi.mock('axios', () => {
  return {
    default: {
      get: vi.fn()
    }
  }
})

import { createHillshadeVectorTileLayer, createVectorTileLayer, getStyleJson } from '@/utils/vectorLayerUtils'
import axios from 'axios'
import { applyStyle } from 'ol-mapbox-style'

afterEach(() => {
  vi.clearAllMocks()
  vi.restoreAllMocks()
})

describe('getStyleJson', () => {
  it('returns data on success', async () => {
    const sample = { name: 'my-style', version: 8 }

    // Strongly-typed mock for axios.get
    ;(axios.get as unknown as AxiosGet) = vi.fn(async (url: string) => {
      expect(url).toBe('https://example.com/style.json')
      return { data: sample }
    })

    const result = await getStyleJson('https://example.com/style.json')

    expect(result).toEqual(sample)
    expect(axios.get).toHaveBeenCalledTimes(1)
    expect(axios.get).toHaveBeenCalledWith('https://example.com/style.json')
  })

  it('returns {} on failure and logs an error', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    ;(axios.get as unknown as AxiosGet) = vi.fn(async () => {
      throw new Error('network error')
    })

    const result = await getStyleJson('https://bad-url/style.json')

    expect(result).toEqual({})
    expect(axios.get).toHaveBeenCalledTimes(1)
    expect(axios.get).toHaveBeenCalledWith('https://bad-url/style.json')
    expect(consoleSpy).toHaveBeenCalledWith('Unable to fetch style JSON.')
  })
})

describe('createVectorBasemapLayer', () => {
  it('creates a VectorTileLayer with the given source, opacity, sets name, and applies style (object style)', async () => {
    const sourceUrl = 'https://tiles.example.com/{z}/{x}/{y}.mvt'
    const glstyle = { version: 8, name: 'mock-style' } // object style
    const opacity = 0.5
    const name = 'Basemap'
    const layer = await createVectorTileLayer(sourceUrl, glstyle as unknown, opacity, name)

    expect(layer.getOpacity()).toBe(opacity)
    const source = layer.getSource()
    expect(source).toBeDefined()
    const urls = source?.getUrls()
    expect(urls?.[0]).toBe(sourceUrl)
    expect(layer.get('name')).toBe(name)
    expect(applyStyle).toHaveBeenCalledTimes(1)
    expect(applyStyle).toHaveBeenCalledWith(layer, glstyle, { updateSource: false })
  })
})

describe('createHillshadeVectorTileLayer', () => {
  it('creates a VectorTileLayer with the given source, opacity, sets name, and applies style (object style)', async () => {
    const sourceUrl = 'https://tiles.example.com/{z}/{x}/{y}.mvt'
    const glstyle = { version: 8, name: 'mock-style' } // object style
    const opacity = 0.5
    const name = 'Hillshade'
    const layer = await createHillshadeVectorTileLayer(sourceUrl, glstyle as unknown, opacity, name)

    expect(layer.getOpacity()).toBe(opacity)
    const source = layer.getSource()
    expect(source).toBeDefined()
    const urls = source?.getUrls()
    expect(urls?.[0]).toBe(sourceUrl)
    expect(layer.get('name')).toBe(name)
    expect(applyStyle).toHaveBeenCalledTimes(1)
    expect(applyStyle).toHaveBeenCalledWith(layer, glstyle, { updateSource: false })
  })
})
