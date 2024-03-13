import { MorecastDraftForecast } from 'features/moreCast2/forecastDraft'
import { DraftMorecast2Rows } from 'features/moreCast2/interfaces'
import { buildValidActualRow, buildValidForecastRow } from 'features/moreCast2/rowFilters.test'
import { DateTime } from 'luxon'

const TEST_DATE = DateTime.now()
const EDITED_TEST_DATE_NUMBER = 1710187123569

describe('MorecastDraftForecast', () => {
  jest.spyOn(Date, 'now').mockReturnValue(EDITED_TEST_DATE_NUMBER)

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
    const toBeStored: DraftMorecast2Rows = { rows: mockRowData.slice(0, 4), lastEdited: Date.now() }
    const setSpy = jest.spyOn(localStorageMock, 'setItem')

    draftForecast.updateStoredDraftForecasts(mockRowData)

    expect(setSpy).toHaveBeenCalledWith(draftForecast.STORAGE_KEY, JSON.stringify(toBeStored))
  })
  it('should call getItem upon retrieval of a forecast', () => {
    const getSpy = jest.spyOn(localStorageMock, 'getItem')
    draftForecast.getStoredDraftForecasts()

    expect(getSpy).toHaveBeenCalledWith(draftForecast.STORAGE_KEY)
  })
  it('should delete saved rows from storage', () => {
    const storedDraft: DraftMorecast2Rows = { rows: mockRowData.slice(0, 4), lastEdited: Date.now() }
    const toBeStored: DraftMorecast2Rows = { rows: mockRowData.slice(2, 4), lastEdited: Date.now() }
    const savedRows = mockRowData.slice(0, 2)

    jest.spyOn(localStorageMock, 'getItem').mockReturnValue(JSON.stringify(storedDraft))
    const setSpy = jest.spyOn(localStorageMock, 'setItem')

    draftForecast.deleteRowsFromStoredDraft(savedRows)

    expect(setSpy).toHaveBeenCalledWith(draftForecast.STORAGE_KEY, JSON.stringify(toBeStored))
  })
  it('should return true if a draft forecast is stored', () => {
    const storedDraft: DraftMorecast2Rows = { rows: mockRowData.slice(0, 4), lastEdited: Date.now() }
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
