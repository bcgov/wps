import { WeatherStation } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import { isGrassFuelType } from 'features/fbaCalculator/utils'
import CalculatedCell from 'features/hfiCalculator/components/CalculatedCell'
import IntensityGroupCell from 'features/hfiCalculator/components/IntensityGroupCell'
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
      <CalculatedCell
        testid={`${daily.code}-grass-cure`}
        value={daily?.grass_cure_percentage?.toFixed(DECIMAL_PLACES)}
        error={isGrassFuelType(station.station_props.fuel_type.abbrev)}
        className={classNameForRow}
      />

      <CalculatedCell
        testid={`${daily.code}-ros`}
        value={daily.rate_of_spread?.toFixed(DECIMAL_PLACES)}
        error={false}
        className={classNameForRow}
      />
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
