import { FireCentre } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import { DailyViewTable } from 'features/hfiCalculator/components/DailyViewTable'
import WeeklyViewTable from 'features/hfiCalculator/components/WeeklyViewTable'
import React from 'react'

export interface ViewSwitcherProps {
  testId?: string
  dailies: StationDaily[]
  dateOfInterest: string
  setSelected: (selected: number[]) => void
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
          dailies={props.dailies}
          currentDay={props.dateOfInterest}
          setSelected={props.setSelected}
        />
      ) : (
        <DailyViewTable
          testId="hfi-calc-daily-table"
          fireCentre={props.selectedFireCentre}
          dailies={props.dailies}
          setSelected={props.setSelected}
        ></DailyViewTable>
      )}
    </React.Fragment>
  )
}

export default React.memo(ViewSwitcher)
