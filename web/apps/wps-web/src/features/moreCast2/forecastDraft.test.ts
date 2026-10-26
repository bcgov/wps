import { ModelChoice } from '@wps/api/moreCast2API'
import * as DateUtils from '@wps/utils/date'
import { MorecastDraftForecast } from 'features/moreCast2/forecastDraft'
import type { DraftMorecast2Rows, MoreCast2Row } from 'features/moreCast2/interfaces'
import { buildValidActualRow, buildValidForecastRow } from 'features/moreCast2/rowFilters.test'
import { DateTime } from 'luxon'
import { vi } from 'vitest'

const TEST_DATE = DateTime.fromISO('2024-01-01T00:00:00.000-08:00')

describe('MorecastDraftForecast', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  const localStorageMock: Storage = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    length: 0,
    clear: vi.fn(),
    key: vi.fn()
  }

  const draftForecast = new MorecastDraftForecast(localStorageMock)

  const mockRowData = [
    buildValidForecastRow(111, TEST_DATE.plus({ days: 1 })),
    buildValidForecastRow(111, TEST_DATE.plus({ days: 2 })),
    buildValidForecastRow(222, TEST_DATE.plus({ days: 1 })),
    buildValidForecastRow(222, TEST_DATE.plus({ days: 2 })),
    buildValidActualRow(222, TEST_DATE.minus({ days: 1 })),
    buildValidActualRow(222, TEST_DATE.minus({ days: 2 })),
    buildValidForecastRow(111, TEST_DATE.minus({ days: 1 }))
  ]

  it('should only store current forecast rows', () => {
    vi.spyOn(DateUtils, 'getDateTimeNowPST').mockReturnValue(TEST_DATE)
    const toBeStored: DraftMorecast2Rows = { rows: mockRowData.slice(0, 4), lastEdited: TEST_DATE }
    const setSpy = vi.spyOn(localStorageMock, 'setItem')

    draftForecast.updateStoredDraftForecasts(mockRowData, TEST_DATE)

    expect(setSpy).toHaveBeenCalledWith(draftForecast.STORAGE_KEY, JSON.stringify(toBeStored))
  })
  it('should call getItem upon retrieval of a forecast', () => {
    const getSpy = vi.spyOn(localStorageMock, 'getItem')
    draftForecast.getStoredDraftForecasts()

    expect(getSpy).toHaveBeenCalledWith(draftForecast.STORAGE_KEY)
  })
  it('should restore null prediction values as NaN', () => {
    const storedRow = buildValidForecastRow(111, TEST_DATE.plus({ days: 1 }))
    storedRow.tempForecast!.value = null as unknown as number
    storedRow.ffmcCalcForecast = { choice: ModelChoice.NULL, value: null as unknown as number }
    const storedDraft: DraftMorecast2Rows = { rows: [storedRow], lastEdited: TEST_DATE }

    vi.spyOn(localStorageMock, 'getItem').mockReturnValue(JSON.stringify(storedDraft))

    const restoredDraft = draftForecast.getStoredDraftForecasts()

    expect(Number.isNaN(restoredDraft?.rows[0].tempForecast?.value)).toBe(true)
    expect(Number.isNaN(restoredDraft?.rows[0].ffmcCalcForecast?.value)).toBe(true)
  })
  it('should delete saved rows from storage', () => {
    const storedDraft: DraftMorecast2Rows = { rows: mockRowData.slice(0, 4), lastEdited: TEST_DATE }
    const toBeStored: DraftMorecast2Rows = { rows: mockRowData.slice(2, 4), lastEdited: TEST_DATE }
    const savedRows = mockRowData.slice(0, 2)

    vi.spyOn(localStorageMock, 'getItem').mockReturnValue(JSON.stringify(storedDraft))
    const setSpy = vi.spyOn(localStorageMock, 'setItem')

    draftForecast.deleteRowsFromStoredDraft(savedRows)

    expect(setSpy).toHaveBeenCalledWith(draftForecast.STORAGE_KEY, JSON.stringify(toBeStored))
  })
  it('should return true if a draft forecast is stored', () => {
    const storedDraft: DraftMorecast2Rows = { rows: mockRowData.slice(0, 4), lastEdited: TEST_DATE }
    vi.spyOn(localStorageMock, 'getItem').mockReturnValue(JSON.stringify(storedDraft))

    const draftStored = draftForecast.hasDraftForecastStored()
    expect(draftStored).toBe(true)
  })
  it('should return false if a draft forecast is not stored', () => {
    vi.spyOn(localStorageMock, 'getItem').mockReturnValue('')

    const draftStored = draftForecast.hasDraftForecastStored()
    expect(draftStored).toBe(false)
  })
})

