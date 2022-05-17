import { FireCentre, FuelType } from 'api/hfiCalculatorAPI'
import { DailyViewTable } from 'features/hfiCalculator/components/DailyViewTable'
import WeeklyViewTable from 'features/hfiCalculator/components/WeeklyViewTable'
import { FireStartRange, PrepDateRange, StationInfo } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import React from 'react'

export interface ViewSwitcherProps {
  testId?: string
  dateRange?: PrepDateRange
  setSelected: (planningAreaId: number, code: number, selected: boolean) => void
  setNewFireStarts: (areaId: number, dayOffset: number, newFireStarts: FireStartRange) => void
  setFuelType: (planningAreaId: number, code: number, fuelTypeId: number) => void
  selectedPrepDay: string
  selectedFireCentre: FireCentre | undefined
  fuelTypes: FuelType[]
  planningAreaStationInfo: { [key: number]: StationInfo[] }
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
          setFuelType={props.setFuelType}
          fuelTypes={props.fuelTypes}
        />
      ) : (
        <DailyViewTable
          testId="hfi-calc-daily-table"
          fireCentre={props.selectedFireCentre}
          setSelected={props.setSelected}
          setFuelType={props.setFuelType}
          fuelTypes={props.fuelTypes}
          planningAreaStationInfo={props.planningAreaStationInfo}
        ></DailyViewTable>
      )}
    </React.Fragment>
  )
}

export default React.memo(ViewSwitcher)
