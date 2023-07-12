import { TableCell } from '@mui/material'
import { FuelType, PlanningArea } from 'api/hfiCalculatorAPI'
import MeanIntensityGroupRollup from 'features/hfiCalculator/components/MeanIntensityGroupRollup'
import PrepLevelCell from 'features/hfiCalculator/components/PrepLevelCell'
import { range } from 'lodash'
import React from 'react'
import MeanPrepLevelCell from './MeanPrepLevelCell'
import { FireStartRange, PlanningAreaResult, StationInfo } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import FireStartsDropdown from 'features/hfiCalculator/components/FireStartsDropdown'
import { PlanningAreaTableCell } from 'features/hfiCalculator/components/StyledPlanningArea'

export interface CalculatedCellsProps {
  testId?: string
  area: PlanningArea
  areaName: string
  planningAreaResult: PlanningAreaResult
  fireStartsEnabled: boolean
  setNewFireStarts: (areaId: number, dayOffset: number, newFireStarts: FireStartRange) => void
  numPrepDays: number
  fireStartRanges: FireStartRange[]
  fuelTypes: FuelType[]
  planningAreaStationInfo: { [key: number]: StationInfo[] }
}

const CalculatedPlanningAreaCells = (props: CalculatedCellsProps) => {
  const allPlanningAreaDailies = props.planningAreaResult.daily_results.flatMap(result =>
    result.dailies.map(validatedDaily => validatedDaily.daily)
  )
  return (
    <React.Fragment>
      {range(props.numPrepDays).map(day => {
        const meanIntensityGroup = props.planningAreaResult.daily_results[day]?.mean_intensity_group
        const prepLevel = props.planningAreaResult.daily_results[day]?.prep_level
        const fireStarts = props.planningAreaResult.daily_results[day]?.fire_starts

        return (
          <React.Fragment key={`calc-cells-${day}`}>
            <PlanningAreaTableCell colSpan={2}></PlanningAreaTableCell>
            <MeanIntensityGroupRollup
              area={props.area}
              dailies={allPlanningAreaDailies ? allPlanningAreaDailies : []}
              meanIntensityGroup={meanIntensityGroup}
              planningAreaStationInfo={props.planningAreaStationInfo}
              fuelTypes={props.fuelTypes}
            />
            <TableCell>
              <FireStartsDropdown
                fireStarts={fireStarts}
                fireStartRanges={props.fireStartRanges}
                areaId={props.planningAreaResult.planning_area_id}
                dayOffset={day}
                setFireStarts={props.setNewFireStarts}
                fireStartsEnabled={props.fireStartsEnabled}
              />
            </TableCell>
            <PrepLevelCell
              toolTipText={'Cannot calculate prep level. Please check the daily forecast using the tabs above.'}
              prepLevel={prepLevel}
            />
          </React.Fragment>
        )
      })}

      <MeanIntensityGroupRollup
        area={props.area}
        dailies={allPlanningAreaDailies}
        meanIntensityGroup={props.planningAreaResult.highest_daily_intensity_group}
        planningAreaStationInfo={props.planningAreaStationInfo}
        fuelTypes={props.fuelTypes}
      ></MeanIntensityGroupRollup>
      <MeanPrepLevelCell
        areaName={props.areaName}
        meanPrepLevel={props.planningAreaResult.mean_prep_level}
        emptyOrIncompleteForecast={allPlanningAreaDailies.length === 0 || !props.planningAreaResult.all_dailies_valid}
      />
    </React.Fragment>
  )
}

export default React.memo(CalculatedPlanningAreaCells)
