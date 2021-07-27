import React, { useState } from 'react'
import { isNull, isUndefined, zipWith } from 'lodash'
import {
  Checkbox,
  makeStyles,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip
} from '@material-ui/core'
import InfoIcon from '@material-ui/icons/Info'
import { FuelTypes } from 'features/fireBehaviourCalculator/fuelTypes'
import { FBCStation } from 'api/fbCalcAPI'
import WeatherStationCell from 'features/fireBehaviourCalculator/components/WeatherStationCell'
import FuelTypeCell from 'features/fireBehaviourCalculator/components/FuelTypeCell'
import GrassCureCell from 'features/fireBehaviourCalculator/components/GrassCureCell'
import WindSpeedCell from 'features/fireBehaviourCalculator/components/WindSpeedCell'
import SelectionCheckbox from 'features/fireBehaviourCalculator/components/SelectionCheckbox'

export interface FBCInputGridProps {
  testId?: string
  stationOptions: GridMenuOption[]
  fuelTypeOptions: GridMenuOption[]
  inputRows: FBCInputRow[]
  updateRow: (rowId: number, updatedRow: FBCInputRow) => void
  selected: number[]
  updateSelected: (selected: number[]) => void
  calculatedResults: FBCStation[]
}

export interface GridMenuOption {
  label: string
  value: string | number
}

export interface FBCInputRow {
  id: number
  weatherStation: string | undefined
  fuelType: string | undefined
  grassCure: number | undefined
  windSpeed: number | undefined
}

const useStyles = makeStyles({
  display: {
    paddingBottom: 12,

    '& .MuiTableCell-sizeSmall': {
      padding: '6px 12px 6px 6px'
    }
  },
  weatherStation: {
    minWidth: 220
  },
  fuelType: {
    minWidth: 220
  },
  grassCure: {
    width: 80
  },
  windSpeed: {
    width: 80
  },
  paper: {
    width: '100%'
  },
  tableContainer: {
    maxHeight: 1080,
    maxWidth: 1900
  },
  adjustedValueCell: {
    fontWeight: 'bold'
  },
  criticalHoursCell: {
    backgroundColor: '#e6ebf0'
  }
})

