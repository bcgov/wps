import { TableCell } from '@material-ui/core'
import { PlanningArea } from 'api/hfiCalcAPI'
import MeanIntensityGroupRollup from 'features/hfiCalculator/components/MeanIntensityGroupRollup'
import PrepLevelCell from 'features/hfiCalculator/components/PrepLevelCell'
import { range } from 'lodash'
import React from 'react'
import MeanPrepLevelCell from './MeanPrepLevelCell'
import {
  FireStarts,
  PlanningAreaResult
} from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import FireStartsDropdown from 'features/hfiCalculator/components/FireStartsDropdown'

export interface CalculatedCellsProps {
  testId?: string
  area: PlanningArea
  areaName: string
  planningAreaResult: PlanningAreaResult
  selectedStationCodes: number[]
  planningAreaClass: string
  numPrepDays: number
}

const CalculatedPlanningAreaCells = (props: CalculatedCellsProps) => {
  const allDailies = props.planningAreaResult.dailyResults.flatMap(
    result => result.dailies
  )
  return (
    <React.Fragment>
      {range(props.numPrepDays).map(day => {
        const meanIntensityGroup =
          props.planningAreaResult.dailyResults[day]?.meanIntensityGroup
        const prepLevel = props.planningAreaResult.dailyResults[day]?.prepLevel

        return (
          <React.Fragment key={`calc-cells-${day}`}>
            <TableCell colSpan={2} className={props.planningAreaClass}></TableCell>
            <MeanIntensityGroupRollup
              area={props.area}
              dailies={allDailies ? allDailies : []}
              selectedStationCodes={props.selectedStationCodes}
              meanIntensityGroup={meanIntensityGroup}
            />
            <FireStartsDropdown
              areaName={props.area.name}
              dayOffset={day}
              setFireStarts={function (
                areaName: string,
                dayOffSets: number,
                newFireStarts: FireStarts
              ): void {
                console.log(
                  `areaName: ${areaName}, dayOffset: ${dayOffSets}, newFireStarts: ${newFireStarts.label}`
                )
              }}
            />
            <PrepLevelCell prepLevel={prepLevel} />
          </React.Fragment>
        )
      })}

      <MeanIntensityGroupRollup
        area={props.area}
        dailies={allDailies}
        selectedStationCodes={props.selectedStationCodes}
        meanIntensityGroup={props.planningAreaResult.highestDailyIntensityGroup}
      ></MeanIntensityGroupRollup>
      <MeanPrepLevelCell
        areaName={props.areaName}
        meanPrepLevel={props.planningAreaResult.meanPrepLevel}
      />
    </React.Fragment>
  )
}

export default React.memo(CalculatedPlanningAreaCells)
