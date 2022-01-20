import { FireCentre, PlanningArea } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import { isNull, isUndefined, range } from 'lodash'
import * as CSV from 'csv-string'
import { getZoneFromAreaName } from 'features/hfiCalculator/util'
import { dailyTableColumnLabels } from 'features/hfiCalculator/components/DailyViewTable'
import { columnLabelsForEachDayInWeek } from 'features/hfiCalculator/components/WeeklyViewTable'
import { isValidGrassCure } from 'features/hfiCalculator/validation'
import { DECIMAL_PLACES } from 'features/hfiCalculator/constants'
import { HFIResult } from 'features/hfiCalculator/slices/hfiCalculatorSlice'

// padding for station-data cells (e.g., station name, fuel type) before dates begin
const NUM_STATION_DATA_COLS = 5

// padding for station-specific cells (repeated daily) that will be left empty in planning area row
// (e.g., ROS, HFI)
const NUM_DAILY_DATA_COLS_THAT_DONT_APPLY_TO_AREA = 2
// padding for end-of-week cells (e.g., Highest Daily FIG, Calc. Prep)
const NUM_WEEKLY_SUMMARY_CELLS = 2

const printGrassCurePercentage = (daily: StationDaily): string => {
  if (!isUndefined(daily) && !isNull(daily.grass_cure_percentage)) {
    return daily.grass_cure_percentage.toString()
  } else {
    return 'ND'
  }
}

export class FormatTableAsCSV {
  public static exportDailyRowsAsStrings = (
    fireCentres: Record<string, FireCentre>,
    planningAreaHFIResults: {
      [key: string]: HFIResult
    }
  ): string => {
    const rowsAsStrings: string[] = []

    rowsAsStrings.push(CSV.stringify(dailyTableColumnLabels.toString()))

    Object.entries(fireCentres).forEach(([, centre]) => {
      rowsAsStrings.push(CSV.stringify(centre.name))
      Object.entries(centre.planning_areas)
        .sort((a, b) =>
          getZoneFromAreaName(a[1].name) < getZoneFromAreaName(b[1].name) ? -1 : 1
        )
        .forEach(([, area]) => {
          const stationCodesInArea: number[] = []
          Object.entries(area.stations).forEach(([, station]) => {
            stationCodesInArea.push(station.code)
          })
          const hfiResult = planningAreaHFIResults[area.name]
          const areaDailies = hfiResult.dailies
          const meanIntensityGroup = hfiResult.dailyMeanIntensity
          const areaPrepLevel = hfiResult.dailyPrepLevels
          rowsAsStrings.push(
            CSV.stringify(
              `${area.name}, ${Array(21).join(
                ','
              )} ${meanIntensityGroup}, 0-1, ${areaPrepLevel}` // fire starts of 0-1 is hard-coded for now
            )
          )
          Object.entries(area.stations).forEach(([, station]) => {
            const rowArray: string[] = []
            const daily = areaDailies.filter(daily => daily.code === station.code)[0]

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
            rowArray.push(grassCureError ? 'ERROR' : printGrassCurePercentage(daily))
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

            rowsAsStrings.push(CSV.stringify(rowArray))
          })
        })
    })
    return rowsAsStrings.join('')
  }

