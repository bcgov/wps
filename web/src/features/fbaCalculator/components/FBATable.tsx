import React, { useEffect, useState } from 'react'
import { difference, filter, findIndex, isEmpty, isUndefined } from 'lodash'
import {
  Checkbox,
  FormControl,
  LinearProgress,
  makeStyles,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel
} from '@material-ui/core'
import { Button } from 'components'
import { CriticalHoursHFI, FBAStation } from 'api/fbaCalcAPI'
import WeatherStationCell from 'features/fbaCalculator/components/WeatherStationCell'
import FuelTypeCell from 'features/fbaCalculator/components/FuelTypeCell'
import GrassCureCell from 'features/fbaCalculator/components/GrassCureCell'
import WindSpeedCell from 'features/fbaCalculator/components/WindSpeedCell'
import SelectionCheckbox from 'features/fbaCalculator/components/SelectionCheckbox'
import { Order } from 'utils/table'
import { FBATableRow, RowManager, SortByColumn } from 'features/fbaCalculator/RowManager'
import { GeoJsonStation, getStations, StationSource } from 'api/stationAPI'
import { selectFireWeatherStations, selectFireBehaviourCalcResult } from 'app/rootReducer'
import { FuelTypes } from 'features/fbaCalculator/fuelTypes'
import { fetchFireBehaviourStations } from 'features/fbaCalculator/slices/fbaCalculatorSlice'
import {
  getRowsFromUrlParams,
  getNextRowIdFromRows,
  getUrlParamsFromRows
} from 'features/fbaCalculator/utils'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { DateTime } from 'luxon'
import { useDispatch, useSelector } from 'react-redux'
import { useLocation, useHistory } from 'react-router-dom'
import DatePicker from 'features/fbaCalculator/components/DatePicker'
import assert from 'assert'
import { isRowInvalid } from 'features/fbaCalculator/validation'

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
      padding: '6px 6px 6px 6px',
      height: '40px'
    },

    '& .MuiTableCell-stickyHeader': {
      padding: '8px'
    },

    '& .MuiInputBase-root': {
      fontSize: '1em'
    },

    '& .MuiOutlinedInput-root': {
      padding: '0'
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
    paddingRight: '8px'
  },
  tableHeaderRow: {
    padding: '8px'
  }
}))

