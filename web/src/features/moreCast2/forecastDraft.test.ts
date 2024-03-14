import { MorecastDraftForecast } from 'features/moreCast2/forecastDraft'
import { DraftMorecast2Rows } from 'features/moreCast2/interfaces'
import { buildValidActualRow, buildValidForecastRow } from 'features/moreCast2/rowFilters.test'
import { DateTime } from 'luxon'
import * as DateUtils from 'utils/date'

const TEST_DATE = DateTime.fromISO('2024-01-01T00:00:00.000-08:00')

describe('MorecastDraftForecast', () => {
  afterEach(() => {
    jest.clearAllMocks()
  })
  const localStorageMock: Storage = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    length: 0,
    clear: jest.fn(),
    key: jest.fn()
  }

  const draftForecast = new MorecastDraftForecast(localStorageMock)

  const mockRowData = [
    buildValidForecastRow(111, TEST_DATE.plus({ days: 1 })),
    buildValidForecastRow(111, TEST_DATE.plus({ days: 2 })),
    buildValidForecastRow(222, TEST_DATE.plus({ days: 1 })),
    buildValidForecastRow(222, TEST_DATE.plus({ days: 2 })),
    buildValidActualRow(222, TEST_DATE.minus({ days: 1 })),
    buildValidActualRow(222, TEST_DATE.minus({ days: 2 }))
  ]

  it('should only store forecast rows', () => {
    jest.spyOn(DateUtils, 'getDateTimeNowPST').mockReturnValue(TEST_DATE)
    const toBeStored: DraftMorecast2Rows = { rows: mockRowData.slice(0, 4), lastEdited: TEST_DATE.toISO() }
    const setSpy = jest.spyOn(localStorageMock, 'setItem')

    draftForecast.updateStoredDraftForecasts(mockRowData, TEST_DATE)

    expect(setSpy).toHaveBeenCalledWith(draftForecast.STORAGE_KEY, JSON.stringify(toBeStored))
  })
  it('should call getItem upon retrieval of a forecast', () => {
    const getSpy = jest.spyOn(localStorageMock, 'getItem')
    draftForecast.getStoredDraftForecasts()

    expect(getSpy).toHaveBeenCalledWith(draftForecast.STORAGE_KEY)
  })
  it('should delete saved rows from storage', () => {
    const storedDraft: DraftMorecast2Rows = { rows: mockRowData.slice(0, 4), lastEdited: TEST_DATE.toISO() }
    const toBeStored: DraftMorecast2Rows = { rows: mockRowData.slice(2, 4), lastEdited: TEST_DATE.toISO() }
    const savedRows = mockRowData.slice(0, 2)

    jest.spyOn(localStorageMock, 'getItem').mockReturnValue(JSON.stringify(storedDraft))
    const setSpy = jest.spyOn(localStorageMock, 'setItem')

    draftForecast.deleteRowsFromStoredDraft(savedRows, TEST_DATE)

    expect(setSpy).toHaveBeenCalledWith(draftForecast.STORAGE_KEY, JSON.stringify(toBeStored))
  })
  it('should return true if a draft forecast is stored', () => {
    const storedDraft: DraftMorecast2Rows = { rows: mockRowData.slice(0, 4), lastEdited: TEST_DATE.toISO() }
    jest.spyOn(localStorageMock, 'getItem').mockReturnValue(JSON.stringify(storedDraft))

    const draftStored = draftForecast.hasDraftForecastStored()
    expect(draftStored).toBe(true)
  })
  it('should return false if a draft forecast is not stored', () => {
    jest.spyOn(localStorageMock, 'getItem').mockReturnValue('')

    const draftStored = draftForecast.hasDraftForecastStored()
    expect(draftStored).toBe(false)
  })
})
