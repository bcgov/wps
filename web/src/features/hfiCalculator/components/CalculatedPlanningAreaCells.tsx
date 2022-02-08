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
  setNewFireStarts: (
    areaName: string,
    dayOffset: number,
    newFireStarts: FireStarts
  ) => void
  planningAreaClass: string
  numPrepDays: number
}

const CalculatedPlanningAreaCells = (props: CalculatedCellsProps) => {
  const allPlanningAreaDailies = props.planningAreaResult.dailyResults.flatMap(
    result => result.dailies
  )
  return (
    <React.Fragment>
      {range(props.numPrepDays).map(day => {
        const meanIntensityGroup =
          props.planningAreaResult.dailyResults[day]?.meanIntensityGroup
        const prepLevel = props.planningAreaResult.dailyResults[day]?.prepLevel
        const fireStarts = props.planningAreaResult.dailyResults[day]?.fireStarts

        return (
          <React.Fragment key={`calc-cells-${day}`}>
            <TableCell colSpan={2} className={props.planningAreaClass}></TableCell>
            <MeanIntensityGroupRollup
              area={props.area}
              dailies={allPlanningAreaDailies ? allPlanningAreaDailies : []}
              selectedStationCodes={props.selectedStationCodes}
              meanIntensityGroup={meanIntensityGroup}
            />
            <TableCell>
              <FireStartsDropdown
                fireStarts={fireStarts}
                areaName={props.area.name}
                dayOffset={day}
                setFireStarts={props.setNewFireStarts}
              />
            </TableCell>
            <PrepLevelCell
              toolTipText={
                'Cannot calculate prep level. Please check the daily forecast using the tabs above.'
              }
              prepLevel={prepLevel}
            />
          </React.Fragment>
        )
      })}

      <MeanIntensityGroupRollup
        area={props.area}
        dailies={allPlanningAreaDailies}
        selectedStationCodes={props.selectedStationCodes}
        meanIntensityGroup={props.planningAreaResult.highestDailyIntensityGroup}
      ></MeanIntensityGroupRollup>
      <MeanPrepLevelCell
        areaName={props.areaName}
        meanPrepLevel={props.planningAreaResult.meanPrepLevel}
        emptyOrIncompleteForecast={
          allPlanningAreaDailies.length === 0 || !props.planningAreaResult.allDailiesValid
        }
      />
    </React.Fragment>
  )
}

export default React.memo(CalculatedPlanningAreaCells)
