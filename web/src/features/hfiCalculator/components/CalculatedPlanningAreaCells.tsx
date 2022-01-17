import { TableCell } from '@material-ui/core'
import { PlanningArea } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import FireStartsCell from 'features/hfiCalculator/components/FireStartsCell'
import {
  calculateDailyMeanIntensities,
  calculateMaxMeanIntensityGroup
} from 'features/hfiCalculator/components/meanIntensity'
import MeanIntensityGroupRollup from 'features/hfiCalculator/components/MeanIntensityGroupRollup'
import PrepLevelCell from 'features/hfiCalculator/components/PrepLevelCell'
import { NUM_WEEK_DAYS } from 'features/hfiCalculator/constants'
import { getDailiesForArea } from 'features/hfiCalculator/util'
import { groupBy, isUndefined, range } from 'lodash'
import React from 'react'
import { calculatePrepLevel } from './prepLevel'

export interface CalculatedCellsProps {
  testId?: string
  area: PlanningArea
  dailies: StationDaily[]
  areaName: string
  selected: number[]
  planningAreaClass: string
}

const CalculatedPlanningAreaCells = (props: CalculatedCellsProps) => {
  const areaDailies = getDailiesForArea(props.area, props.dailies, props.selected)
  const utcDict = groupBy(areaDailies, (daily: StationDaily) =>
    daily.date.toUTC().toMillis()
  )

  const calculateDailyPrepLevels = () => {
    const prepLevels: (number | undefined)[] = []
    range(NUM_WEEK_DAYS).map(day => {
      const meanIntensityGroup = dailyMeanIntensityGroups[day]
      prepLevels.push(calculatePrepLevel(meanIntensityGroup))
    })
    return prepLevels
  }
  const calculateMeanPrepLevel = (
    rawMeanIntensityGroups: (number | undefined)[]
  ): number | undefined => {
    // for now, prep level calculation assumed a fixed Fire Starts value of 0-1
    if (isUndefined(rawMeanIntensityGroups)) {
      return undefined
    } else {
      const existingDailies: number[] = []
      rawMeanIntensityGroups.forEach(daily => {
        if (!isUndefined(daily)) {
          existingDailies.push(Math.round(daily))
        }
      })
      return Math.round(
        existingDailies?.reduce((a, b) => a + b, 0) / existingDailies.length
      )
    }
  }

  const dailiesByDayUTC = new Map(
    Object.entries(utcDict).map(entry => [Number(entry[0]), entry[1]])
  )

  const orderedDayTimestamps = Array.from(dailiesByDayUTC.keys()).sort((a, b) => a - b)

  const dailyMeanIntensityGroups = calculateDailyMeanIntensities(dailiesByDayUTC)

  const highestMeanIntensityGroup = calculateMaxMeanIntensityGroup(
    dailyMeanIntensityGroups
  )

  const dailyPrepLevels = calculateDailyPrepLevels()
  const meanPrepLevel = calculateMeanPrepLevel(dailyPrepLevels)

  return (
    <React.Fragment>
      {range(NUM_WEEK_DAYS).map(day => {
        const dailies: StationDaily[] | undefined = dailiesByDayUTC.get(
          orderedDayTimestamps[day]
        )
        const meanIntensityGroup = dailyMeanIntensityGroups[day]
        return (
          <React.Fragment key={`calc-cells-${day}`}>
            <TableCell colSpan={2} className={props.planningAreaClass}></TableCell>
            <MeanIntensityGroupRollup
              area={props.area}
              dailies={dailies ? dailies : []}
              selectedStations={props.selected}
              meanIntensityGroup={meanIntensityGroup}
            ></MeanIntensityGroupRollup>
            <FireStartsCell areaName={props.areaName} />
            <PrepLevelCell
              meanPrepLevelBoolean={false}
              meanIntensityGroup={meanIntensityGroup}
              areaName={props.areaName}
              meanPrepLevel={meanPrepLevel}
            />
          </React.Fragment>
        )
      })}

      <MeanIntensityGroupRollup
        area={props.area}
        dailies={areaDailies}
        selectedStations={props.selected}
        meanIntensityGroup={highestMeanIntensityGroup}
      ></MeanIntensityGroupRollup>
      <PrepLevelCell
        meanPrepLevelBoolean={true}
        meanIntensityGroup={meanPrepLevel}
        areaName={props.areaName}
        meanPrepLevel={meanPrepLevel}
      />
    </React.Fragment>
  )
}

export default React.memo(CalculatedPlanningAreaCells)
