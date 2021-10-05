import { FireCentre } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import DailyViewTable from 'features/hfiCalculator/components/DailyViewTable'
import WeeklyViewTable from 'features/hfiCalculator/components/WeeklyViewTable'
import React from 'react'

export interface ViewSwitcherProps {
  testId?: string
  isWeeklyView: boolean
  fireCentres: Record<string, FireCentre>
  dailiesMap: Map<number, StationDaily>
  weekliesMap: Map<number, StationDaily[]>
  weekliesByUTC: Map<number, StationDaily[]>
  dateOfInterest: string
}

const ViewSwitcher = (props: ViewSwitcherProps) => {
  return (
    <React.Fragment>
      {props.isWeeklyView ? (
        <WeeklyViewTable
          title="HFI Calculator Weekly View"
          testId="hfi-calc-weekly-table"
          fireCentres={props.fireCentres}
          dailiesMap={props.dailiesMap}
          weekliesByStationCode={props.weekliesMap}
          weekliesByUTC={props.weekliesByUTC}
          currentDay={props.dateOfInterest}
        />
      ) : (
        <DailyViewTable
          title="HFI Calculator Daily View"
          testId="hfi-calc-daily-table"
          fireCentres={props.fireCentres}
          dailiesMap={props.dailiesMap}
        ></DailyViewTable>
      )}
    </React.Fragment>
  )
}

export default React.memo(ViewSwitcher)
