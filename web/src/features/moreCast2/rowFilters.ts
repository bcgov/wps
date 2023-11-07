import { MoreCast2Row } from 'features/moreCast2/interfaces'
import { validForecastPredicate, validActualPredicate, validActualOrForecastPredicate } from 'features/moreCast2/util'

export const filterAllVisibleRowsForSimulation = (rows: MoreCast2Row[]): MoreCast2Row[] | undefined => {
  const forecasts = rows.filter(validForecastPredicate)
  const actuals = rows.filter(validActualPredicate)
  const mostRecentActualMap = new Map<number, MoreCast2Row>()
  let rowsForSimulation = undefined

  if (forecasts.length > 0) {
    for (const row of actuals) {
      const recentActual = mostRecentActualMap.get(row.stationCode)
      if (!recentActual || recentActual.forDate < row.forDate) {
        mostRecentActualMap.set(row.stationCode, row)
      }
    }
    const mostRecentActuals = Array.from(mostRecentActualMap.values())
    rowsForSimulation = [...mostRecentActuals, ...forecasts]
  }

  return rowsForSimulation
}

export const filterRowsForSimulationFromEdited = (
  editedRow: MoreCast2Row,
  allRows: MoreCast2Row[]
): MoreCast2Row[] | undefined => {
  if (validForecastPredicate(editedRow)) {
    const validRowsForStation = allRows.filter(
      row => row.stationCode === editedRow.stationCode && validActualOrForecastPredicate(row)
    )

    const yesterday = editedRow.forDate.minus({ days: 1 })
    const yesterdayRow = validRowsForStation.find(row => row.forDate.toISODate() === yesterday.toISODate())

    if (yesterdayRow) {
      const rowsForSimulation = validRowsForStation.filter(row => row.forDate >= yesterday)
      return rowsForSimulation
    } else return undefined
  }
}
