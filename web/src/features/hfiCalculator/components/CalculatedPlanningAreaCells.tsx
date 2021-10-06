import { TableCell } from '@material-ui/core'
import { PlanningArea } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import FireStartsCell from 'features/hfiCalculator/components/FireStartsCell'
import {
  calculateMeanIntensityGroup,
  getDailiesByWeekDay
} from 'features/hfiCalculator/components/meanIntensity'
import MeanIntensityGroupRollup from 'features/hfiCalculator/components/MeanIntensityGroupRollup'
import PrepLevelCell from 'features/hfiCalculator/components/PrepLevelCell'
import { NUM_WEEK_DAYS } from 'features/hfiCalculator/constants'
import { range } from 'lodash'
import React from 'react'

export interface CalculatedCellsProps {
  testId?: string
  area: PlanningArea
  areaName: string
  selected: number[]
  weekliesByStationCode: Map<number, StationDaily[]>
  weekliesByUTC: Map<number, StationDaily[]>
  dailiesMap: Map<number, StationDaily>
  planningAreaClass: string
}

const CalculatedPlanningAreaCells = (props: CalculatedCellsProps) => {
  const orderedDayTimestamps = Array.from(props.weekliesByUTC.keys()).sort(
    (a, b) => a - b
  )

  const cells = range(NUM_WEEK_DAYS).map(i => {
    const stationsWithDaily = getDailiesByWeekDay(
      props.area,
      orderedDayTimestamps[i],
      props.weekliesByUTC,
      props.selected
    )
    const meanIntensityGroup = calculateMeanIntensityGroup(
      stationsWithDaily,
      props.selected
    )
    return (
      <React.Fragment key={`calc-cells-${i}`}>
        <TableCell colSpan={3} className={props.planningAreaClass}></TableCell>
        <MeanIntensityGroupRollup
          area={props.area}
          stationsWithDaily={stationsWithDaily}
          selectedStations={props.selected}
        ></MeanIntensityGroupRollup>
        <FireStartsCell areaName={props.areaName} />
        <PrepLevelCell
          meanIntensityGroup={meanIntensityGroup}
          areaName={props.areaName}
        />
      </React.Fragment>
    )
  })

  return <React.Fragment>{cells}</React.Fragment>
}

export default React.memo(CalculatedPlanningAreaCells)
