import { FireCentre } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import DailyViewTable from 'features/hfiCalculator/components/DailyViewTable'
import WeeklyViewTable from 'features/hfiCalculator/components/WeeklyViewTable'
import { DateTime } from 'luxon'
import React from 'react'

export interface ViewSwitcherProps {
  testId?: string
  fireCentres: Record<string, FireCentre>
  dailies: StationDaily[]
  dateOfInterest: string
  selectedPrepDay: DateTime | null
}

const ViewSwitcher = (props: ViewSwitcherProps) => {
  return (
    <React.Fragment>
      {props.selectedPrepDay == null ? (
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
          selectedPrepDay={props.selectedPrepDay}
        ></DailyViewTable>
      )}
    </React.Fragment>
  )
}

export default React.memo(ViewSwitcher)
