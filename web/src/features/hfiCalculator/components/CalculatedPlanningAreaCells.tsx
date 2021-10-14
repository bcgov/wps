import { TableCell } from '@material-ui/core'
import { PlanningArea } from 'api/hfiCalcAPI'
import { selectHFIDailies } from 'app/rootReducer'
import FireStartsCell from 'features/hfiCalculator/components/FireStartsCell'
import { calculateMeanIntensityGroup } from 'features/hfiCalculator/components/meanIntensity'
import MeanIntensityGroupRollup from 'features/hfiCalculator/components/MeanIntensityGroupRollup'
import PrepLevelCell from 'features/hfiCalculator/components/PrepLevelCell'
import { NUM_WEEK_DAYS } from 'features/hfiCalculator/constants'
import { buildWeekliesByUTC, getDailiesByWeekDay } from 'features/hfiCalculator/util'
import { range } from 'lodash'
import React from 'react'
import { useSelector } from 'react-redux'

export interface CalculatedCellsProps {
  testId?: string
  area: PlanningArea
  areaName: string
  selected: number[]
  planningAreaClass: string
}

const CalculatedPlanningAreaCells = (props: CalculatedCellsProps) => {
  const { dailies } = useSelector(selectHFIDailies)

  const weekliesByUTC = buildWeekliesByUTC(dailies)
  const orderedDayTimestamps = Array.from(weekliesByUTC.keys()).sort((a, b) => a - b)

  const cells = range(NUM_WEEK_DAYS).map(i => {
    const stationsWithDaily = getDailiesByWeekDay(
      props.area,
      orderedDayTimestamps[i],
      weekliesByUTC,
      props.selected
    )
    const meanIntensityGroup = calculateMeanIntensityGroup(
      stationsWithDaily,
      props.selected
    )
    return (
      <React.Fragment key={`calc-cells-${i}`}>
        <TableCell colSpan={2} className={props.planningAreaClass}></TableCell>
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
