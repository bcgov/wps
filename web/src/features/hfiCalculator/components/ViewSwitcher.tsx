import { FireCentre } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import DailyViewTable from 'features/hfiCalculator/components/DailyViewTable'
import WeeklyViewTable from 'features/hfiCalculator/components/WeeklyViewTable'
import React from 'react'

export interface ViewSwitcherProps {
  testId?: string
  isWeeklyView: boolean
  dailies: StationDaily[]
  dateOfInterest: string
  selectedFireCentre: FireCentre | undefined
}

const ViewSwitcher = (props: ViewSwitcherProps) => {
  return (
    <React.Fragment>
      {props.isWeeklyView ? (
        <WeeklyViewTable
          testId="hfi-calc-weekly-table"
          fireCentre={props.selectedFireCentre}
          dailies={props.dailies}
          currentDay={props.dateOfInterest}
        />
      ) : (
        <DailyViewTable
          testId="hfi-calc-daily-table"
          fireCentre={props.selectedFireCentre}
          dailies={props.dailies}
        ></DailyViewTable>
      )}
    </React.Fragment>
  )
}

export default React.memo(ViewSwitcher)
