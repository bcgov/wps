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
  TableSortLabel,
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
import { Order } from 'utils/table'

export interface FBCInputGridProps {
  testId?: string
  stationOptions: GridMenuOption[]
  fuelTypeOptions: GridMenuOption[]
  inputRows: FBCInputRow[]
  updateRow: (rowId: number, updatedRow: FBCInputRow, dispatchRequest?: boolean) => void
  selected: number[]
  updateSelected: (selected: number[]) => void
  calculatedResults: FBCStation[]
  autoUpdateHandler: () => void
}

export interface GridMenuOption {
  label: string
  value: string
}

export interface FBCInputRow {
  id: number
  weatherStation: string | undefined
  fuelType: string | undefined
  grassCure: number | undefined
  windSpeed: number | undefined
}

enum SortByColumn {
  Zone,
  Station,
  FuelType,
  ISI,
  HFI,
  WindSpeed
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
  }
})

const FBCInputGrid = (props: FBCInputGridProps) => {
  const { updateSelected, inputRows, calculatedResults } = props
  const classes = useStyles()

  const stationCodeMap = new Map(
    props.stationOptions.map(station => [station.value, station.label])
  )

  const [headerSelected, setHeaderSelect] = useState<boolean>(false)
  const [order, setOrder] = useState<Order>('desc')
  const [sortByColumn, setSortByColumn] = useState<SortByColumn>(SortByColumn.Station)

  const toggleSortZone = () => {
    toggleSorting(SortByColumn.Zone)
  }
  const toggleSortStation = () => {
    toggleSorting(SortByColumn.Station)
  }
  const toggleSortFuelType = () => {
    toggleSorting(SortByColumn.FuelType)
  }
  const toggleSortWindSpeed = () => {
    toggleSorting(SortByColumn.WindSpeed)
  }
  const toggleSortISI = () => {
    toggleSorting(SortByColumn.ISI)
  }
  const toggleSortHFI = () => {
    toggleSorting(SortByColumn.HFI)
  }

  const toggleSorting = (selectedColumn: SortByColumn) => {
    if (sortByColumn !== selectedColumn) {
      setSortByColumn(selectedColumn)
    } else {
      setOrder(order === 'asc' ? 'desc' : 'asc')
    }
  }

  const buildStationOption = (value: string | undefined) => {
    if (isUndefined(value)) {
      return null
    }
    const label = stationCodeMap.get(value)

    if (isUndefined(label)) {
      return null
    }
    return {
      label,
      value
    }
  }

  const buildFuelTypeMenuOption = (value: string | undefined) => {
    if (isUndefined(value)) {
      return null
    }
    const fuelType = FuelTypes.lookup(value)
    if (isUndefined(fuelType) || isNull(fuelType)) {
      return null
    }
    return {
      label: fuelType.friendlyName,
      value
    }
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

  const stringComparator = (a: string | undefined, b: string | undefined): number => {
    if (a === undefined || b === undefined) {
      return 0
    }
    const diff = a.localeCompare(b)
    return order === 'asc' ? diff : -diff
  }
  const numericComparator = (a: number | undefined, b: number | undefined): number => {
    if (a === undefined || b === undefined) {
      return 0
    }
    const diff = a - b
    return order === 'asc' ? diff : -diff
  }

  const sortRows = (tableRows: FBCTableRow[]) => {
    switch (sortByColumn) {
      case SortByColumn.Zone: {
        return tableRows.sort((a, b) => stringComparator(a.zone_code, b.zone_code))
      }
      case SortByColumn.Station: {
        return tableRows.sort((a, b) => stringComparator(a.station_name, b.station_name))
      }
      case SortByColumn.FuelType: {
        return tableRows.sort((a, b) => stringComparator(a.fuel_type, b.fuel_type))
      }
      case SortByColumn.HFI: {
        return tableRows.sort((a, b) =>
          numericComparator(a.head_fire_intensity, b.head_fire_intensity)
        )
      }
      case SortByColumn.ISI: {
        return tableRows.sort((a, b) =>
          numericComparator(a.initial_spread_index, b.initial_spread_index)
        )
      }
      case SortByColumn.WindSpeed: {
        return tableRows.sort((a, b) => numericComparator(a.wind_speed, b.wind_speed))
      }
      default: {
        return tableRows
      }
    }
  }

  const sortedRows = sortRows(rows)

  return (
    <div className={classes.display} data-testid={props.testId}>
      <Paper className={classes.paper} elevation={1}>
        <TableContainer className={classes.tableContainer}>
          <Table stickyHeader aria-label="Fire Behaviour Analysis table">
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
                <TableCell key="header-zone" sortDirection={order}>
                  <TableSortLabel direction={order} onClick={toggleSortZone}>
                    Zone
                  </TableSortLabel>
                </TableCell>
                <TableCell key="header-location" sortDirection={order}>
                  <TableSortLabel direction={order} onClick={toggleSortStation}>
                    Weather Station
                  </TableSortLabel>
                </TableCell>
                <TableCell key="header-elevation">
                  Elev.
                  <br />
                  (m)
                </TableCell>
                <TableCell sortDirection={order} key="header-fuel-type">
                  <TableSortLabel direction={order} onClick={toggleSortFuelType}>
                    FBP
                    <br />
                    Fuel
                    <br />
                    Type
                  </TableSortLabel>
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
                <TableCell sortDirection={order} className={classes.windSpeed}>
                  <TableSortLabel direction={order} onClick={toggleSortWindSpeed}>
                    {'Wind Speed (km/h)'}
                    <Tooltip title="Leave this empty to calculate forecasted/observed wind speed. Add a custom wind speed to influence the calculations">
                      <InfoIcon aria-label="info"></InfoIcon>
                    </Tooltip>
                  </TableSortLabel>
                </TableCell>
                <TableCell>
                  Precip
                  <br />
                  (mm)
                </TableCell>
                <TableCell>FFMC</TableCell>
                <TableCell>DMC</TableCell>
                <TableCell>DC</TableCell>
                <TableCell sortDirection={order}>
                  <TableSortLabel direction={order} onClick={toggleSortISI}>
                    ISI
                  </TableSortLabel>
                </TableCell>
                <TableCell>BUI</TableCell>
                <TableCell>FWI</TableCell>
                <TableCell sortDirection={order}>
                  <TableSortLabel direction={order} onClick={toggleSortHFI}>
                    HFI
                  </TableSortLabel>
                </TableCell>
                <TableCell>
                  Critical
                  <br />
                  Hours
                  <br />
                  (4000 kW/m)
                </TableCell>
                <TableCell>
                  Critical
                  <br />
                  Hours
                  <br />
                  (10000 kW/m)
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
              {sortedRows.map((row, ri) => {
                console.log(ri)
                console.log(row)
                return (
                  <TableRow key={ri}>
                    <TableCell>
                      <SelectionCheckbox fbcInputGridProps={props} rowId={ri} />
                    </TableCell>
                    <TableCell>{row.zone_code}</TableCell>
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
                        inputValue={row.windSpeed}
                        calculatedValue={
                          calculatedResults.length > 0 && ri < calculatedResults.length
                            ? calculatedResults[ri].wind_speed
                            : undefined
                        }
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
                    <TableCell>{row.critical_hours_hfi_4000}</TableCell>
                    <TableCell>{row.critical_hours_hfi_10000}</TableCell>
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
