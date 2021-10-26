import { FireCentre } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import { isNull, isUndefined } from 'lodash'
import { getDailiesByStationCode } from 'features/hfiCalculator/util'
import { dailyTableColumnLabels } from 'features/hfiCalculator/components/DailyViewTable'
import { weeklyTableColumnLabels } from 'features/hfiCalculator/components/WeeklyViewTable'

// the number of decimal places to round to
const DECIMAL_PLACES = 1

export class RowManager {
  public static exportDailyRowsAsStrings = (
    fireCentres: Record<string, FireCentre>,
    dailies: StationDaily[]
  ): string => {
    const rowsAsStrings: string[] = []

    rowsAsStrings.push(dailyTableColumnLabels.toString())

    Object.entries(fireCentres).forEach(([, centre]) => {
      rowsAsStrings.push(centre.name)
      Object.entries(centre.planning_areas).forEach(([, area]) => {
        rowsAsStrings.push(area.name)
        Object.entries(area.stations).forEach(([, station]) => {
          const rowArray: string[] = []
          const daily = getDailiesByStationCode(dailies, station.code)[0]

          rowArray.push(station.station_props.name + ' (' + station.code + ')')
          rowArray.push(
            isUndefined(station.station_props.elevation) ||
              isNull(station.station_props.elevation)
              ? ''
              : station.station_props.elevation?.toString()
          )
          rowArray.push(station.station_props.fuel_type.abbrev)
          rowArray.push(!isUndefined(daily) ? daily.status : '')
          rowArray.push(
            !isUndefined(daily) ? daily.temperature.toFixed(DECIMAL_PLACES) : ''
          )
          rowArray.push(
            !isUndefined(daily) ? daily.relative_humidity.toFixed(DECIMAL_PLACES) : ''
          )
          rowArray.push(!isUndefined(daily) ? daily.wind_direction.toString() : '')
          rowArray.push(
            !isUndefined(daily) ? daily.wind_speed.toFixed(DECIMAL_PLACES) : ''
          )
          rowArray.push(
            !isUndefined(daily) ? daily.precipitation.toFixed(DECIMAL_PLACES) : ''
          )
          rowArray.push(
            !isUndefined(daily) && !isNull(daily.grass_cure_percentage)
              ? daily.grass_cure_percentage.toString()
              : ''
          )
          rowArray.push(!isUndefined(daily) ? daily.ffmc.toString() : '')
          rowArray.push(!isUndefined(daily) ? daily.dmc.toString() : '')
          rowArray.push(!isUndefined(daily) ? daily.dc.toString() : '')
          rowArray.push(!isUndefined(daily) ? daily.isi.toString() : '')
          rowArray.push(!isUndefined(daily) ? daily.bui.toString() : '')
          rowArray.push(!isUndefined(daily) ? daily.fwi.toString() : '')
          rowArray.push(
            !isUndefined(daily) && !isNull(daily.danger_class)
              ? daily.danger_class.toString()
              : ''
          )
          rowArray.push(
            !isUndefined(daily) ? daily.rate_of_spread.toFixed(DECIMAL_PLACES) : ''
          )
          rowArray.push(!isUndefined(daily) ? daily.hfi.toFixed(DECIMAL_PLACES) : '')
          rowArray.push(
            !isUndefined(daily)
              ? daily.sixty_minute_fire_size.toFixed(DECIMAL_PLACES)
              : ''
          )
          rowArray.push(!isUndefined(daily) ? daily.fire_type : '')
          rowArray.push(!isUndefined(daily) ? daily.intensity_group.toString() : '')

          rowsAsStrings.push(rowArray.toString())
        })
      })
    })
    return rowsAsStrings.join('\r\n')
  }

  public static exportWeeklyRowsAsStrings = (
    fireCentres: Record<string, FireCentre>,
    dailies: StationDaily[]
  ): string => {
    const rowsAsStrings: string[] = []
    const dateSet = new Set()

    dailies.flatMap(dailyRecord => {
      dateSet.add(
        `${dailyRecord.date.weekdayShort} ${dailyRecord.date.monthShort} ${dailyRecord.date.day}`
      )
    })
    // build header row of dates
    rowsAsStrings.push(Array(5).join(',').concat(Array.from(dateSet).join(',,,,,'))) // padding for date-less column labels
    rowsAsStrings.push(weeklyTableColumnLabels.toString())

    Object.entries(fireCentres).forEach(([, centre]) => {
      rowsAsStrings.push(centre.name)
      Object.entries(centre.planning_areas).forEach(([, area]) => {
        rowsAsStrings.push(area.name)
        Object.entries(area.stations).forEach(([, station]) => {
          const dailiesForStation = getDailiesByStationCode(dailies, station.code)

          const rowArray: string[] = []

          rowArray.push(station.station_props.name + ' (' + station.code + ')')
          rowArray.push(
            isUndefined(station.station_props.elevation) ||
              isNull(station.station_props.elevation)
              ? ''
              : station.station_props.elevation.toString()
          )
          rowArray.push(station.station_props.fuel_type.abbrev)
          // TODO: grass cure
          rowArray.push(
            !isUndefined(dailiesForStation[0]) &&
              !isNull(dailiesForStation[0].grass_cure_percentage)
              ? dailiesForStation[0].grass_cure_percentage.toString()
              : ''
          )

          dailiesForStation.forEach(day => {
            rowArray.push(
              !isUndefined(day) ? day.rate_of_spread.toFixed(DECIMAL_PLACES) : ''
            )
            rowArray.push(!isUndefined(day) ? day.hfi.toFixed(DECIMAL_PLACES) : '')
            rowArray.push(!isUndefined(day) ? day.intensity_group.toString() : '')
            rowArray.push(Array(2).join(','))
          })

          rowArray.push(Array(2).join(','))

          rowsAsStrings.push(rowArray.toString())
        })
      })
    })

    return rowsAsStrings.join('\r\n')
  }
}
