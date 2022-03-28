import { FireCentre } from 'api/hfiCalcAPI'
import { DailyViewTable } from 'features/hfiCalculator/components/DailyViewTable'
import WeeklyViewTable from 'features/hfiCalculator/components/WeeklyViewTable'
import {
  FireStarts,
  HFIResultResponse,
  PrepDateRange
} from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import React from 'react'

export interface ViewSwitcherProps {
  testId?: string
  result: HFIResultResponse
  dateRange?: PrepDateRange
  setSelected: (selected: number[]) => void
  setNewFireStarts: (areaId: number, dayOffset: number, newFireStarts: FireStarts) => void
  selectedPrepDay: string
  selectedFireCentre: FireCentre | undefined
}

const ViewSwitcher = (props: ViewSwitcherProps) => {
  return (
    <React.Fragment>
      {props.selectedPrepDay == '' ? (
        <WeeklyViewTable
          testId="hfi-calc-weekly-table"
          fireCentre={props.selectedFireCentre}
          dateRange={props.dateRange}
          setSelected={props.setSelected}
          setNewFireStarts={props.setNewFireStarts}
        />
      ) : (
        <DailyViewTable
          testId="hfi-calc-daily-table"
          fireCentre={props.selectedFireCentre}
          setSelected={props.setSelected}
        ></DailyViewTable>
      )}
    </React.Fragment>
  )
}

export default React.memo(ViewSwitcher)
