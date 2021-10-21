import { FireCentre, PlanningArea, WeatherStation } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import assert from 'assert'
import _, { isNull, isUndefined, merge, uniqBy } from 'lodash'

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
    dailiesMap: Map<number, StationDaily>
  ): string => {
    const rowsAsStrings: string[] = []
    tableRows.forEach(row => {
      const rowArray: string[] = []
      rowArray.push(
        row.weatherStation.station_props.name + ' (' + row.weatherStation.code + ')'
      )
      rowArray.push(
        isUndefined(row.weatherStation.station_props.elevation) ||
          isNull(row.weatherStation.station_props.elevation)
          ? ''
          : row.weatherStation.station_props.elevation.toString()
      )
      rowArray.push(row.weatherStation.station_props.fuel_type.abbrev)
      rowArray.push(row.dailyData.status)
      rowArray.push(row.dailyData.temperature.toFixed(DECIMAL_PLACES))
      rowArray.push(row.dailyData.relative_humidity.toFixed(DECIMAL_PLACES))
      rowArray.push(row.dailyData.wind_direction.toString())
      rowArray.push(row.dailyData.wind_speed.toFixed(DECIMAL_PLACES))
      rowArray.push(row.dailyData.precipitation.toFixed(DECIMAL_PLACES))
      rowArray.push(row.dailyData.grass_cure_percentage.toString())
      rowArray.push(row.dailyData.ffmc.toString())
      rowArray.push(row.dailyData.dmc.toString())
      rowArray.push(row.dailyData.dc.toString())
      rowArray.push(row.dailyData.isi.toString())
      rowArray.push(row.dailyData.bui.toString())
      rowArray.push(row.dailyData.fwi.toString())
      rowArray.push(row.dailyData.danger_class.toString())
      rowArray.push(row.dailyData.rate_of_spread.toFixed(DECIMAL_PLACES))
      rowArray.push(row.dailyData.hfi.toFixed(DECIMAL_PLACES))
      rowArray.push(row.dailyData.sixty_minute_fire_size.toFixed(DECIMAL_PLACES))
      rowArray.push(row.dailyData.fire_type)
      rowArray.push(row.dailyData.intensity_group.toString())

      rowsAsStrings.push(rowArray.toString())
    })

    return rowsAsStrings.join('\n')
  }

  public static exportWeeklyRowsAsStrings = (
    tableRows: WeeklyHFITableStationRow[]
  ): string[][] => {
    const rowsAsStrings: string[][] = []

    return rowsAsStrings
  }
}
