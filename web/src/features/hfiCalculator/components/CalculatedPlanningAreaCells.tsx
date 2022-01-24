import { TableCell } from '@material-ui/core'
import { PlanningArea } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import FireStartsCell from 'features/hfiCalculator/components/FireStartsCell'
import MeanIntensityGroupRollup from 'features/hfiCalculator/components/MeanIntensityGroupRollup'
import PrepLevelCell from 'features/hfiCalculator/components/PrepLevelCell'
import { groupBy, range } from 'lodash'
import React from 'react'
import MeanPrepLevelCell from './MeanPrepLevelCell'
import { HFIResult } from 'features/hfiCalculator/slices/hfiCalculatorSlice'

export interface CalculatedCellsProps {
  testId?: string
  area: PlanningArea
  areaName: string
  areaHFIResults: HFIResult
  selectedStationCodes: number[]
  planningAreaClass: string
  numPrepDays: number
}

const CalculatedPlanningAreaCells = (props: CalculatedCellsProps) => {
  const utcDict = groupBy(props.areaHFIResults.dailies, (daily: StationDaily) =>
    daily.date.toUTC().toMillis()
  )

  const dailiesByDayUTC = new Map(
    Object.entries(utcDict).map(entry => [Number(entry[0]), entry[1]])
  )

  const orderedDayTimestamps = Array.from(dailiesByDayUTC.keys()).sort((a, b) => a - b)

  return (
    <React.Fragment>
      {range(props.numPrepDays).map(day => {
        const dailies: StationDaily[] | undefined = dailiesByDayUTC.get(
          orderedDayTimestamps[day]
        )
        const meanIntensityGroup = props.areaHFIResults.dailyMeanIntensityGroups[day]
        const prepLevel = props.areaHFIResults.dailyPrepLevels[day]
        return (
          <React.Fragment key={`calc-cells-${day}`}>
            <TableCell colSpan={2} className={props.planningAreaClass}></TableCell>
            <MeanIntensityGroupRollup
              area={props.area}
              dailies={dailies ? dailies : []}
              selectedStationCodes={props.selectedStationCodes}
              meanIntensityGroup={meanIntensityGroup}
            />
            <FireStartsCell areaName={props.areaName} />
            <PrepLevelCell prepLevel={prepLevel} />
          </React.Fragment>
        )
      })}

      <MeanIntensityGroupRollup
        area={props.area}
        dailies={props.areaHFIResults.dailies}
        selectedStationCodes={props.selectedStationCodes}
        meanIntensityGroup={props.areaHFIResults.maxMeanIntensityGroup}
      ></MeanIntensityGroupRollup>
      <MeanPrepLevelCell
        areaName={props.areaName}
        meanPrepLevel={props.areaHFIResults.meanPrepLevel}
      />
    </React.Fragment>
  )
}

export default React.memo(CalculatedPlanningAreaCells)
