import React, { useEffect, useState } from 'react'
import { filter, isUndefined } from 'lodash'
import {
  Checkbox,
  FormControl,
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
import { Button } from 'components'
import InfoIcon from '@material-ui/icons/Info'
import { FBCStation } from 'api/fbCalcAPI'
import WeatherStationCell from 'features/fbaCalculator/components/WeatherStationCell'
import FuelTypeCell from 'features/fbaCalculator/components/FuelTypeCell'
import GrassCureCell from 'features/fbaCalculator/components/GrassCureCell'
import WindSpeedCell from 'features/fbaCalculator/components/WindSpeedCell'
import SelectionCheckbox from 'features/fbaCalculator/components/SelectionCheckbox'
import { Order } from 'utils/table'
import { RowManager, SortByColumn } from 'features/fbaCalculator/RowManager'
import { GridRowId } from '@material-ui/data-grid'
import { GeoJsonStation, getStations, StationSource } from 'api/stationAPI'
import { selectFireWeatherStations, selectFireBehaviourCalcResult } from 'app/rootReducer'
import { FuelTypes } from 'features/fbaCalculator/fuelTypes'
import { fetchFireBehaviourStations } from 'features/fbaCalculator/slices/fbaCalculatorSlice'
import {
  getRowsFromUrlParams,
  getMostRecentIdFromRows,
  getUrlParamsFromRows
} from 'features/fbaCalculator/utils'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { DateTime } from 'luxon'
import { useDispatch, useSelector } from 'react-redux'
import { useLocation, useHistory } from 'react-router-dom'
import DatePicker from 'features/fbaCalculator/components/DatePicker'

export interface FBAInputGridProps {
  testId?: string
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

const useStyles = makeStyles(theme => ({
  display: {
    paddingBottom: 12,

    '& .MuiTableCell-sizeSmall': {
      padding: '6px 12px 6px 6px'
    }
  },
  formControl: {
    margin: theme.spacing(1),
    minWidth: 210
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
    fontWeight: 'bold',
    color: '#460270'
  }
}))

const FBAInputGrid = (props: FBAInputGridProps) => {
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

  const [dateOfInterest, setDateOfInterest] = useState(DateTime.now().toISODate())

  const { stations } = useSelector(selectFireWeatherStations)

  const stationMenuOptions: GridMenuOption[] = (stations as GeoJsonStation[]).map(
    station => ({
      value: String(station.properties.code),
      label: `${station.properties.name} (${station.properties.code})`
    })
  )

  const fuelTypeMenuOptions: GridMenuOption[] = Object.entries(FuelTypes.get()).map(
    ([key, value]) => ({
      value: key,
      label: value.friendlyName
    })
  )
  const location = useLocation()
  const history = useHistory()

  const rowsFromQuery = getRowsFromUrlParams(location.search)
  const [rows, setRows] = useState<FBAInputRow[]>(rowsFromQuery)
  const lastId = getMostRecentIdFromRows(rows)

  const [rowId, setRowId] = useState(lastId + 1)
  const [selected, setSelected] = useState<number[]>([])

  const { fireBehaviourResultStations } = useSelector(selectFireBehaviourCalcResult)
  const [calculatedResults, setCalculatedResults] = useState<FBCStation[]>(
    fireBehaviourResultStations
  )

  useEffect(() => {
    setCalculatedResults(fireBehaviourResultStations)
  }, [fireBehaviourResultStations]) // eslint-disable-line react-hooks/exhaustive-deps

  const dispatch = useDispatch()

  const addStation = () => {
    const newRowId = rowId + 1
    setRowId(newRowId)
    const newRow = {
      id: rowId,
      weatherStation: undefined,
      fuelType: undefined,
      grassCure: undefined,
      windSpeed: undefined
    }
    const newRows = [...rows, newRow]
    setRows(newRows)
    updateQueryParams(getUrlParamsFromRows(newRows))
  }

  const deleteSelectedStations = () => {
    const selectedSet = new Set<number>(selected)
    const unselectedRows = rows.filter(row => !selectedSet.has(row.id))
    const updatedCalculateRows = filter(calculatedResults, (_, i) => !selectedSet.has(i))
    setRows(unselectedRows)
    setCalculatedResults(updatedCalculateRows)
    updateQueryParams(getUrlParamsFromRows(unselectedRows))
    setSelected([])
  }

  const updateRow = (id: GridRowId, updatedRow: FBAInputRow, dispatchUpdate = true) => {
    const newRows = [...rows]

    // rowId is the row array index
    newRows[id as number] = updatedRow
    setRows(newRows)
    if (dispatchUpdate) {
      updateQueryParams(getUrlParamsFromRows(newRows))
      dispatch(fetchFireBehaviourStations(dateOfInterest, newRows))
    }
  }

  useEffect(() => {
    dispatch(fetchWxStations(getStations, StationSource.wildfire_one))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const updateQueryParams = (queryParams: string) => {
    history.push({
      search: queryParams
    })
  }

  useEffect(() => {
    const rows = getRowsFromUrlParams(location.search)
    setRows(rows)
    const mostRecentId = getMostRecentIdFromRows(rows)
    setRowId(mostRecentId + 1)

    if (rows.length > 0) {
      dispatch(fetchFireBehaviourStations(dateOfInterest, rows))
    }
  }, [location]) // eslint-disable-line react-hooks/exhaustive-deps

  const autoUpdateHandler = () => {
    dispatch(fetchFireBehaviourStations(dateOfInterest, rows))
  }

  const DECIMAL_PLACES = 1

  const stationCodeMap = new Map(
    stationMenuOptions.map(station => [station.value, station.label])
  )
  const rowManager = new RowManager(stationCodeMap)

  const sortedRows = RowManager.sortRows(
    sortByColumn,
    order,
    rowManager.mergeFBARows(rows, calculatedResults)
  )

  return (
    <React.Fragment>
      <FormControl className={classes.formControl}>
        <DatePicker
          date={dateOfInterest}
          onChange={setDateOfInterest}
          autoUpdateHandler={autoUpdateHandler}
        />
      </FormControl>
      <FormControl className={classes.formControl}>
        <Button
          data-testid="add-row"
          variant="contained"
          color="primary"
          spinnercolor="white"
          onClick={addStation}
        >
          Add Row
        </Button>
      </FormControl>
      <FormControl className={classes.formControl}>
        <Button
          data-testid="remove-rows"
          disabled={rows.length === 0}
          variant="contained"
          color="primary"
          spinnercolor="white"
          onClick={deleteSelectedStations}
        >
          Remove Row(s)
        </Button>
      </FormControl>
      <div className={classes.display} data-testid={props.testId}>
        <Paper className={classes.paper} elevation={1}>
          <TableContainer className={classes.tableContainer}>
            <Table stickyHeader aria-label="Fire Behaviour Analysis table">
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
                          setSelected([])
                          setHeaderSelect(false)
                        } else {
                          setSelected(rows.map((_, i) => i))
                          setHeaderSelect(true)
                        }
                      }}
                    />
                  </TableCell>
                  <TableCell key="header-zone" sortDirection={order}>
                    <TableSortLabel
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
                      <br />
                      Fuel
                      <br />
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
                    Critical
                    <br />
                    Hours
                    <br />
                    (4000 kW/m)
                  </TableCell>
                  <TableCell sortDirection={order}>
                    Critical
                    <br />
                    Hours
                    <br />
                    (10000 kW/m)
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
                      <TableCell>
                        <SelectionCheckbox
                          selected={selected}
                          updateSelected={(newSelected: number[]) =>
                            setSelected(newSelected)
                          }
                          rowId={ri}
                        />
                      </TableCell>
                      <TableCell>{row.zone_code}</TableCell>
                      <TableCell>
                        <WeatherStationCell
                          stationOptions={stationMenuOptions}
                          inputRows={rows}
                          updateRow={updateRow}
                          classNameMap={classes}
                          value={row.weatherStation}
                          rowId={row.id}
                        />
                      </TableCell>
                      <TableCell>{row.elevation}</TableCell>
                      <TableCell>
                        <FuelTypeCell
                          fuelTypeOptions={fuelTypeMenuOptions}
                          inputRows={rows}
                          updateRow={updateRow}
                          classNameMap={classes}
                          value={row.fuelType}
                          rowId={row.id}
                        />
                      </TableCell>
                      <TableCell>
                        <GrassCureCell
                          inputRows={rows}
                          updateRow={updateRow}
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
                            : undefined
                        }
                      >
                        {row.status}
                      </TableCell>
                      <TableCell>{row.temp}</TableCell>
                      <TableCell>{row.rh}</TableCell>
                      <TableCell>{row.wind_direction}</TableCell>
                      <TableCell>
                        <WindSpeedCell
                          inputRows={rows}
                          updateRow={updateRow}
                          inputValue={row.windSpeed}
                          calculatedValue={sortedRows[ri].wind_speed}
                          rowId={row.id}
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
    </React.Fragment>
  )
}

export default React.memo(FBAInputGrid)
