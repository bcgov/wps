import { TableCell } from '@mui/material'
import { PlanningArea } from 'api/hfiCalcAPI'
import MeanIntensityGroupRollup from 'features/hfiCalculator/components/MeanIntensityGroupRollup'
import PrepLevelCell from 'features/hfiCalculator/components/PrepLevelCell'
import { range } from 'lodash'
import React from 'react'
import MeanPrepLevelCell from './MeanPrepLevelCell'
import {
  FireStartRange,
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
    areaId: number,
    dayOffset: number,
    newFireStarts: FireStartRange
  ) => void
  planningAreaClass: string
  numPrepDays: number
  fireStartRanges: FireStartRange[]
}

const CalculatedPlanningAreaCells = (props: CalculatedCellsProps) => {
  const allPlanningAreaDailies = props.planningAreaResult.daily_results.flatMap(result =>
    result.dailies.map(validatedDaily => validatedDaily.daily)
  )
  return (
    <React.Fragment>
      {range(props.numPrepDays).map(day => {
        const meanIntensityGroup =
          props.planningAreaResult.daily_results[day]?.mean_intensity_group
        const prepLevel = props.planningAreaResult.daily_results[day]?.prep_level
        const fireStarts = props.planningAreaResult.daily_results[day]?.fire_starts

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
                fireStartRanges={props.fireStartRanges}
                areaId={props.planningAreaResult.planning_area_id}
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
        meanIntensityGroup={props.planningAreaResult.highest_daily_intensity_group}
      ></MeanIntensityGroupRollup>
      <MeanPrepLevelCell
        areaName={props.areaName}
        meanPrepLevel={props.planningAreaResult.mean_prep_level}
        emptyOrIncompleteForecast={
          allPlanningAreaDailies.length === 0 ||
          !props.planningAreaResult.all_dailies_valid
        }
      />
    </React.Fragment>
  )
}

export default React.memo(CalculatedPlanningAreaCells)
