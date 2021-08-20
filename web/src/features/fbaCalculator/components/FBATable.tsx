import React, { useState } from 'react'
import { isUndefined } from 'lodash'
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
import { CriticalHoursHFI, FBCStation } from 'api/fbCalcAPI'
import WeatherStationCell from 'features/fbaCalculator/components/WeatherStationCell'
import FuelTypeCell from 'features/fbaCalculator/components/FuelTypeCell'
import GrassCureCell from 'features/fbaCalculator/components/GrassCureCell'
import WindSpeedCell from 'features/fbaCalculator/components/WindSpeedCell'
import SelectionCheckbox from 'features/fbaCalculator/components/SelectionCheckbox'
import { Order } from 'utils/table'
import { RowManager, SortByColumn } from 'features/fbaCalculator/RowManager'

export interface FBAInputGridProps {
  testId?: string
  stationOptions: GridMenuOption[]
  fuelTypeOptions: GridMenuOption[]
  inputRows: FBAInputRow[]
  updateRow: (rowId: number, updatedRow: FBAInputRow, dispatchRequest?: boolean) => void
  selected: number[]
  updateSelected: (selected: number[]) => void
  calculatedResults: FBCStation[]
  autoUpdateHandler: () => void
}

export interface GridMenuOption {
  label: string
  value: string
}

export interface FBAInputRow {
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
    },

    '& .MuiTableCell-stickyHeader': {
      padding: '8px'
    },

    '& .MuiInputBase-root': {
      fontSize: '1em'
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
    maxHeight: 600,
    maxWidth: 1900
  },
  adjustedValueCell: {
    fontWeight: 'bold',
    color: '#460270'
  },
  dataRow: {
    height: '40px',
    paddingLeft: '8px',
    paddingRight: '8px',
    fontSize: '12px'
  },
  tableHeaderRow: {
    padding: '8px'
  }
})