const FBAInputGrid = (props: FBAInputGridProps) => {
  const DECIMAL_PLACES = 1

  const classes = useStyles()
  const history = useHistory()
  const location = useLocation()
  const dispatch = useDispatch()

  const [headerSelected, setHeaderSelect] = useState<boolean>(false)
  const [dateOfInterest, setDateOfInterest] = useState(DateTime.now().toISODate())
  const [rowIdsToUpdate, setRowIdsToUpdate] = useState<Set<number>>(new Set())
  const [sortByColumn, setSortByColumn] = useState<SortByColumn>(SortByColumn.Station)
  const [initialLoad, setInitialLoad] = useState<boolean>(true)
  const [selected, setSelected] = useState<number[]>([])
  const [order, setOrder] = useState<Order>('desc')
  const [rows, setRows] = useState<FBATableRow[]>([])
  const { stations } = useSelector(selectFireWeatherStations)
  const { fireBehaviourResultStations, loading } = useSelector(
    selectFireBehaviourCalcResult
  )
  const [calculatedResults, setCalculatedResults] = useState<FBAStation[]>(
    fireBehaviourResultStations
  )

  const rowsFromQuery = getRowsFromUrlParams(location.search)

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

  useEffect(() => {
    dispatch(fetchWxStations(getStations, StationSource.wildfire_one))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (stations.length > 0) {
      const stationCodeMap = new Map(
        stationMenuOptions.map(station => [station.value, station.label])
      )

      const sortedRows = RowManager.sortRows(
        sortByColumn,
        order,
        rowsFromQuery.map(inputRow => ({
          ...RowManager.buildFBCTableRow(inputRow, stationCodeMap)
        }))
      )
      setRows(sortedRows)
      dispatch(fetchFireBehaviourStations(dateOfInterest, sortedRows))
    }
  }, [stations]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (stations.length > 0) {
      const rowsToUpdate = rows.filter(row => rowIdsToUpdate.has(row.id))
      if (!isEmpty(rowsToUpdate)) {
        dispatch(fetchFireBehaviourStations(dateOfInterest, rowsToUpdate))
      }
    }
  }, [location]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    // Row updates
    if (!isEmpty(rowIdsToUpdate) && fireBehaviourResultStations.length > 0) {
      const updatedRows = RowManager.updateRows(rows, fireBehaviourResultStations)
      setRows(updatedRows)

      const updatedRowIds = difference(
        Array.from(rowIdsToUpdate),
        fireBehaviourResultStations.map(result => result.id)
      )
      setRowIdsToUpdate(new Set(updatedRowIds))
    }
    // Initial row list page load
    if (initialLoad && fireBehaviourResultStations.length > 0) {
      const sortedRows = RowManager.sortRows(
        sortByColumn,
        order,
        RowManager.updateRows(rows, fireBehaviourResultStations)
      )
      setRows(sortedRows)
      setInitialLoad(false)
    }
    const updatedCalculatedResults = RowManager.updateRows(
      calculatedResults,
      fireBehaviourResultStations
    )
    setCalculatedResults(updatedCalculatedResults)
  }, [fireBehaviourResultStations]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const sortedRows = RowManager.sortRows(sortByColumn, order, rows)
    setRows(sortedRows)
  }, [order]) // eslint-disable-line react-hooks/exhaustive-deps

  const addStation = () => {
    const newRowId = getNextRowIdFromRows(rows)
    const newRow = {
      id: newRowId,
      weatherStation: null,
      fuelType: null,
      grassCure: undefined,
      windSpeed: undefined
    }
    assert(!new Set(rows.map(row => row.id)).has(newRowId))
    const newRows = rows.concat(newRow)
    setRows(newRows)
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

  const updateRow = (id: number, updatedRow: FBATableRow, dispatchUpdate = true) => {
    const newRows = [...rows]
    const index = findIndex(newRows, row => row.id === id)

    newRows[index] = updatedRow
    setRows(newRows)

    if (!rowIdsToUpdate.has(id)) {
      rowIdsToUpdate.add(id)
      const toUpdate = new Set(rowIdsToUpdate)
      setRowIdsToUpdate(toUpdate)
    }
    if (dispatchUpdate) {
      updateQueryParams(getUrlParamsFromRows(newRows))
    }
  }

  const updateQueryParams = (queryParams: string) => {
    history.push({
      search: queryParams
    })
  }

  const updateDate = () => {
    dispatch(fetchFireBehaviourStations(dateOfInterest, rows))
  }

  const toggleSorting = (selectedColumn: SortByColumn) => {
    if (sortByColumn !== selectedColumn) {
      setSortByColumn(selectedColumn)
    } else {
      setOrder(order === 'asc' ? 'desc' : 'asc')
    }
  }

  const formatCriticalHoursAsString = (
    criticalHours: CriticalHoursHFI | undefined | null
  ): string | undefined => {
    if (criticalHours === undefined || criticalHours === null) {
      return undefined
    }
    return `${criticalHours.start}:00 - ${criticalHours.end}:00`
  }

  return (
    <React.Fragment>
      <FormControl className={classes.formControl}>
        <DatePicker
          date={dateOfInterest}
          onChange={setDateOfInterest}
          updateDate={updateDate}
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
            {loading && <LinearProgress />}
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
                          setSelected([])
                          setHeaderSelect(false)
                        } else {
                          setSelected(rows.map(row => row.id))
                          setHeaderSelect(true)
                        }
                      }}
                    />
                  </TableCell>
                  <TableCell key="header-zone" sortDirection={order}>
                    <TableSortLabel
                      className={classes.tableHeaderRow}
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
                      FBP Fuel Type
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
                      Wind Speed (km/h)
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
                {rows.map((row, ri) => {
                  return (
                    !isUndefined(row) && (
                      <TableRow key={row.id}>
                        <TableCell className={classes.dataRow}>
                          <SelectionCheckbox
                            selected={selected}
                            updateSelected={(newSelected: number[]) =>
                              setSelected(newSelected)
                            }
                            disabled={rowIdsToUpdate.has(row.id) && !isRowInvalid(row)}
                            rowId={row.id}
                          />
                        </TableCell>
                        <TableCell className={classes.dataRow}>{row.zone_code}</TableCell>
                        <TableCell className={classes.dataRow}>
                          <WeatherStationCell
                            stationOptions={stationMenuOptions}
                            inputRows={rows}
                            updateRow={updateRow}
                            classNameMap={classes}
                            value={row.weatherStation}
                            disabled={rowIdsToUpdate.has(row.id) && !isRowInvalid(row)}
                            rowId={row.id}
                          />
                        </TableCell>
                        <TableCell className={classes.dataRow}>{row.elevation}</TableCell>
                        <TableCell className={classes.dataRow}>
                          <FuelTypeCell
                            fuelTypeOptions={fuelTypeMenuOptions}
                            inputRows={rows}
                            updateRow={updateRow}
                            classNameMap={classes}
                            value={row.fuelType}
                            disabled={rowIdsToUpdate.has(row.id) && !isRowInvalid(row)}
                            rowId={row.id}
                          />
                        </TableCell>
                        <TableCell className={classes.dataRow}>
                          <GrassCureCell
                            inputRows={rows}
                            updateRow={updateRow}
                            classNameMap={classes}
                            value={row.grassCure}
                            disabled={rowIdsToUpdate.has(row.id) && !isRowInvalid(row)}
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
                        <TableCell className={classes.dataRow}>
                          {row.wind_direction}
                        </TableCell>
                        <TableCell className={classes.dataRow}>
                          <WindSpeedCell
                            inputRows={rows}
                            updateRow={updateRow}
                            inputValue={row.windSpeed}
                            calculatedValue={rows[ri].wind_speed}
                            disabled={rowIdsToUpdate.has(row.id) && !isRowInvalid(row)}
                            rowId={row.id}
                          />
                        </TableCell>
                        <TableCell className={classes.dataRow}>
                          {row.precipitation}
                        </TableCell>
                        <TableCell className={classes.dataRow}>
                          {row.fine_fuel_moisture_code?.toFixed(DECIMAL_PLACES)}
                        </TableCell>
                        <TableCell className={classes.dataRow}>
                          {row.duff_moisture_code?.toFixed(DECIMAL_PLACES)}
                        </TableCell>
                        <TableCell className={classes.dataRow}>
                          {row.drought_code?.toFixed(DECIMAL_PLACES)}
                        </TableCell>
                        <TableCell className={classes.dataRow}>
                          {row.initial_spread_index?.toFixed(DECIMAL_PLACES)}
                        </TableCell>
                        <TableCell className={classes.dataRow}>
                          {row.build_up_index?.toFixed(DECIMAL_PLACES)}
                        </TableCell>
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
                        <TableCell className={classes.dataRow}>
                          {row.rate_of_spread?.toFixed(DECIMAL_PLACES)}
                        </TableCell>
                        <TableCell className={classes.dataRow}>
                          {row?.fire_type}
                        </TableCell>
                        <TableCell className={classes.dataRow}>
                          {/* CFB comes in as a number 0 to 1, so we multiple by 100 to get the percentage */}
                          {!isUndefined(row.percentage_crown_fraction_burned) &&
                            (row.percentage_crown_fraction_burned * 100).toFixed(
                              DECIMAL_PLACES
                            )}
                        </TableCell>
                        <TableCell className={classes.dataRow}>
                          {row.flame_length?.toFixed(DECIMAL_PLACES)}
                        </TableCell>
                        <TableCell className={classes.dataRow}>
                          {row.thirty_minute_fire_size?.toFixed(DECIMAL_PLACES)}
                        </TableCell>
                        <TableCell className={classes.dataRow}>
                          {row.sixty_minute_fire_size?.toFixed(DECIMAL_PLACES)}
                        </TableCell>
                      </TableRow>
                    )
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
