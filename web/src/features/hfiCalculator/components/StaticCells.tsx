import { TableCell } from '@material-ui/core'
import { WeatherStation } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import IntensityGroupCell from 'features/hfiCalculator/components/IntensityGroupCell'
import WeeklyROSCell from 'features/hfiCalculator/components/WeeklyROSCell'
import { DECIMAL_PLACES } from 'features/hfiCalculator/constants'
import { isValidGrassCure } from 'features/hfiCalculator/validation'
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
  const staticCells = dailies?.map(daily => {
    const error = !isValidGrassCure(daily, station.station_props)
    return (
      <React.Fragment key={`${station.code}-${daily.date}`}>
        <WeeklyROSCell
          daily={daily}
          station={station}
          error={error}
          isRowSelected={isRowSelected}
        />
        <TableCell data-testid={`${daily.code}-hfi`} className={classNameForRow}>
          {error ? undefined : daily.hfi?.toFixed(DECIMAL_PLACES)}
        </TableCell>
        <IntensityGroupCell
          testid={`${daily.code}-intensity-group`}
          value={daily.intensity_group}
          error={error}
          selected={isRowSelected}
        ></IntensityGroupCell>
        {/* Fire Starts */}
        <TableCell
          data-testid={`${daily.code}-fire-starts`}
          className={classNameForRow}
        ></TableCell>
        {/* Prep Level */}
        <TableCell
          data-testid={`${daily.code}-prep-level`}
          className={classNameForRow}
        ></TableCell>
      </React.Fragment>
    )
  })
  return <React.Fragment>{staticCells}</React.Fragment>
}

export default React.memo(StaticCells)