  static buildAreaWeeklySummaryString = (
    area: PlanningArea,
    planningAreaHFIResults: {
      [key: string]: HFIResult
    }
  ): string[] => {
    const areaWeeklySummary: string[] = [
      area.name,
      ...Array(NUM_STATION_DATA_COLS - NUM_DAILY_DATA_COLS_THAT_DONT_APPLY_TO_AREA).fill(
        ' '
      )
    ]

    const stationCodesInArea: number[] = []
    Object.entries(area.stations).forEach(([, station]) => {
      stationCodesInArea.push(station.code)
    })
    const hfiResult = planningAreaHFIResults[area.name]
    const areaDailies = hfiResult.dailies

    Array.from(range(areaDailies.length)).forEach(day => {
      const dailyIntensityGroup = hfiResult.dailyMeanIntensityGroups[day]
      const areaDailyPrepLevel = hfiResult.dailyPrepLevels
      const fireStarts = '0-1' // hard-coded for now

      areaWeeklySummary.push(
        ...Array(NUM_DAILY_DATA_COLS_THAT_DONT_APPLY_TO_AREA).fill('')
      )
      areaWeeklySummary.push(
        isUndefined(dailyIntensityGroup) ? 'ND' : dailyIntensityGroup.toString()
      )
      areaWeeklySummary.push(fireStarts.toString())
      areaWeeklySummary.push(
        isUndefined(areaDailyPrepLevel) ? 'ND' : areaDailyPrepLevel.toString()
      )
    })
    areaWeeklySummary.push(String(hfiResult.maxMeanIntensityGroup))
    areaWeeklySummary.push(
      isUndefined(hfiResult.meanPrepLevel) ? 'ND' : String(hfiResult.meanPrepLevel)
    )
    return areaWeeklySummary
  }

  public static exportWeeklyRowsAsStrings = (
    fireCentres: Record<string, FireCentre>,
    planningAreaHFIResults: {
      [key: string]: HFIResult
    }
  ): string => {
    // build up array of string arrays, which will be converted to CSV string at end
    // each string array represents one row of table
    const rowsAsStringArrays: string[][] = []
    const dateSet = new Set<string>()

    // dailies.flatMap(dailyRecord => {
    //   dateSet.add(
    //     `${dailyRecord.date.weekdayShort} ${dailyRecord.date.monthShort} ${dailyRecord.date.day}`
    //   )
    // })
    // build header row of dates
    const dateRow: string[] = Array(NUM_STATION_DATA_COLS - 1).fill(' ')
    Array.from(dateSet).forEach(date => {
      dateRow.push(date)
      dateRow.push(...Array(columnLabelsForEachDayInWeek.length - 1).fill(' '))
    })
    rowsAsStringArrays.push(dateRow)

    // according to docs for csv-string library (https://www.npmjs.com/package/csv-string#api-documentation),
    // \n char should be used as newline indicator regardless of OS. Later on in code, these strings will be
    // "CSV stringified", so using /n here as line separator
    // rowsAsStringArrays.push(weeklyTableColumnLabels(numPrepDays))

    Object.entries(fireCentres).forEach(([, centre]) => {
      rowsAsStringArrays.push([centre.name])

      Object.entries(centre.planning_areas)
        .sort((a, b) =>
          getZoneFromAreaName(a[1].name) < getZoneFromAreaName(b[1].name) ? -1 : 1
        )
        .forEach(([, area]) => {
          const areaHFIResult = planningAreaHFIResults[area.name]
          rowsAsStringArrays.push(
            this.buildAreaWeeklySummaryString(area, planningAreaHFIResults)
          )

          Object.entries(area.stations).forEach(([, station]) => {
            const dailiesForStation = areaHFIResult.dailies
            const grassCureError = !isValidGrassCure(
              dailiesForStation[0],
              station.station_props
            )

            const rowArray: string[] = []

            rowArray.push(station.station_props.name + ' (' + station.code + ')')
            if (
              isUndefined(station.station_props.elevation) ||
              isNull(station.station_props.elevation)
            ) {
              rowArray.push('ND')
            } else {
              rowArray.push(station.station_props.elevation.toString())
            }
            rowArray.push(station.station_props.fuel_type.abbrev)
            rowArray.push(
              grassCureError ? 'ERROR' : printGrassCurePercentage(dailiesForStation[0])
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
              rowArray.push(...Array(NUM_WEEKLY_SUMMARY_CELLS).fill(''))
            })

            rowArray.push(...Array(NUM_WEEKLY_SUMMARY_CELLS).fill(''))

            const rowString = rowArray
            rowsAsStringArrays.push(rowString)
          })
        })
    })
    return CSV.stringify(rowsAsStringArrays)
  }
}
