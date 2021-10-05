import { TableCell } from '@material-ui/core'
import { PlanningArea } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import FireStartsCell from 'features/hfiCalculator/components/FireStartsCell'
import MeanIntensityGroupRollup from 'features/hfiCalculator/components/MeanIntensityGroupRollup'
import PrepLevelCell from 'features/hfiCalculator/components/PrepLevelCell'
import { NUM_WEEK_DAYS } from 'features/hfiCalculator/constants'
import { calculateMultipleMeanIntensityGroups } from 'features/hfiCalculator/multipleMeanIntensity'
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
}

const CalculatedPlanningAreaCells = (props: CalculatedCellsProps) => {
  const meanIntensityGroup = calculateMultipleMeanIntensityGroups(
    props.area,
    props.weekliesByStationCode,
    props.selected
  )

  const cells = range(NUM_WEEK_DAYS).map(i => (
    <React.Fragment key={`calc-cells-${i}`}>
      <TableCell colSpan={3}></TableCell>
      <MeanIntensityGroupRollup
        area={props.area}
        dailiesMap={props.dailiesMap}
        selectedStations={props.selected}
      ></MeanIntensityGroupRollup>
      <FireStartsCell areaName={props.areaName} />
      <PrepLevelCell
        meanIntensityGroup={meanIntensityGroup}
        areaName={props.areaName}
        testid={undefined}
      />
    </React.Fragment>
  ))

  return <React.Fragment>{cells}</React.Fragment>
}

export default React.memo(CalculatedPlanningAreaCells)
