import { FireCentre } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import DailyViewTable from 'features/hfiCalculator/components/DailyViewTable'
import WeeklyViewTable from 'features/hfiCalculator/components/WeeklyViewTable'
import React from 'react'

export interface ViewSwitcherProps {
  testId?: string
  fireCentres: Record<string, FireCentre>
  dailies: StationDaily[]
  dateOfInterest: string
  setSelected: (selected: number[]) => void
  selectedPrepDay: string | null
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
          setSelected={props.setSelected}
        />
      ) : (
        <DailyViewTable
          testId="hfi-calc-daily-table"
          fireCentres={props.fireCentres}
          dailies={props.dailies}
          setSelected={props.setSelected}
        ></DailyViewTable>
      )}
    </React.Fragment>
  )
}

export default React.memo(ViewSwitcher)
