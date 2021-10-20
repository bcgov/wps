import { FireCentre } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import DailyViewTable from 'features/hfiCalculator/components/DailyViewTable'
import WeeklyViewTable from 'features/hfiCalculator/components/WeeklyViewTable'
import React from 'react'

export interface ViewSwitcherProps {
  testId?: string
  isWeeklyView: boolean
  fireCentres: Record<string, FireCentre>
  dailies: StationDaily[]
  dateOfInterest: string
}

const ViewSwitcher = (props: ViewSwitcherProps) => {
  return (
    <React.Fragment>
      {props.isWeeklyView ? (
        <WeeklyViewTable
          testId="hfi-calc-weekly-table"
          fireCentres={props.fireCentres}
          dailies={props.dailies}
          currentDay={props.dateOfInterest}
        />
      ) : (
        <DailyViewTable
          testId="hfi-calc-daily-table"
          fireCentres={props.fireCentres}
          dailies={props.dailies}
        ></DailyViewTable>
      )}
    </React.Fragment>
  )
}

export default React.memo(ViewSwitcher)
