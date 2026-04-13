import { renderHook, act, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { DateTime } from 'luxon'
import { useWxChartCache, buildChartKey } from './useWxChartCache'
import { ModelType, ModelRunHour, modelRegistry } from '@/features/weatherToolkit/weatherToolkitTypes'
import * as weatherToolkitAPI from '@wps/api/weatherToolkitAPI'

vi.mock('@wps/api/weatherToolkitAPI')

const mockBlob = new Blob(['fake image'], { type: 'image/png' })
const fakeObjectUrl = 'blob:fake-url'
const MODEL = ModelType.GDPS
const MODEL_RUN_DATE = DateTime.fromISO('2024-06-01', { zone: 'utc' })
const MODEL_RUN_HOUR = ModelRunHour.ZERO

beforeEach(() => {
  vi.clearAllMocks()
  vi.spyOn(URL, 'createObjectURL').mockReturnValue(fakeObjectUrl)
  vi.spyOn(URL, 'revokeObjectURL').mockReturnValue(undefined)
  vi.mocked(weatherToolkitAPI.getWxChart).mockResolvedValue(mockBlob)
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('buildChartKey', () => {
  it('builds the correct S3 key for GDPS', () => {
    const key = buildChartKey(ModelType.GDPS, MODEL_RUN_DATE, ModelRunHour.ZERO, 6)
    expect(key).toBe('wx_4panel_charts/20240601/model_gdps/15km/00/006/GDPS_20240601T00Z_F006_4panel.png')
  })

  it('builds the correct S3 key for RDPS', () => {
    const key = buildChartKey(ModelType.RDPS, MODEL_RUN_DATE, ModelRunHour.TWELVE, 3)
    expect(key).toBe('wx_4panel_charts/20240601/model_rdps/10km/12/003/RDPS_20240601T12Z_F003_4panel.png')
  })

  it('pads the hour to 3 digits', () => {
    const key = buildChartKey(ModelType.GDPS, MODEL_RUN_DATE, ModelRunHour.ZERO, 0)
    expect(key).toContain('/000/')
    expect(key).toContain('F000_')
  })
})

describe('useWxChartCache', () => {
  it('returns empty cache and failed set initially', () => {
    vi.mocked(weatherToolkitAPI.getWxChart).mockReturnValue(new Promise(() => {}))
    const { result } = renderHook(() => useWxChartCache(MODEL, MODEL_RUN_DATE, MODEL_RUN_HOUR, 0))
    expect(result.current.cache.size).toBe(0)
    expect(result.current.failed.size).toBe(0)
  })

  it('populates the cache with an object URL on successful fetch', async () => {
    const { result } = renderHook(() => useWxChartCache(MODEL, MODEL_RUN_DATE, MODEL_RUN_HOUR, 0))
    await waitFor(() => expect(result.current.cache.size).toBeGreaterThan(0))
    const key = buildChartKey(MODEL, MODEL_RUN_DATE, MODEL_RUN_HOUR, 0)
    expect(result.current.cache.get(key)).toBe(fakeObjectUrl)
  })

  it('pre-fetches PREFETCH_AHEAD frames ahead', async () => {
    const { interval } = modelRegistry[MODEL]
    const PREFETCH_AHEAD = 5
    const currentHour = 0
    const expectedFetches = PREFETCH_AHEAD + 1

    const { result } = renderHook(() => useWxChartCache(MODEL, MODEL_RUN_DATE, MODEL_RUN_HOUR, currentHour))
    await waitFor(() => expect(result.current.cache.size).toBe(expectedFetches))
    expect(weatherToolkitAPI.getWxChart).toHaveBeenCalledTimes(expectedFetches)

    for (let h = 0; h <= PREFETCH_AHEAD * interval; h += interval) {
      const key = buildChartKey(MODEL, MODEL_RUN_DATE, MODEL_RUN_HOUR, h)
      expect(weatherToolkitAPI.getWxChart).toHaveBeenCalledWith(key)
    }
  })

  it('clamps prefetch window to maxHour', async () => {
    const { interval, maxHour } = modelRegistry[MODEL] // GDPS: interval=6, maxHour=240
    // 228 + 5*6 = 258 > 240, so the window should be clamped to 240
    const currentHour = 228
    const expectedHours: number[] = []
    for (let h = currentHour; h <= maxHour; h += interval) {
      expectedHours.push(h)
    }

    const { result } = renderHook(() => useWxChartCache(MODEL, MODEL_RUN_DATE, MODEL_RUN_HOUR, currentHour))
    await waitFor(() => expect(result.current.cache.size).toBe(expectedHours.length))

    for (const h of expectedHours) {
      const key = buildChartKey(MODEL, MODEL_RUN_DATE, MODEL_RUN_HOUR, h)
      expect(weatherToolkitAPI.getWxChart).toHaveBeenCalledWith(key)
    }
    const beyondKey = buildChartKey(MODEL, MODEL_RUN_DATE, MODEL_RUN_HOUR, maxHour + interval)
    expect(weatherToolkitAPI.getWxChart).not.toHaveBeenCalledWith(beyondKey)
  })

  it('adds failed keys to the failed set on fetch error', async () => {
    vi.mocked(weatherToolkitAPI.getWxChart).mockRejectedValue(new Error('network error'))
    const { result } = renderHook(() => useWxChartCache(MODEL, MODEL_RUN_DATE, MODEL_RUN_HOUR, 0))
    await waitFor(() => expect(result.current.failed.size).toBeGreaterThan(0))
    const key = buildChartKey(MODEL, MODEL_RUN_DATE, MODEL_RUN_HOUR, 0)
    expect(result.current.failed.has(key)).toBe(true)
    expect(result.current.cache.size).toBe(0)
  })

  it('re-fetches a failed key when the effect re-runs and moves it from failed to cache on success', async () => {
    const { interval } = modelRegistry[MODEL] // GDPS: interval=6
    // Start at currentHour=interval (hour 6) and fail only that key; the rest succeed.
    // Then move to currentHour=0 so the effect re-runs with hour 6 still in the window.
    const failedHour = interval
    const failedKey = buildChartKey(MODEL, MODEL_RUN_DATE, MODEL_RUN_HOUR, failedHour)

    vi.mocked(weatherToolkitAPI.getWxChart).mockImplementation(key =>
      key === failedKey ? Promise.reject(new Error('network error')) : Promise.resolve(mockBlob)
    )

    const { result, rerender } = renderHook(
      ({ currentHour }: { currentHour: number }) => useWxChartCache(MODEL, MODEL_RUN_DATE, MODEL_RUN_HOUR, currentHour),
      { initialProps: { currentHour: failedHour } }
    )

    await waitFor(() => expect(result.current.failed.has(failedKey)).toBe(true))
    expect(result.current.cache.has(failedKey)).toBe(false)

    // All fetches now succeed; move currentHour so the effect re-runs with failedHour still in window
    vi.mocked(weatherToolkitAPI.getWxChart).mockResolvedValue(mockBlob)
    act(() => rerender({ currentHour: 0 }))

    await waitFor(() => expect(result.current.cache.has(failedKey)).toBe(true))
    expect(result.current.failed.has(failedKey)).toBe(false)
  })

  it('removes a key from the fetching set after a successful fetch so it can be re-fetched if needed', async () => {
    const { result, rerender } = renderHook(
      ({ modelRunDate }: { modelRunDate: DateTime }) => useWxChartCache(MODEL, modelRunDate, MODEL_RUN_HOUR, 0),
      { initialProps: { modelRunDate: MODEL_RUN_DATE } }
    )
    await waitFor(() => expect(result.current.cache.size).toBeGreaterThan(0))
    const callCountAfterFirst = vi.mocked(weatherToolkitAPI.getWxChart).mock.calls.length

    // Change params to clear the cache, then restore original params — the key
    // should be re-fetched rather than silently skipped due to a stale fetching entry.
    act(() => rerender({ modelRunDate: DateTime.fromISO('2024-06-02', { zone: 'utc' }) }))
    act(() => rerender({ modelRunDate: MODEL_RUN_DATE }))

    await waitFor(() =>
      expect(vi.mocked(weatherToolkitAPI.getWxChart).mock.calls.length).toBeGreaterThan(callCountAfterFirst)
    )
    const key = buildChartKey(MODEL, MODEL_RUN_DATE, MODEL_RUN_HOUR, 0)
    expect(result.current.cache.get(key)).toBe(fakeObjectUrl)
  })

  it('does not fetch the same key twice', async () => {
    const { result, rerender } = renderHook(() => useWxChartCache(MODEL, MODEL_RUN_DATE, MODEL_RUN_HOUR, 0))
    await waitFor(() => expect(result.current.cache.size).toBeGreaterThan(0))
    const callCountAfterFirst = vi.mocked(weatherToolkitAPI.getWxChart).mock.calls.length

    rerender()
    expect(vi.mocked(weatherToolkitAPI.getWxChart).mock.calls.length).toBe(callCountAfterFirst)
  })

  it('resets cache and revokes object URLs when model params change', async () => {
    const { result, rerender } = renderHook(
      ({ model, modelRunHour }: { model: ModelType; modelRunHour: ModelRunHour }) =>
        useWxChartCache(model, MODEL_RUN_DATE, modelRunHour, 0),
      { initialProps: { model: ModelType.GDPS, modelRunHour: ModelRunHour.ZERO } }
    )
    await waitFor(() => expect(result.current.cache.size).toBeGreaterThan(0))

    act(() => {
      rerender({ model: ModelType.RDPS, modelRunHour: ModelRunHour.ZERO })
    })

    expect(result.current.cache.size).toBe(0)
    expect(result.current.failed.size).toBe(0)
    expect(URL.revokeObjectURL).toHaveBeenCalledWith(fakeObjectUrl)
  })

  it('revokes all object URLs on unmount', async () => {
    const { result, unmount } = renderHook(() => useWxChartCache(MODEL, MODEL_RUN_DATE, MODEL_RUN_HOUR, 0))
    await waitFor(() => expect(result.current.cache.size).toBeGreaterThan(0))

    unmount()

    expect(URL.revokeObjectURL).toHaveBeenCalledWith(fakeObjectUrl)
  })

  it('does not update state after model params change (stale generation guard)', async () => {
    let resolveFirst!: (blob: Blob) => void
    const slowFetch = new Promise<Blob>(resolve => {
      resolveFirst = resolve
    })
    // Default all calls to a never-resolving promise so new-generation fetches don't populate the cache.
    // The first call (old generation) uses slowFetch so we can resolve it manually.
    vi.mocked(weatherToolkitAPI.getWxChart).mockReturnValue(new Promise(() => {}))
    vi.mocked(weatherToolkitAPI.getWxChart).mockReturnValueOnce(slowFetch)

    const { result, rerender } = renderHook(
      ({ modelRunHour }: { modelRunHour: ModelRunHour }) => useWxChartCache(MODEL, MODEL_RUN_DATE, modelRunHour, 0),
      { initialProps: { modelRunHour: ModelRunHour.ZERO } }
    )

    // Change params to bump the generation before the first fetch resolves
    act(() => {
      rerender({ modelRunHour: ModelRunHour.TWELVE })
    })

    // Resolve the stale fetch — it should be discarded
    await act(async () => {
      resolveFirst(mockBlob)
    })

    expect(result.current.cache.size).toBe(0)
  })
})
