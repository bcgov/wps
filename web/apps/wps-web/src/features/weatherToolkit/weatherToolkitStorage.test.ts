import { beforeEach, describe, expect, it, vi } from 'vitest'
import {
  readChartExpanded,
  storeChartExpanded,
  WEATHER_TOOLKIT_CHART_EXPANDED_STORAGE_KEY
} from './weatherToolkitStorage'

describe('weatherToolkitStorage', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    localStorage.clear()
  })

  it('returns false when local storage is empty', () => {
    expect(readChartExpanded()).toBe(false)
  })

  it('returns true when the chart was stored as expanded', () => {
    localStorage.setItem(WEATHER_TOOLKIT_CHART_EXPANDED_STORAGE_KEY, 'true')

    expect(readChartExpanded()).toBe(true)
  })

  it('returns false when the chart was stored as collapsed', () => {
    localStorage.setItem(WEATHER_TOOLKIT_CHART_EXPANDED_STORAGE_KEY, 'false')

    expect(readChartExpanded()).toBe(false)
  })

  it('stores the expanded state as a string', () => {
    storeChartExpanded(true)
    expect(localStorage.getItem(WEATHER_TOOLKIT_CHART_EXPANDED_STORAGE_KEY)).toBe('true')

    storeChartExpanded(false)
    expect(localStorage.getItem(WEATHER_TOOLKIT_CHART_EXPANDED_STORAGE_KEY)).toBe('false')
  })

  it('returns false when reading from local storage throws', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('local storage unavailable')
    })

    expect(readChartExpanded()).toBe(false)
  })

  it('does not throw when writing to local storage throws', () => {
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('local storage unavailable')
    })

    expect(() => storeChartExpanded(true)).not.toThrow()
  })
})
