import { DraftMorecast2Rows, MoreCast2ForecastRow, MoreCast2Row } from 'features/moreCast2/interfaces'
import { getRowsMap, isForecastRow } from 'features/moreCast2/util'
import { DateTime } from 'luxon'

export class MorecastDraftForecast {
  public readonly STORAGE_KEY = 'morecastForecastDraft'
  private readonly localStorage: Storage

  constructor(localStorage: Storage) {
    this.localStorage = localStorage
  }

  public getStoredDraftForecasts = (): DraftMorecast2Rows | undefined => {
    const storedDraftString = this.localStorage.getItem(this.STORAGE_KEY)

    if (storedDraftString) {
      const storedDraft = JSON.parse(storedDraftString)
      storedDraft.lastEdited = storedDraft.lastEdited ? DateTime.fromISO(storedDraft.lastEdited) : undefined
      return storedDraft
    }
  }

  private storeDraftForecasts = (forecastDraft: DraftMorecast2Rows) => {
    this.localStorage.setItem(
      this.STORAGE_KEY,
      JSON.stringify({ rows: forecastDraft.rows, lastEdited: forecastDraft.lastEdited })
    )
  }

  public clearDraftForecasts = () => {
    this.localStorage.removeItem(this.STORAGE_KEY)
  }

  public createStoredForecast = (rowsToStore: MoreCast2Row[], editDateTime: DateTime): void => {
    const forecastRows = rowsToStore.filter(row => isForecastRow(row))
    const forecastDraft: DraftMorecast2Rows = { rows: forecastRows, lastEdited: editDateTime }

    this.storeDraftForecasts(forecastDraft)
  }

  public updateStoredDraftForecasts = (rowsToStore: MoreCast2Row[], editDateTime: DateTime) => {
    const storedForecastsToUpdate = this.getStoredDraftForecasts()
    if (!storedForecastsToUpdate) {
      this.createStoredForecast(rowsToStore, editDateTime)
    } else {
      const storedRowsMap = getRowsMap(storedForecastsToUpdate.rows)

      rowsToStore.forEach(row => {
        storedRowsMap.set(row.id, row)
      })
      // we only need to store rows that are 'Forecast' rows
      storedForecastsToUpdate.rows = Array.from(storedRowsMap.values()).filter(row => {
        return isForecastRow(row)
      })
      storedForecastsToUpdate.lastEdited = editDateTime

      this.storeDraftForecasts(storedForecastsToUpdate)
    }
  }

  public deleteRowsFromStoredDraft = (savedRows: MoreCast2ForecastRow[] | MoreCast2Row[], editDateTime: DateTime) => {
    const localStoredForecast = this.getStoredDraftForecasts()
    if (localStoredForecast) {
      const localStoredRows = getRowsMap(localStoredForecast.rows)
      savedRows.forEach(row => {
        localStoredRows.delete(row.id)
      })
      localStoredForecast.rows = Array.from(localStoredRows.values())
      localStoredForecast.lastEdited = editDateTime
      this.storeDraftForecasts(localStoredForecast)
    }
  }

  public hasDraftForecastStored = (): boolean => {
    const localStoredForecast = this.getStoredDraftForecasts()
    return !!localStoredForecast && localStoredForecast.rows.length > 0
  }

  public getLastSavedDraftDateTime = (): string | undefined => {
    const storedDraftForecast = this.getStoredDraftForecasts()
    if (storedDraftForecast) {
      return storedDraftForecast.lastEdited.toFormat('MMMM dd, HH:mm')
    }
  }
}
