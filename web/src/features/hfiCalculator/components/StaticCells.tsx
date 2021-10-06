import { WeatherStation } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import CalculatedCell from 'features/hfiCalculator/components/CalculatedCell'
import IntensityGroupCell from 'features/hfiCalculator/components/IntensityGroupCell'
import WeeklyROSCell from 'features/hfiCalculator/components/WeeklyROSCell'
import { DECIMAL_PLACES } from 'features/hfiCalculator/constants'
import React, { ReactElement } from 'react'

export interface StaticCellsProps {
  dailies: StationDaily[] | undefined
  station: WeatherStation
  classNameForRow: string | undefined
  isRowSelected: boolean
}

export const StaticCells = ({
  dailies,
  station,
  classNameForRow,
  isRowSelected
}: StaticCellsProps): ReactElement => {
  const staticCells = dailies?.map(daily => (
    <React.Fragment key={`${station.code}-${daily.date}`}>
      <WeeklyROSCell daily={daily} station={station} isRowSelected={isRowSelected} />
      <CalculatedCell
        testid={`${daily.code}-hfi`}
        value={daily.hfi?.toFixed(DECIMAL_PLACES)}
        error={false}
        className={classNameForRow}
      />
      <IntensityGroupCell
        testid={`${daily.code}-intensity-group`}
        value={daily.intensity_group}
        error={false}
        selected={isRowSelected}
      ></IntensityGroupCell>
      {/* Fire Starts */}
      <CalculatedCell
        testid={`${daily.code}-fire-starts`}
        error={false}
        className={classNameForRow}
        value={undefined}
      />
      {/* Prep Level */}
      <CalculatedCell
        testid={`${daily.code}-prep-level`}
        error={false}
        className={classNameForRow}
        value={undefined}
      />
    </React.Fragment>
  ))
  return <React.Fragment>{staticCells}</React.Fragment>
}

export default React.memo(StaticCells)
