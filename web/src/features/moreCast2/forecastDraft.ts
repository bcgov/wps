import { DraftMorecast2Rows, MoreCast2ForecastRow, MoreCast2Row } from 'features/moreCast2/interfaces'
import { rowContainsActual } from 'features/moreCast2/util'

export const MORECAST_ROW_LOCAL_STORAGE_KEY = 'morecastForecastDraft'

export const storeDraftForecasts = (forecastDraft: DraftMorecast2Rows) => {
  localStorage.setItem(MORECAST_ROW_LOCAL_STORAGE_KEY, JSON.stringify(forecastDraft))
}

export const updateStoredDraftForecasts = (rowsToStore: MoreCast2Row[]) => {
  const storedForecastsToUpdate = getStoredDraftForecasts()
  const storedRowsMap = getRowsMap(storedForecastsToUpdate.rows)

  rowsToStore.forEach(row => {
    storedRowsMap.set(row.id, row)
  })
  // we only need to store rows that are 'Forecast' rows
  storedForecastsToUpdate.rows = Array.from(storedRowsMap.values()).filter(row => {
    return !rowContainsActual(row)
  })
  storedForecastsToUpdate.lastEdited = Date.now()

  storeDraftForecasts(storedForecastsToUpdate)
}

export const getStoredDraftForecasts = (): DraftMorecast2Rows => {
  const storedDraftString = localStorage.getItem(MORECAST_ROW_LOCAL_STORAGE_KEY)
  let storedDraft: DraftMorecast2Rows = { rows: [], lastEdited: 0 }

  if (storedDraftString) {
    storedDraft = JSON.parse(storedDraftString)
  }

  return storedDraft
}

export const deleteSavedRowsFromLocalStorage = (savedRows: MoreCast2ForecastRow[]) => {
  const localStoredForecast = getStoredDraftForecasts()
  const localStoredRows = getRowsMap(localStoredForecast.rows)
  savedRows.forEach(row => {
    localStoredRows.delete(row.id)
  })
  localStoredForecast.rows = Array.from(localStoredRows.values())
  localStoredForecast.lastEdited = Date.now()
  storeDraftForecasts(localStoredForecast)
}

export const getRowsMap = (morecastRows: MoreCast2Row[]): Map<string, MoreCast2Row> => {
  const morecastRowMap = new Map<string, MoreCast2Row>()
  morecastRows.forEach((row: MoreCast2Row) => {
    morecastRowMap.set(row.id, row)
  })
  return morecastRowMap
}

export const clearLocalStorageRows = () => {
  localStorage.removeItem(MORECAST_ROW_LOCAL_STORAGE_KEY)
}
