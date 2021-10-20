import { TableCell } from '@material-ui/core'
import { PlanningArea } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import FireStartsCell from 'features/hfiCalculator/components/FireStartsCell'
import { calculateMeanIntensity } from 'features/hfiCalculator/components/meanIntensity'
import MeanIntensityGroupRollup from 'features/hfiCalculator/components/MeanIntensityGroupRollup'
import PrepLevelCell from 'features/hfiCalculator/components/PrepLevelCell'
import { NUM_WEEK_DAYS } from 'features/hfiCalculator/constants'
import { DailyManager } from 'features/hfiCalculator/DailyManager'
import { groupBy, range } from 'lodash'
import React from 'react'

export interface CalculatedCellsProps {
  testId?: string
  area: PlanningArea
  areaName: string
  selected: number[]
  planningAreaClass: string
  dailyManager: DailyManager
}

const CalculatedPlanningAreaCells = (props: CalculatedCellsProps) => {
  const areaDailies = props.dailyManager
    .getDailiesForArea(props.area)
    .filter(daily => props.selected.includes(daily.code))
  const dailiesByDayUTC = new Map<number, StationDaily[]>()
  const utcDict = groupBy(areaDailies, (daily: StationDaily) =>
    daily.date.toUTC().toMillis()
  )

  Object.keys(utcDict).forEach(key => {
    dailiesByDayUTC.set(Number(key), utcDict[key])
  })

  const orderedDayTimestamps = Array.from(dailiesByDayUTC.keys()).sort((a, b) => a - b)

  return (
    <React.Fragment>
      {range(NUM_WEEK_DAYS).map(i => {
        const dailies: StationDaily[] | undefined = dailiesByDayUTC.get(
          orderedDayTimestamps[i]
        )
        const meanIntensityGroup = dailies ? calculateMeanIntensity(dailies) : undefined
        return (
          <React.Fragment key={`calc-cells-${i}`}>
            <TableCell colSpan={2} className={props.planningAreaClass}></TableCell>
            <MeanIntensityGroupRollup
              area={props.area}
              dailies={dailies ? dailies : []}
              selectedStations={props.selected}
            ></MeanIntensityGroupRollup>
            <FireStartsCell areaName={props.areaName} />
            <PrepLevelCell
              meanIntensityGroup={meanIntensityGroup}
              areaName={props.areaName}
            />
          </React.Fragment>
        )
      })}
      <MeanIntensityGroupRollup
        area={props.area}
        dailies={areaDailies}
        selectedStations={props.selected}
      ></MeanIntensityGroupRollup>
      <TableCell>Test</TableCell>
    </React.Fragment>
  )
}

export default React.memo(CalculatedPlanningAreaCells)
