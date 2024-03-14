import { DraftMorecast2Rows, MoreCast2ForecastRow, MoreCast2Row } from 'features/moreCast2/interfaces'
import { getRowsMap, isForecastRow } from 'features/moreCast2/util'
import { DateTime } from 'luxon'

export class MorecastDraftForecast {
  public readonly STORAGE_KEY = 'morecastForecastDraft'
  private readonly localStorage: Storage

  constructor(localStorage: Storage) {
    this.localStorage = localStorage
  }

  public getStoredDraftForecasts = (): DraftMorecast2Rows => {
    const storedDraftString = this.localStorage.getItem(this.STORAGE_KEY)
    let storedDraft: DraftMorecast2Rows = { rows: [], lastEdited: null }

    if (storedDraftString) {
      storedDraft = JSON.parse(storedDraftString)
    }

    return storedDraft
  }

  private storeDraftForecasts = (forecastDraft: DraftMorecast2Rows) => {
    this.localStorage.setItem(this.STORAGE_KEY, JSON.stringify(forecastDraft))
  }

  public clearDraftForecasts = () => {
    this.localStorage.removeItem(this.STORAGE_KEY)
  }

  public updateStoredDraftForecasts = (rowsToStore: MoreCast2Row[], editDateTime: DateTime) => {
    const storedForecastsToUpdate = this.getStoredDraftForecasts()
    const storedRowsMap = getRowsMap(storedForecastsToUpdate.rows)

    rowsToStore.forEach(row => {
      storedRowsMap.set(row.id, row)
    })
    // we only need to store rows that are 'Forecast' rows
    storedForecastsToUpdate.rows = Array.from(storedRowsMap.values()).filter(row => {
      return isForecastRow(row)
    })
    storedForecastsToUpdate.lastEdited = editDateTime.toISO()

    this.storeDraftForecasts(storedForecastsToUpdate)
  }

  public deleteRowsFromStoredDraft = (savedRows: MoreCast2ForecastRow[] | MoreCast2Row[], editDateTime: DateTime) => {
    const localStoredForecast = this.getStoredDraftForecasts()
    const localStoredRows = getRowsMap(localStoredForecast.rows)
    savedRows.forEach(row => {
      localStoredRows.delete(row.id)
    })
    localStoredForecast.rows = Array.from(localStoredRows.values())
    localStoredForecast.lastEdited = editDateTime.toISO()
    this.storeDraftForecasts(localStoredForecast)
  }

  public hasDraftForecastStored = (): boolean => {
    const localStoredRows = this.getStoredDraftForecasts().rows
    return localStoredRows.length > 0
  }

  public getLastSavedDraftDateTime = (): string | undefined => {
    const storedDraftForecast = this.getStoredDraftForecasts()
    if (storedDraftForecast.lastEdited && this.hasDraftForecastStored()) {
      return DateTime.fromISO(storedDraftForecast.lastEdited).toFormat('MMMM dd, HH:mm')
    }
  }
}
