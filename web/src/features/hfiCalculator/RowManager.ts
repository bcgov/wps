import { FireCentre, PlanningArea } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import { groupBy, isNull, isUndefined, range } from 'lodash'
import { getDailiesByStationCode, getDailiesForArea } from 'features/hfiCalculator/util'
import { dailyTableColumnLabels } from 'features/hfiCalculator/components/DailyViewTable'
import { weeklyTableColumnLabels } from 'features/hfiCalculator/components/WeeklyViewTable'
import {
  calculateDailyMeanIntensities,
  calculateMaxMeanIntensityGroup,
  calculateMeanIntensity,
  calculateMeanIntensityGroupLevel
} from 'features/hfiCalculator/components/meanIntensity'
import { calculatePrepLevel } from 'features/hfiCalculator/components/prepLevel'
import { isValidGrassCure } from './validation'
import { NUM_WEEK_DAYS } from './constants'

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
      Object.entries(centre.planning_areas)
        .sort((a, b) => (a[1].name.slice(-3) < b[1].name.slice(-3) ? -1 : 1)) // sort by zone code
        .forEach(([, area]) => {
          const stationCodesInArea: number[] = []
          Object.entries(area.stations).forEach(([, station]) => {
            stationCodesInArea.push(station.code)
          })
          const areaDailies = getDailiesForArea(area, dailies, stationCodesInArea)
          const meanIntensityGroup = calculateMeanIntensity(areaDailies)
          const areaPrepLevel = calculatePrepLevel(meanIntensityGroup)
          rowsAsStrings.push(
            `${area.name}, ${Array(21).join(
              ','
            )} ${meanIntensityGroup}, 0-1, ${areaPrepLevel}` // fire starts of 0-1 is hard-coded for now
          )
          Object.entries(area.stations).forEach(([, station]) => {
            const rowArray: string[] = []
            const daily = getDailiesByStationCode(dailies, station.code)[0]

            const grassCureError = !isValidGrassCure(daily, station.station_props)

            rowArray.push(station.station_props.name + ' (' + station.code + ')')
            rowArray.push(
              isUndefined(station.station_props.elevation) ||
                isNull(station.station_props.elevation)
                ? 'ND'
                : station.station_props.elevation?.toString()
            )
            rowArray.push(station.station_props.fuel_type.abbrev)
            rowArray.push(!isUndefined(daily) ? daily.status : 'ND')
            rowArray.push(
              !isUndefined(daily) && !isUndefined(daily.temperature)
                ? daily.temperature.toFixed(DECIMAL_PLACES)
                : 'ND'
            )
            rowArray.push(
              !isUndefined(daily) && !isUndefined(daily.relative_humidity)
                ? daily.relative_humidity.toFixed(DECIMAL_PLACES)
                : 'ND'
            )
            rowArray.push(
              !isUndefined(daily) && !isNull(daily.wind_direction)
                ? daily.wind_direction.toString()
                : 'ND'
            )
            rowArray.push(
              !isUndefined(daily) && !isUndefined(daily.wind_speed)
                ? daily.wind_speed.toFixed(DECIMAL_PLACES)
                : 'ND'
            )
            rowArray.push(
              !isUndefined(daily) && !isUndefined(daily.precipitation)
                ? daily.precipitation.toFixed(DECIMAL_PLACES)
                : 'ND'
            )
            rowArray.push(
              grassCureError
                ? 'ERROR'
                : !isUndefined(daily) && !isNull(daily.grass_cure_percentage)
                ? daily.grass_cure_percentage.toString()
                : 'ND'
            )
            rowArray.push(!isUndefined(daily) ? daily.ffmc.toString() : 'ND')
            rowArray.push(!isUndefined(daily) ? daily.dmc.toString() : 'ND')
            rowArray.push(!isUndefined(daily) ? daily.dc.toString() : 'ND')
            rowArray.push(!isUndefined(daily) ? daily.isi.toString() : 'ND')
            rowArray.push(!isUndefined(daily) ? daily.bui.toString() : 'ND')
            rowArray.push(!isUndefined(daily) ? daily.fwi.toString() : 'ND')
            rowArray.push(
              !isUndefined(daily) && !isNull(daily.danger_class)
                ? daily.danger_class.toString()
                : 'ND'
            )
            rowArray.push(
              !isUndefined(daily) && !isUndefined(daily.rate_of_spread) && !grassCureError
                ? daily.rate_of_spread.toFixed(DECIMAL_PLACES)
                : 'ND'
            )
            rowArray.push(
              !isUndefined(daily) && !isUndefined(daily.hfi) && !grassCureError
                ? daily.hfi.toFixed(DECIMAL_PLACES)
                : 'ND'
            )
            rowArray.push(
              !isUndefined(daily) &&
                !isUndefined(daily.sixty_minute_fire_size) &&
                !grassCureError
                ? daily.sixty_minute_fire_size.toFixed(DECIMAL_PLACES)
                : 'ND'
            )
            rowArray.push(!isUndefined(daily) && !grassCureError ? daily.fire_type : 'ND')
            rowArray.push(
              !isUndefined(daily) && !grassCureError
                ? daily.intensity_group.toString()
                : 'ND'
            )

            rowsAsStrings.push(rowArray.toString())
          })
        })
    })
    return rowsAsStrings.join('\r\n')
  }

  static buildAreaWeeklySummaryString = (
    area: PlanningArea,
    dailies: StationDaily[]
  ): string => {
    let areaWeeklySummaryString = `${area.name},,,,`

    const stationCodesInArea: number[] = []
    Object.entries(area.stations).forEach(([, station]) => {
      stationCodesInArea.push(station.code)
    })
    const areaDailies = getDailiesForArea(area, dailies, stationCodesInArea)

    const utcDict = groupBy(areaDailies, (daily: StationDaily) =>
      daily.date.toUTC().toMillis()
    )

    const dailiesByDayUTC = new Map(
      Object.entries(utcDict).map(entry => [Number(entry[0]), entry[1]])
    )
    const dailyMeanIntensityGroups = calculateDailyMeanIntensities(dailiesByDayUTC)
    const highestMeanIntensityGroup = calculateMaxMeanIntensityGroup(
      dailyMeanIntensityGroups
    )
    const meanIntensityGroup = calculateMeanIntensityGroupLevel(dailyMeanIntensityGroups)
    const calcPrepLevel = calculatePrepLevel(meanIntensityGroup)

    Array.from(range(NUM_WEEK_DAYS)).forEach(day => {
      const dailyIntensityGroup = dailyMeanIntensityGroups[day]
      const areaDailyPrepLevel = calculatePrepLevel(dailyIntensityGroup)
      const fireStarts = '0-1' // hard-coded for now

      areaWeeklySummaryString = areaWeeklySummaryString.concat(
        `,, ${dailyIntensityGroup}, ${fireStarts}, ${areaDailyPrepLevel},`
      )
    })
    areaWeeklySummaryString = areaWeeklySummaryString.concat(
      `${highestMeanIntensityGroup}, ${calcPrepLevel}`
    )

    return areaWeeklySummaryString
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
    rowsAsStrings.push(Array(5).join(',').concat(Array.from(dateSet).join(',,,,,')))
    rowsAsStrings.push(weeklyTableColumnLabels.toString())

    Object.entries(fireCentres).forEach(([, centre]) => {
      rowsAsStrings.push(centre.name)
      Object.entries(centre.planning_areas)
        .sort((a, b) => (a[1].name.slice(-3) < b[1].name.slice(-3) ? -1 : 1)) // sort by zone code
        .forEach(([, area]) => {
          rowsAsStrings.push(this.buildAreaWeeklySummaryString(area, dailies))
          Object.entries(area.stations).forEach(([, station]) => {
            const dailiesForStation = getDailiesByStationCode(dailies, station.code)
            const grassCureError = !isValidGrassCure(dailies[0], station.station_props)

            const rowArray: string[] = []

            rowArray.push(station.station_props.name + ' (' + station.code + ')')
            rowArray.push(
              isUndefined(station.station_props.elevation) ||
                isNull(station.station_props.elevation)
                ? 'ND'
                : station.station_props.elevation.toString()
            )
            rowArray.push(station.station_props.fuel_type.abbrev)
            rowArray.push(
              grassCureError
                ? 'ERROR'
                : !isUndefined(dailiesForStation[0]) &&
                  !isNull(dailiesForStation[0].grass_cure_percentage)
                ? dailiesForStation[0].grass_cure_percentage.toString()
                : 'ND'
            )

            dailiesForStation.forEach(day => {
              rowArray.push(
                !isUndefined(day) && !grassCureError
                  ? day.rate_of_spread.toFixed(DECIMAL_PLACES)
                  : 'ND'
              )
              rowArray.push(
                !isUndefined(day) && !grassCureError
                  ? day.hfi.toFixed(DECIMAL_PLACES)
                  : 'ND'
              )
              rowArray.push(
                !isUndefined(day) && !grassCureError
                  ? day.intensity_group.toString()
                  : 'ND'
              )
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
