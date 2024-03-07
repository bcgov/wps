import { DraftMorecast2Rows, MoreCast2ForecastRow, MoreCast2Row } from 'features/moreCast2/interfaces'
import { rowContainsActual } from 'features/moreCast2/util'
import { DateTime } from 'luxon'

export class MorecastDraftForecast {
  private readonly STORAGE_KEY = 'morecastForecastDraft'
  private localStorage: Storage

  constructor(localStorage: Storage) {
    this.localStorage = localStorage
  }

  public getStoredDraftForecasts = (): DraftMorecast2Rows => {
    const storedDraftString = this.localStorage.getItem(this.STORAGE_KEY)
    let storedDraft: DraftMorecast2Rows = { rows: [], lastEdited: 0 }

    if (storedDraftString) {
      storedDraft = JSON.parse(storedDraftString)
    }

    return storedDraft
  }

  public storeDraftForecasts = (forecastDraft: DraftMorecast2Rows) => {
    this.localStorage.setItem(this.STORAGE_KEY, JSON.stringify(forecastDraft))
  }

  public clearDraftForecast = () => {
    this.localStorage.removeItem(this.STORAGE_KEY)
  }

  public updateStoredDraftForecasts = (rowsToStore: MoreCast2Row[]) => {
    const storedForecastsToUpdate = this.getStoredDraftForecasts()
    const storedRowsMap = this.getRowsMap(storedForecastsToUpdate.rows)

    rowsToStore.forEach(row => {
      storedRowsMap.set(row.id, row)
    })
    // we only need to store rows that are 'Forecast' rows
    storedForecastsToUpdate.rows = Array.from(storedRowsMap.values()).filter(row => {
      return !rowContainsActual(row)
    })
    storedForecastsToUpdate.lastEdited = Date.now()

    this.storeDraftForecasts(storedForecastsToUpdate)
  }

  public deleteRowsFromStoredDraft = (savedRows: MoreCast2ForecastRow[] | MoreCast2Row[]) => {
    const localStoredForecast = this.getStoredDraftForecasts()
    const localStoredRows = this.getRowsMap(localStoredForecast.rows)
    savedRows.forEach(row => {
      localStoredRows.delete(row.id)
    })
    localStoredForecast.rows = Array.from(localStoredRows.values())
    localStoredForecast.lastEdited = Date.now()
    this.storeDraftForecasts(localStoredForecast)
  }

  public getRowsMap = (morecastRows: MoreCast2Row[]): Map<string, MoreCast2Row> => {
    const morecastRowMap = new Map<string, MoreCast2Row>()
    morecastRows.forEach((row: MoreCast2Row) => {
      morecastRowMap.set(row.id, row)
    })
    return morecastRowMap
  }

  public hasDraftForecastStored = (): boolean => {
    const localStoredRows = this.getStoredDraftForecasts().rows
    return localStoredRows.length > 0
  }

  public getLastSavedDraftDateTime = (): string | undefined => {
    const storedDraftForecast = this.getStoredDraftForecasts()
    return storedDraftForecast.lastEdited !== 0
      ? DateTime.fromMillis(storedDraftForecast.lastEdited).toFormat('MMMM dd, HH:mm')
      : undefined
  }
}