const FBCInputGrid = (props: FBCInputGridProps) => {
  const { updateSelected, inputRows, calculatedResults } = props
  const classes = useStyles()

  const stationCodeMap = new Map(
    props.stationOptions.map(station => [station.value, station.label])
  )

  const [headerSelected, setHeaderSelect] = useState<boolean>(false)
  const buildStationOption = (value: string | undefined) => {
    if (isUndefined(value)) {
      return null
    }
    const label = stationCodeMap.get(parseInt(value))

    if (isUndefined(label)) {
      return null
    }
    const option: GridMenuOption = {
      label,
      value
    }
    return option
  }

  const buildFuelTypeMenuOption = (value: string | undefined) => {
    if (isUndefined(value)) {
      return null
    }
    const fuelType = FuelTypes.lookup(value)
    if (isUndefined(fuelType) || isNull(fuelType)) {
      return null
    }
    const option: GridMenuOption = {
      label: fuelType.friendlyName,
      value
    }
    return option
  }

  interface DisplayableInputRow {
    weatherStation: GridMenuOption | null
    fuelType: GridMenuOption | null
    grassCure: number | undefined
    windSpeed: number | undefined
  }

  const inputFieldData: DisplayableInputRow[] = inputRows.map(row => ({
    weatherStation: buildStationOption(row.weatherStation),
    fuelType: buildFuelTypeMenuOption(row.fuelType),
    grassCure: row.grassCure,
    windSpeed: row.windSpeed
  }))

  type FBCTableRow = DisplayableInputRow & Partial<FBCStation>

  const rows: FBCTableRow[] = zipWith(
    inputFieldData,
    calculatedResults,
    (inputRow, outputRow) => {
      if (inputRow) {
        return [
          {
            ...inputRow,
            ...outputRow
          }
        ]
      }
      return []
    }
  ).flat()
  const DECIMAL_PLACES = 1

  return (
    <div className={classes.display} data-testid={props.testId}>
      <Paper className={classes.paper} elevation={1}>
        <TableContainer className={classes.tableContainer}>
          <Table stickyHeader aria-label="daily table view of HFI by planning area">
            <TableHead>
              <TableRow>
                <TableCell>
                  <Checkbox
                    color="primary"
                    checked={headerSelected}
                    onClick={() => {
                      if (headerSelected) {
                        // Toggle off
                        updateSelected([])
                        setHeaderSelect(false)
                      } else {
                        updateSelected(inputRows.map((_, i) => i))
                        setHeaderSelect(true)
                      }
                    }}
                  />
                </TableCell>
                <TableCell key="header-location">Weather Station</TableCell>
                <TableCell key="header-elevation">
                  Elev.
                  <br />
                  (m)
                </TableCell>
                <TableCell key="header-fuel-type">
                  FBP
                  <br />
                  Fuel
                  <br />
                  Type
                </TableCell>
                <TableCell>
                  Grass
                  <br />
                  Cure
                  <br />
                  (%)
                </TableCell>
                <TableCell>Status</TableCell>
                <TableCell>
                  Temp
                  <br />
                  (&deg;C)
                </TableCell>
                <TableCell>
                  RH
                  <br />
                  (%)
                </TableCell>
                <TableCell>
                  Wind
                  <br />
                  Dir
                  <br />
                  (&deg;)
                </TableCell>
                <TableCell className={classes.windSpeed}>
                  {'Wind Speed (km/h) (Optional)'}
                  <Tooltip title="Leave this empty to calculate forecasted/observed wind speed. Add a custom wind speed to influence the calculations">
                    <InfoIcon aria-label="info"></InfoIcon>
                  </Tooltip>
                </TableCell>
                <TableCell>
                  Precip
                  <br />
                  (mm)
                </TableCell>
                <TableCell>FFMC</TableCell>
                <TableCell>DMC</TableCell>
                <TableCell>DC</TableCell>
                <TableCell>ISI</TableCell>
                <TableCell>BUI</TableCell>
                <TableCell>FWI</TableCell>
                <TableCell>HFI</TableCell>
                <TableCell className={classes.criticalHoursCell}>
                  Critical
                  <br />
                  Hours
                  <br />
                  (4000 kW/m) &dagger;
                </TableCell>
                <TableCell className={classes.criticalHoursCell}>
                  Critical
                  <br />
                  Hours
                  <br />
                  (10000 kW/m) &dagger;
                </TableCell>
                <TableCell>
                  ROS
                  <br />
                  (m/min)
                </TableCell>
                <TableCell>Fire Type</TableCell>
                <TableCell>CFB (%)</TableCell>
                <TableCell>
                  Flame <br />
                  Length <br /> (m)
                </TableCell>
                <TableCell>
                  30 min <br />
                  fire size <br />
                  (hectares)
                </TableCell>
                <TableCell>
                  60 min <br />
                  fire size <br />
                  (hectares)
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.map((row, ri) => {
                return (
                  <TableRow key={ri}>
                    <TableCell>
                      <SelectionCheckbox fbcInputGridProps={props} rowId={ri} />
                    </TableCell>
                    <TableCell>
                      <WeatherStationCell
                        fbcInputGridProps={props}
                        classNameMap={classes}
                        value={row.weatherStation}
                        rowId={ri}
                      />
                    </TableCell>
                    <TableCell>{row.elevation}</TableCell>
                    <TableCell>
                      <FuelTypeCell
                        fbcInputGridProps={props}
                        classNameMap={classes}
                        value={row.fuelType}
                        rowId={ri}
                      />
                    </TableCell>
                    <TableCell>
                      <GrassCureCell
                        fbcInputGridProps={props}
                        classNameMap={classes}
                        value={row.grassCure}
                        rowId={ri}
                      />
                    </TableCell>
                    <TableCell
                      className={
                        !isUndefined(row.status) &&
                        row.status.toLowerCase() === 'adjusted'
                          ? classes.adjustedValueCell
                          : undefined
                      }
                    >
                      {row.status}
                    </TableCell>
                    <TableCell>{row.temp}</TableCell>
                    <TableCell>{row.rh}</TableCell>
                    <TableCell>{row.wind_direction}</TableCell>
                    <TableCell
                      className={
                        !isUndefined(row.status) &&
                        row.status.toLowerCase() === 'adjusted'
                          ? classes.adjustedValueCell
                          : undefined
                      }
                    >
                      <WindSpeedCell
                        fbcInputGridProps={props}
                        classNameMap={classes}
                        value={row.windSpeed}
                        rowId={ri}
                      />
                    </TableCell>
                    <TableCell>{row.precipitation}</TableCell>
                    <TableCell>
                      {row.fine_fuel_moisture_code?.toFixed(DECIMAL_PLACES)}
                    </TableCell>
                    <TableCell>
                      {row.duff_moisture_code?.toFixed(DECIMAL_PLACES)}
                    </TableCell>
                    <TableCell>{row.drought_code?.toFixed(DECIMAL_PLACES)}</TableCell>
                    <TableCell>
                      {row.initial_spread_index?.toFixed(DECIMAL_PLACES)}
                    </TableCell>
                    <TableCell>{row.build_up_index?.toFixed(DECIMAL_PLACES)}</TableCell>
                    <TableCell>
                      {row.fire_weather_index?.toFixed(DECIMAL_PLACES)}
                    </TableCell>
                    <TableCell>
                      {row.head_fire_intensity?.toFixed(DECIMAL_PLACES)}
                    </TableCell>
                    <TableCell className={classes.criticalHoursCell}>
                      {row.critical_hours_hfi_4000}
                    </TableCell>
                    <TableCell className={classes.criticalHoursCell}>
                      {row.critical_hours_hfi_10000}
                    </TableCell>
                    <TableCell>{row.rate_of_spread?.toFixed(DECIMAL_PLACES)}</TableCell>
                    <TableCell>{row?.fire_type}</TableCell>
                    <TableCell>
                      {/* CFB comes in as a number 0 to 1, so we multiple by 100 to get the percentage */}
                      {!isUndefined(row.percentage_crown_fraction_burned) &&
                        (row.percentage_crown_fraction_burned * 100).toFixed(
                          DECIMAL_PLACES
                        )}
                    </TableCell>
                    <TableCell>{row.flame_length?.toFixed(DECIMAL_PLACES)}</TableCell>
                    <TableCell>
                      {row.thirty_minute_fire_size?.toFixed(DECIMAL_PLACES)}
                    </TableCell>
                    <TableCell>
                      {row.sixty_minute_fire_size?.toFixed(DECIMAL_PLACES)}
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </div>
  )
}

export default React.memo(FBCInputGrid)