const FBAInputGrid = (props: FBAInputGridProps) => {
  const { updateSelected, inputRows, calculatedResults } = props
  const classes = useStyles()

  const [headerSelected, setHeaderSelect] = useState<boolean>(false)
  const [order, setOrder] = useState<Order>('desc')
  const [sortByColumn, setSortByColumn] = useState<SortByColumn>(SortByColumn.Station)

  const toggleSorting = (selectedColumn: SortByColumn) => {
    if (sortByColumn !== selectedColumn) {
      setSortByColumn(selectedColumn)
    } else {
      setOrder(order === 'asc' ? 'desc' : 'asc')
    }
  }
  const DECIMAL_PLACES = 1

  const stationCodeMap = new Map(
    props.stationOptions.map(station => [station.value, station.label])
  )
  const rowManager = new RowManager(stationCodeMap)

  const sortedRows = RowManager.sortRows(
    sortByColumn,
    order,
    rowManager.mergeFBARows(inputRows, calculatedResults)
  )

  const formatCriticalHoursAsString = (
    criticalHours: CriticalHoursHFI | undefined | null
  ): string | undefined => {
    if (criticalHours === undefined || criticalHours === null) {
      return undefined
    }
    return `${criticalHours.start}:00 - ${criticalHours.end}:00`
  }

  return (
    <div className={classes.display} data-testid={props.testId}>
      <Paper className={classes.paper} elevation={1}>
        <TableContainer className={classes.tableContainer}>
          <Table size="small" stickyHeader aria-label="Fire Behaviour Analysis table">
            <TableHead>
              <TableRow>
                <TableCell>
                  <Checkbox
                    data-testid="select-all"
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
                  <TableSortLabel className={classes.tableHeaderRow}
                    direction={order}
                    onClick={() => {
                      toggleSorting(SortByColumn.Zone)
                    }}
                  >
                    Zone
                  </TableSortLabel>
                </TableCell>
                <TableCell key="header-location" sortDirection={order}>
                  <TableSortLabel
                    direction={order}
                    onClick={() => {
                      toggleSorting(SortByColumn.Station)
                    }}
                  >
                    Weather Station
                  </TableSortLabel>
                </TableCell>
                <TableCell key="header-elevation" sortDirection={order}>
                  <TableSortLabel
                    direction={order}
                    onClick={() => {
                      toggleSorting(SortByColumn.Elevation)
                    }}
                  >
                    Elev.
                    <br />
                    (m)
                  </TableSortLabel>
                </TableCell>
                <TableCell key="header-fuel-type" sortDirection={order}>
                  <TableSortLabel
                    direction={order}
                    onClick={() => toggleSorting(SortByColumn.FuelType)}
                  >
                    FBP
                    Fuel
                    Type
                  </TableSortLabel>
                </TableCell>
                <TableCell sortDirection={order}>
                  <TableSortLabel
                    direction={order}
                    onClick={() => toggleSorting(SortByColumn.GrassCure)}
                  >
                    Grass
                    <br />
                    Cure
                    <br />
                    (%)
                  </TableSortLabel>
                </TableCell>
                <TableCell sortDirection={order}>
                  <TableSortLabel
                    direction={order}
                    onClick={() => {
                      toggleSorting(SortByColumn.Status)
                    }}
                  >
                    Status
                  </TableSortLabel>
                </TableCell>
                <TableCell sortDirection={order}>
                  <TableSortLabel
                    direction={order}
                    onClick={() => {
                      toggleSorting(SortByColumn.Temperature)
                    }}
                  >
                    Temp
                    <br />
                    (&deg;C)
                  </TableSortLabel>
                </TableCell>
                <TableCell sortDirection={order}>
                  <TableSortLabel
                    direction={order}
                    onClick={() => {
                      toggleSorting(SortByColumn.RelativeHumidity)
                    }}
                  >
                    RH
                    <br />
                    (%)
                  </TableSortLabel>
                </TableCell>
                <TableCell sortDirection={order}>
                  <TableSortLabel
                    direction={order}
                    onClick={() => {
                      toggleSorting(SortByColumn.WindDirection)
                    }}
                  >
                    Wind
                    <br />
                    Dir
                    <br />
                    (&deg;)
                  </TableSortLabel>
                </TableCell>
                <TableCell className={classes.windSpeed} sortDirection={order}>
                  <TableSortLabel
                    direction={order}
                    onClick={() => {
                      toggleSorting(SortByColumn.WindSpeed)
                    }}
                  >
                    {'Wind Speed (km/h)'}
                    <Tooltip title="Leave this empty to calculate forecasted/observed wind speed. Add a custom wind speed to influence the calculations">
                      <InfoIcon aria-label="info"></InfoIcon>
                    </Tooltip>
                  </TableSortLabel>
                </TableCell>
                <TableCell sortDirection={order}>
                  <TableSortLabel
                    direction={order}
                    onClick={() => {
                      toggleSorting(SortByColumn.Precipitation)
                    }}
                  >
                    Precip
                    <br />
                    (mm)
                  </TableSortLabel>
                </TableCell>
                <TableCell sortDirection={order}>
                  <TableSortLabel
                    direction={order}
                    onClick={() => {
                      toggleSorting(SortByColumn.FFMC)
                    }}
                  >
                    FFMC
                  </TableSortLabel>
                </TableCell>
                <TableCell sortDirection={order}>
                  <TableSortLabel
                    direction={order}
                    onClick={() => {
                      toggleSorting(SortByColumn.DMC)
                    }}
                  >
                    DMC
                  </TableSortLabel>
                </TableCell>
                <TableCell sortDirection={order}>
                  <TableSortLabel
                    direction={order}
                    onClick={() => {
                      toggleSorting(SortByColumn.DMC)
                    }}
                  >
                    DC
                  </TableSortLabel>
                </TableCell>
                <TableCell sortDirection={order}>
                  <TableSortLabel
                    direction={order}
                    onClick={() => {
                      toggleSorting(SortByColumn.ISI)
                    }}
                  >
                    ISI
                  </TableSortLabel>
                </TableCell>
                <TableCell sortDirection={order}>
                  <TableSortLabel
                    direction={order}
                    onClick={() => {
                      toggleSorting(SortByColumn.BUI)
                    }}
                  >
                    BUI
                  </TableSortLabel>
                </TableCell>
                <TableCell sortDirection={order}>
                  <TableSortLabel
                    direction={order}
                    onClick={() => {
                      toggleSorting(SortByColumn.BUI)
                    }}
                  >
                    FWI
                  </TableSortLabel>
                </TableCell>
                <TableCell sortDirection={order}>
                  <TableSortLabel
                    direction={order}
                    onClick={() => {
                      toggleSorting(SortByColumn.HFI)
                    }}
                  >
                    HFI
                  </TableSortLabel>
                </TableCell>
                <TableCell sortDirection={order}>
                  <TableSortLabel
                    direction={order}
                    onClick={() => {
                      toggleSorting(SortByColumn.CriticalHours4000)
                    }}
                  >
                    Critical
                    <br />
                    Hours
                    <br />
                    (4000 kW/m)
                  </TableSortLabel>
                </TableCell>
                <TableCell sortDirection={order}>
                  <TableSortLabel
                    direction={order}
                    onClick={() => {
                      toggleSorting(SortByColumn.CriticalHours10000)
                    }}
                  >
                    Critical
                    <br />
                    Hours
                    <br />
                    (10000 kW/m)
                  </TableSortLabel>
                </TableCell>
                <TableCell sortDirection={order}>
                  <TableSortLabel
                    direction={order}
                    onClick={() => {
                      toggleSorting(SortByColumn.ROS)
                    }}
                  >
                    ROS
                    <br />
                    (m/min)
                  </TableSortLabel>
                </TableCell>
                <TableCell sortDirection={order}>
                  <TableSortLabel
                    direction={order}
                    onClick={() => {
                      toggleSorting(SortByColumn.FireType)
                    }}
                  >
                    Fire Type
                  </TableSortLabel>
                </TableCell>
                <TableCell sortDirection={order}>
                  <TableSortLabel
                    direction={order}
                    onClick={() => {
                      toggleSorting(SortByColumn.CFB)
                    }}
                  >
                    CFB (%)
                  </TableSortLabel>
                </TableCell>
                <TableCell sortDirection={order}>
                  <TableSortLabel
                    direction={order}
                    onClick={() => {
                      toggleSorting(SortByColumn.FlameLength)
                    }}
                  >
                    Flame <br />
                    Length <br /> (m)
                  </TableSortLabel>
                </TableCell>
                <TableCell sortDirection={order}>
                  <TableSortLabel
                    direction={order}
                    onClick={() => {
                      toggleSorting(SortByColumn.ThirtyMinFireSize)
                    }}
                  >
                    30 min <br />
                    fire size <br />
                    (hectares)
                  </TableSortLabel>
                </TableCell>
                <TableCell sortDirection={order}>
                  <TableSortLabel
                    direction={order}
                    onClick={() => {
                      toggleSorting(SortByColumn.SixtyMinFireSize)
                    }}
                  >
                    60 min <br />
                    fire size <br />
                    (hectares)
                  </TableSortLabel>
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody data-testid="fba-table-body">
              {sortedRows.map((row, ri) => {
                return (
                  <TableRow key={row.id}>
                    <TableCell className={classes.dataRow}>
                      <SelectionCheckbox fbaInputGridProps={props} rowId={ri} />
                    </TableCell>
                    <TableCell className={classes.dataRow}>{row.zone_code}</TableCell>
                    <TableCell className={classes.dataRow}>
                      <WeatherStationCell
                        fbaInputGridProps={props}
                        classNameMap={classes}
                        value={row.weatherStation}
                        rowId={row.id}
                      />
                    </TableCell>
                    <TableCell className={classes.dataRow}>{row.elevation}</TableCell>
                    <TableCell className={classes.dataRow}>
                      <FuelTypeCell
                        fbaInputGridProps={props}
                        classNameMap={classes}
                        value={row.fuelType}
                        rowId={row.id}
                      />
                    </TableCell>
                    <TableCell className={classes.dataRow}>
                      <GrassCureCell
                        fbaInputGridProps={props}
                        classNameMap={classes}
                        value={row.grassCure}
                        rowId={row.id}
                      />
                    </TableCell>
                    <TableCell
                      className={
                        !isUndefined(row.status) &&
                        row.status.toLowerCase() === 'adjusted'
                          ? classes.adjustedValueCell
                          : classes.dataRow
                      }
                    >
                      {row.status}
                    </TableCell>
                    <TableCell className={classes.dataRow}>{row.temp}</TableCell>
                    <TableCell className={classes.dataRow}>{row.rh}</TableCell>
                    <TableCell className={classes.dataRow}>{row.wind_direction}</TableCell>
                    <TableCell className={classes.dataRow}>
                      <WindSpeedCell
                        fbaInputGridProps={props}
                        inputValue={row.windSpeed}
                        calculatedValue={sortedRows[ri].wind_speed}
                        rowId={row.id}
                      />
                    </TableCell>
                    <TableCell className={classes.dataRow}>{row.precipitation}</TableCell>
                    <TableCell className={classes.dataRow}>
                      {row.fine_fuel_moisture_code?.toFixed(DECIMAL_PLACES)}
                    </TableCell>
                    <TableCell className={classes.dataRow}>
                      {row.duff_moisture_code?.toFixed(DECIMAL_PLACES)}
                    </TableCell>
                    <TableCell className={classes.dataRow}>{row.drought_code?.toFixed(DECIMAL_PLACES)}</TableCell>
                    <TableCell className={classes.dataRow}>
                      {row.initial_spread_index?.toFixed(DECIMAL_PLACES)}
                    </TableCell>
                    <TableCell className={classes.dataRow}>{row.build_up_index?.toFixed(DECIMAL_PLACES)}</TableCell>
                    <TableCell className={classes.dataRow}>
                      {row.fire_weather_index?.toFixed(DECIMAL_PLACES)}
                    </TableCell>
                    <TableCell className={classes.dataRow}>
                      {row.head_fire_intensity?.toFixed(DECIMAL_PLACES)}
                    </TableCell>
                    <TableCell className={classes.dataRow}>
                      {formatCriticalHoursAsString(row.critical_hours_hfi_4000)}
                    </TableCell>
                    <TableCell className={classes.dataRow}>
                      {formatCriticalHoursAsString(row.critical_hours_hfi_10000)}
                    </TableCell>
                    <TableCell className={classes.dataRow}>{row.rate_of_spread?.toFixed(DECIMAL_PLACES)}</TableCell>
                    <TableCell className={classes.dataRow}>{row?.fire_type}</TableCell>
                    <TableCell className={classes.dataRow}>
                      {/* CFB comes in as a number 0 to 1, so we multiple by 100 to get the percentage */}
                      {!isUndefined(row.percentage_crown_fraction_burned) &&
                        (row.percentage_crown_fraction_burned * 100).toFixed(
                          DECIMAL_PLACES
                        )}
                    </TableCell>
                    <TableCell className={classes.dataRow}>{row.flame_length?.toFixed(DECIMAL_PLACES)}</TableCell>
                    <TableCell className={classes.dataRow}>
                      {row.thirty_minute_fire_size?.toFixed(DECIMAL_PLACES)}
                    </TableCell>
                    <TableCell className={classes.dataRow}>
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

export default React.memo(FBAInputGrid)
