import { TableCell } from '@mui/material'
import { FuelType, StationDaily, WeatherStation } from 'api/hfiCalculatorAPI'
import HFICell from 'components/HFICell'
import EmptyStaticCells from 'features/hfiCalculator/components/EmptyStaticCells'
import HighestDailyFIGCell from 'features/hfiCalculator/components/HighestDailyFIGCell'
import IntensityGroupCell from 'features/hfiCalculator/components/IntensityGroupCell'
import WeeklyROSCell from 'features/hfiCalculator/components/WeeklyROSCell'
import { isValidGrassCure } from 'features/hfiCalculator/validation'
import { isNull, isUndefined, range } from 'lodash'
import React, { ReactElement } from 'react'

export interface StaticCellsProps {
  numPrepDays: number
  dailies: StationDaily[] | undefined
  station: WeatherStation
  classNameForRow: string | undefined
  isRowSelected: boolean
  selectedFuelType: FuelType | undefined
}

export const isError = (daily: StationDaily | undefined, selectedFuelType: FuelType | undefined): boolean => {
  if (!isValidGrassCure(daily, selectedFuelType)) {
    return false
  }
  if (
    isNull(daily?.bui) ||
    isNull(daily?.dc) ||
    isNull(daily?.dmc) ||
    isNull(daily?.ffmc) ||
    isNull(daily?.isi) ||
    isNull(daily?.fwi)
  ) {
    return true
  }
  return false
}

export const StaticCells = ({
  numPrepDays,
  dailies,
  station,
  classNameForRow,
  isRowSelected,
  selectedFuelType
}: StaticCellsProps): ReactElement => {
  const staticCells = range(numPrepDays).map(dailyIndex => {
    const daily = dailies ? dailies[dailyIndex] : undefined
    const error = isError(daily, selectedFuelType)
    return isUndefined(daily) ? (
      <EmptyStaticCells
        key={`empty-${station.code}-${dailyIndex}`}
        rowId={dailyIndex}
        isRowSelected={isRowSelected}
        classNameForRow={classNameForRow}
      />
    ) : (
      <React.Fragment key={`${station.code}-${daily.date}-${dailyIndex}`}>
        <WeeklyROSCell
          daily={daily}
          testId={`${station.code}-ros`}
          error={error}
          isRowSelected={isRowSelected}
          isFirstDayOfPrepPeriod={dailyIndex === 0}
        />
        <HFICell value={daily?.hfi} />
        <IntensityGroupCell
          testid={`${daily.code}-intensity-group`}
          value={daily.intensity_group}
          error={error}
          selected={isRowSelected}
        ></IntensityGroupCell>
        {/* Fire Starts */}
        <TableCell data-testid={`${daily.code}-fire-starts`} className={classNameForRow}></TableCell>
        {/* Prep Level */}
        <TableCell data-testid={`${daily.code}-prep-level`} className={classNameForRow}></TableCell>
      </React.Fragment>
    )
  })
  return (
    <React.Fragment>
      {staticCells}
      <HighestDailyFIGCell isRowSelected={isRowSelected} />
      {/* Calc. Prep */}
      <TableCell data-testid={`calc-prep`} className={classNameForRow}></TableCell>
    </React.Fragment>
  )
}

export default React.memo(StaticCells)