describe('draft reconciliation', () => {
  const draft = new MorecastDraftForecast(localStorage)
  const lastEdited = TEST_DATE.minus({ hours: 1 })
  const seedDraft = (rows: MoreCast2Row[]) => {
    localStorage.setItem(draft.STORAGE_KEY, JSON.stringify({ rows, lastEdited }))
  }

  beforeEach(() => {
    localStorage.clear()
    vi.spyOn(DateUtils, 'getDateTimeNowPST').mockReturnValue(TEST_DATE)
  })

  afterEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('restores dates and offsets without changing stored prediction values', () => {
    const forDate = DateTime.fromISO('2024-01-02T20:00:00Z', { setZone: true })
    seedDraft([buildValidForecastRow(111, forDate)])

    const restored = draft.getStoredDraftForecasts()!

    expect(DateTime.isDateTime(restored.rows[0].forDate)).toBe(true)
    expect(restored.rows[0].forDate.toISO()).toBe(forDate.toISO())
    expect(restored.lastEdited.toISO()).toBe(lastEdited.toISO())
    expect(restored.rows[0].tempForecast?.value).toBe(2)
    expect(Number.isNaN(restored.rows[0].grassCuringForecast?.value)).toBe(true)
  })

  it('removes matching actuals and expired rows while preserving unrelated drafts', () => {
    const rows = [
      buildValidForecastRow(111, TEST_DATE),
      buildValidForecastRow(111, TEST_DATE.plus({ days: 1 })),
      buildValidForecastRow(222, TEST_DATE),
      buildValidForecastRow(333, TEST_DATE.minus({ days: 1 }))
    ]
    seedDraft(rows)

    draft.reconcileWithActuals([{ station_code: 111, utc_timestamp: TEST_DATE.toISO()! }])

    const remaining = draft.getStoredDraftForecasts()!
    expect(remaining.rows.map(row => row.id)).toEqual([rows[1].id, rows[2].id])
    expect(remaining.lastEdited.toISO()).toBe(lastEdited.toISO())
  })

  it('matches actuals by instant even when their timezone offsets differ', () => {
    const forDate = DateTime.fromISO('2024-01-01T20:00:00Z', { setZone: true })
    seedDraft([buildValidForecastRow(111, forDate)])

    draft.reconcileWithActuals([{ station_code: 111, utc_timestamp: '2024-01-01T12:00:00-08:00' }])

    expect(localStorage.getItem(draft.STORAGE_KEY)).toBeNull()
    expect(draft.hasDraftForecastStored()).toBe(false)
    expect(draft.getLastSavedDraftDateTime()).toBeUndefined()
  })

  it('keeps current drafts when no actuals are returned and repeated cleanup changes nothing', () => {
    seedDraft([buildValidForecastRow(111, TEST_DATE)])
    const original = localStorage.getItem(draft.STORAGE_KEY)

    draft.reconcileWithActuals([])
    draft.reconcileWithActuals([])

    expect(localStorage.getItem(draft.STORAGE_KEY)).toBe(original)
  })

  it('removes expired rows from storage even when no stations have actuals', () => {
    seedDraft([buildValidForecastRow(111, TEST_DATE.minus({ days: 1 }))])

    draft.reconcileWithActuals([])

    expect(localStorage.getItem(draft.STORAGE_KEY)).toBeNull()
  })

  it('filters expired stored rows when another draft is edited', () => {
    const expired = buildValidForecastRow(111, TEST_DATE.minus({ days: 1 }))
    const current = buildValidForecastRow(222, TEST_DATE)
    const edited = buildValidForecastRow(333, TEST_DATE)
    seedDraft([expired, current])

    draft.updateStoredDraftForecasts([edited], TEST_DATE)

    const stored = draft.getStoredDraftForecasts()!
    expect(stored.rows.map(row => row.id)).toEqual([current.id, edited.id])
    expect(stored.lastEdited.toISO()).toBe(TEST_DATE.toISO())
  })

  it('preserves the edit timestamp when published rows are deleted', () => {
    const saved = buildValidForecastRow(111, TEST_DATE)
    const remaining = buildValidForecastRow(222, TEST_DATE)
    seedDraft([saved, remaining])

    draft.deleteRowsFromStoredDraft([saved])

    expect(draft.getStoredDraftForecasts()!.rows.map(row => row.id)).toEqual([remaining.id])
    expect(draft.getStoredDraftForecasts()!.lastEdited.toISO()).toBe(lastEdited.toISO())
  })

  it('removes the storage key when the final draft is published', () => {
    const saved = buildValidForecastRow(111, TEST_DATE)
    seedDraft([saved])

    draft.deleteRowsFromStoredDraft([saved])

    expect(localStorage.getItem(draft.STORAGE_KEY)).toBeNull()
    expect(draft.getLastSavedDraftDateTime()).toBeUndefined()
  })

  it('hides the draft indicator for an empty stored draft and clears it on reconciliation', () => {
    seedDraft([])
    expect(draft.hasDraftForecastStored()).toBe(false)
    expect(draft.getLastSavedDraftDateTime()).toBeUndefined()

    draft.reconcileWithActuals([])

    expect(localStorage.getItem(draft.STORAGE_KEY)).toBeNull()
  })

  it('does not store empty drafts', () => {
    draft.createStoredForecast([], TEST_DATE)
    expect(localStorage.getItem(draft.STORAGE_KEY)).toBeNull()
  })
})
