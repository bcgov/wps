import { FireCentre, PlanningArea, WeatherStation } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import _, { isNull, isUndefined } from 'lodash'
import { getDailiesByStationCode } from 'features/hfiCalculator/util'
import { dailyTableColumnLabels } from 'features/hfiCalculator/components/DailyViewTable'
import { toUnicode } from 'punycode'

// the number of decimal places to round to
const DECIMAL_PLACES = 1

interface DailyHFITableStationRow {
  weatherStation: WeatherStation
  dailyData: StationDaily
}

interface WeeklyHFITableStationRow {
  weatherStation: WeatherStation
  dataByDay: StationDaily[]
}

interface WeeklyHFITableStationRow {
  weatherStation: WeatherStation
}

interface HFITablePlanningAreaRow {
  planningArea: PlanningArea
  fireStarts: string
  prepLevel: number
}

export class RowManager {
  public static exportDailyRowsAsStrings = (
    fireCentres: Record<string, FireCentre>,
    dailies: StationDaily[]
  ): string => {
    const rowsAsStrings: string[] = []

    rowsAsStrings.push(dailyTableColumnLabels.toString())

    Object.entries(fireCentres).forEach(([_, centre]) => {
      rowsAsStrings.push(centre.name)
      Object.entries(centre.planning_areas).forEach(([_, area]) => {
        rowsAsStrings.push(area.name)
        Object.entries(area.stations).forEach(([_, station]) => {
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
    tableRows: WeeklyHFITableStationRow[]
  ): string[][] => {
    const rowsAsStrings: string[][] = []

    return rowsAsStrings
  }
}
