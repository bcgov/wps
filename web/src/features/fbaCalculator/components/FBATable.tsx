import React, { useEffect, useState } from 'react'
import { difference, filter, findIndex, isEmpty, isEqual, isUndefined } from 'lodash'
import { Grid, TableBody, TableCell, TableRow } from '@mui/material'
import GetAppIcon from '@mui/icons-material/GetApp'
import ViewColumnOutlinedIcon from '@mui/icons-material/ViewColumnOutlined'
import { CsvBuilder } from 'filefy'
import { Button, ErrorBoundary } from 'components'
import { FBAStation } from 'api/fbaCalcAPI'
import WeatherStationCell from 'features/fbaCalculator/components/WeatherStationCell'
import FuelTypeCell from 'features/fbaCalculator/components/FuelTypeCell'
import GrassCureCell from 'features/fbaCalculator/components/GrassCureCell'
import PrecipCell from 'features/fbaCalculator/components/PrecipCell'
import WindSpeedCell from 'features/fbaCalculator/components/WindSpeedCell'
import { Order, PST_UTC_OFFSET } from 'utils/constants'
import { FBATableRow, RowManager, SortByColumn } from 'features/fbaCalculator/RowManager'
import { GeoJsonStation, getStations, StationSource } from 'api/stationAPI'
import { selectFireWeatherStations, selectFireBehaviourCalcResult } from 'app/rootReducer'
import { FuelTypes } from 'features/fbaCalculator/fuelTypes'
import { fetchFireBehaviourStations } from 'features/fbaCalculator/slices/fbaCalculatorSlice'
import {
  getRowsFromUrlParams,
  getNextRowIdFromRows,
  getUrlParamsFromRows,
  stripWindFromQueryParams
} from 'features/fbaCalculator/utils'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { DateTime } from 'luxon'
import { useDispatch, useSelector } from 'react-redux'
import { useLocation, useNavigate } from 'react-router-dom'
import { rowShouldUpdate, isWindSpeedInvalid, isPrecipInvalid } from 'features/fbaCalculator/validation'
import TextDisplayCell from 'features/fbaCalculator/components/TextDisplayCell'
import FixedDecimalNumberCell from 'features/fbaCalculator/components/FixedDecimalNumberCell'
import HFICell from 'components/HFICell'
import CrownFractionBurnedCell from 'features/fbaCalculator/components/CrownFractionBurnedCell'
import CriticalHoursCell from 'features/fbaCalculator/components/CriticalHoursCell'
import StatusCell from 'features/fbaCalculator/components/StatusCell'
import ErrorAlert from 'features/fbaCalculator/components/ErrorAlert'
import LoadingIndicatorCell from 'features/fbaCalculator/components/LoadingIndicatorCell'
import SelectionCell from 'features/fbaCalculator/components/SelectionCell'
import StickyCell from 'components/StickyCell'
import FBATableHead from 'features/fbaCalculator/components/FBATableHead'
import FireTable from 'components/FireTable'
import FBATableInstructions from 'features/fbaCalculator/components/FBATableInstructions'
import FilterColumnsModal from 'components/FilterColumnsModal'
import WPSDatePicker from 'components/WPSDatePicker'
import { AppDispatch } from 'app/store'
import { DataTableCell } from 'features/hfiCalculator/components/StyledPlanningAreaComponents'
import { theme } from '@/app/theme'
import AboutDataPopover from '@/components/AboutDataPopover'
import { FBAAboutDataContent } from '@/features/fbaCalculator/components/FbaAboutDataContent'
import ResetDialog from '@/components/ResetDialog'
export interface FBATableProps {
  maxWidth?: number
  maxHeight?: number
  minHeight?: number
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
  precip: number | undefined
  windSpeed: number | undefined
}

export type ColumnLabel =
  | 'Zone'
  | 'Weather Station'
  | 'Elevation'
  | 'FBP Fuel Type'
  | 'Grass Cure'
  | 'Status'
  | 'Temp'
  | 'RH'
  | 'Wind Dir'
  | 'Wind Speed (km/h)'
  | 'Precip (mm)'
  | 'FFMC'
  | 'DMC'
  | 'DC'
  | 'ISI'
  | 'BUI'
  | 'FWI'
  | 'HFI'
  | 'Critical Hours (4000 kW/m)'
  | 'Critical Hours (10000 kW/m)'
  | 'ROS (m/min)'
  | 'Fire Type'
  | 'CFB (%)'
  | 'Flame Length (m)'
  | '30 min fire size (ha)'
  | '60 min fire size (ha)'

const tableColumnLabels: ColumnLabel[] = [
  'Zone',
  'Weather Station',
  'Elevation',
  'FBP Fuel Type',
  'Grass Cure',
  'Status',
  'Temp',
  'RH',
  'Wind Dir',
  'Wind Speed (km/h)',
  'Precip (mm)',
  'FFMC',
  'DMC',
  'DC',
  'ISI',
  'BUI',
  'FWI',
  'HFI',
  'Critical Hours (4000 kW/m)',
  'Critical Hours (10000 kW/m)',
  'ROS (m/min)',
  'Fire Type',
  'CFB (%)',
  'Flame Length (m)',
  '30 min fire size (ha)',
  '60 min fire size (ha)'
]

const FBATable = (props: FBATableProps) => {
  const navigate = useNavigate()
  const location = useLocation()
  const dispatch: AppDispatch = useDispatch()

  const [headerSelected, setHeaderSelect] = useState<boolean>(false)
  const [dateOfInterest, setDateOfInterest] = useState(DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`))
  const [rowIdsToUpdate, setRowIdsToUpdate] = useState<Set<number>>(new Set())
  const [sortByColumn, setSortByColumn] = useState<SortByColumn>(SortByColumn.Station)
  const [initialLoad, setInitialLoad] = useState<boolean>(true)
  const [selected, setSelected] = useState<number[]>([])
  const [order, setOrder] = useState<Order>('desc')
  const [rows, setRows] = useState<FBATableRow[]>([])
  const [modalOpen, setModalOpen] = useState<boolean>(false)
  const { stations, error: stationsError } = useSelector(selectFireWeatherStations)
  const { fireBehaviourResultStations, loading, error: fbaResultsError } = useSelector(selectFireBehaviourCalcResult)
  const [calculatedResults, setCalculatedResults] = useState<FBAStation[]>(fireBehaviourResultStations)
  const [visibleColumns, setVisibleColumns] = useState<ColumnLabel[]>(tableColumnLabels)
  const [showResetDialog, setShowResetDialog] = useState<boolean>(false)

  const stationMenuOptions: GridMenuOption[] = (stations as GeoJsonStation[]).map(station => ({
    value: String(station.properties.code),
    label: `${station.properties.name} (${station.properties.code})`
  }))

  const fuelTypeMenuOptions: GridMenuOption[] = Object.entries(FuelTypes.get()).map(([key, value]) => ({
    value: key,
    label: value.friendlyName
  }))

  useEffect(() => {
    // Strip the wind query parameters if present and update the URL
    updateQueryParams(stripWindFromQueryParams(location.search))
    dispatch(fetchWxStations(getStations, StationSource.wildfire_one))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (stations.length > 0) {
      const rowsFromQuery = getRowsFromUrlParams(location.search)
      const stationCodeMap = new Map(stationMenuOptions.map(station => [station.value, station.label]))

      const sortedRows = RowManager.sortRows(
        sortByColumn,
        order,
        rowsFromQuery.map(inputRow => ({
          ...RowManager.buildFBATableRow(inputRow, stationCodeMap)
        }))
      )
      if (rows.length > 0 || sortedRows.length > 0) {
        setRows(sortedRows)
      }

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
      const updatedRows = RowManager.updateRows(
        rows.filter(row => !isUndefined(row)),
        fireBehaviourResultStations
      )
      if (rows.length > 0 || updatedRows.length > 0) {
        setRows(updatedRows)
      }

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
        RowManager.updateRows(
          rows.filter(row => !isUndefined(row)),
          fireBehaviourResultStations
        )
      )
      if (rows.length > 0 || sortedRows.length > 0) {
        setRows(sortedRows)
      }
      setInitialLoad(false)
    }
    const updatedCalculatedResults = RowManager.updateRows(calculatedResults, fireBehaviourResultStations)
    setCalculatedResults(updatedCalculatedResults)
  }, [fireBehaviourResultStations, stations]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const sortedRows = RowManager.sortRows(
      sortByColumn,
      order,
      RowManager.updateRows(
        rows.filter(row => !isUndefined(row)),
        fireBehaviourResultStations
      )
    )
    const updatedCalculatedResults = RowManager.updateRows(calculatedResults, fireBehaviourResultStations)
    setCalculatedResults(updatedCalculatedResults)
    if (rows.length > 0 || sortedRows.length > 0) {
      setRows(sortedRows)
    }
  }, [dateOfInterest, fireBehaviourResultStations]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const sortedRows = RowManager.sortRows(
      sortByColumn,
      order,
      rows.filter(row => !isUndefined(row))
    )
    if (rows.length > 0 || sortedRows.length > 0) {
      setRows(sortedRows)
    }
  }, [order]) // eslint-disable-line react-hooks/exhaustive-deps

  const addStation = () => {
    const newRowId = getNextRowIdFromRows(rows.filter(row => !isUndefined(row)))
    const newRow = {
      id: newRowId,
      weatherStation: null,
      fuelType: null,
      grassCure: undefined,
      precip: undefined,
      windSpeed: undefined
    }
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

  const exportSelectedRows = () => {
    const selectedSet = new Set<number>(selected)
    const selectedRows = rows.filter(row => selectedSet.has(row.id))
    const selectedRowsAsStrings = RowManager.exportRowsAsStrings(selectedRows)
    const csvBuilder = new CsvBuilder(`FireCalc_${dateOfInterest}.csv`)
      .setColumns(tableColumnLabels)
      .addRows(selectedRowsAsStrings)
    csvBuilder.exportFile()
  }

  const getNewRows = (id: number, updatedRow: FBATableRow) => {
    const newRows = [...rows].filter(row => !isUndefined(row))
    const index = findIndex(newRows, row => row.id === id)

    newRows[index] = updatedRow
    setRows(newRows)

    if (!rowIdsToUpdate.has(id)) {
      rowIdsToUpdate.add(id)
      const toUpdate = new Set(rowIdsToUpdate)
      setRowIdsToUpdate(toUpdate)
    }
    return newRows
  }

  const updateRow = (id: number, updatedRow: FBATableRow, dispatchUpdate = true) => {
    const newRows = getNewRows(id, updatedRow)
    if (dispatchUpdate) {
      updateQueryParams(getUrlParamsFromRows(newRows))
    }
  }

  const updateRowDirect = (id: number, updatedRow: FBATableRow, dispatchUpdate = true) => {
    const newRows = getNewRows(id, updatedRow)
    if (dispatchUpdate) {
      dispatch(fetchFireBehaviourStations(dateOfInterest, newRows))
    }
  }

  const updateQueryParams = (queryParams: string) => {
    navigate({
      search: queryParams
    })
  }

  const updateDate = (newDate: DateTime) => {
    if (!isEqual(newDate, dateOfInterest)) {
      dispatch(fetchFireBehaviourStations(newDate, rows))
      setDateOfInterest(newDate)
    }
  }

  const toggleSorting = (selectedColumn: SortByColumn) => {
    if (sortByColumn !== selectedColumn) {
      setSortByColumn(selectedColumn)
    } else {
      setOrder(order === 'asc' ? 'desc' : 'asc')
    }
  }

  const openColumnsModal = () => {
    setModalOpen(true)
  }

  const openResetDialog = () => {
    setShowResetDialog(true)
  }

  const handleResetSelected = () => {
    setShowResetDialog(false)
    const rowsToUpdate = rows.filter(row => selected.includes(row.id))
    const updatedRows = rowsToUpdate.map(rowToUpdate => {
      rowToUpdate.precip = undefined
      rowToUpdate.windSpeed = undefined
      return rowToUpdate
    })
    dispatch(fetchFireBehaviourStations(dateOfInterest, updatedRows))
  }

  const filterColumnsCallback = (filterByColumns: ColumnLabel[]) => {
    setVisibleColumns(filterByColumns)
  }

  type TextDisplayCellType = keyof Pick<
    FBATableRow,
    'zone_code' | 'elevation' | 'temp' | 'rh' | 'wind_direction' | 'precipitation' | 'fire_type'
  >
  type FixedDecimalNumberCellType = keyof Pick<
    FBATableRow,
    | 'fine_fuel_moisture_code'
    | 'duff_moisture_code'
    | 'drought_code'
    | 'initial_spread_index'
    | 'build_up_index'
    | 'fire_weather_index'
    | 'rate_of_spread'
    | 'flame_length'
    | 'thirty_minute_fire_size'
    | 'sixty_minute_fire_size'
  >

  const getTextDisplayCell = (row: FBATableRow, rowProperty: TextDisplayCellType) => {
    return (
      <LoadingIndicatorCell loading={loading} rowUpdating={rowIdsToUpdate.has(row.id)} initialLoad={initialLoad}>
        <TextDisplayCell value={row[rowProperty]}></TextDisplayCell>
      </LoadingIndicatorCell>
    )
  }

  const getFixedDecimalNumberCell = (row: FBATableRow, rowProperty: FixedDecimalNumberCellType) => {
    return (
      <LoadingIndicatorCell loading={loading} rowUpdating={rowIdsToUpdate.has(row.id)} initialLoad={initialLoad}>
        <FixedDecimalNumberCell value={row[rowProperty]}></FixedDecimalNumberCell>
      </LoadingIndicatorCell>
    )
  }

  const getWeatherStationCell = (row: FBATableRow) => {
    return (
      <StickyCell left={50} zIndexOffset={1} backgroundColor="#FFFFFF">
        <WeatherStationCell
          stationOptions={stationMenuOptions}
          inputRows={rows}
          updateRow={updateRow}
          value={row.weatherStation}
          disabled={rowIdsToUpdate.has(row.id) && !rowShouldUpdate(row)}
          rowId={row.id}
        />
      </StickyCell>
    )
  }

  const getFuelTypeCell = (row: FBATableRow) => {
    return (
      <StickyCell left={280} zIndexOffset={1} backgroundColor="#FFFFFF">
        <FuelTypeCell
          fuelTypeOptions={fuelTypeMenuOptions}
          inputRows={rows}
          updateRow={updateRow}
          value={row.fuelType}
          disabled={rowIdsToUpdate.has(row.id) && !rowShouldUpdate(row)}
          rowId={row.id}
        />
      </StickyCell>
    )
  }

  const getGrassCureCell = (row: FBATableRow) => {
    return (
      <DataTableCell>
        <GrassCureCell
          inputRows={rows}
          updateRow={updateRow}
          value={row.grassCure}
          disabled={rowIdsToUpdate.has(row.id) && !rowShouldUpdate(row)}
          rowId={row.id}
        />
      </DataTableCell>
    )
  }

  const getStatusCell = (row: FBATableRow) => {
    return (
      <LoadingIndicatorCell loading={loading} rowUpdating={rowIdsToUpdate.has(row.id)} initialLoad={initialLoad}>
        <StatusCell value={row.status}></StatusCell>
      </LoadingIndicatorCell>
    )
  }

  const getPrecipCell = (row: FBATableRow) => {
    return (
      <DataTableCell>
        <PrecipCell
          inputRows={rows}
          updateRow={updateRowDirect}
          inputValue={row.precip}
          calculatedValue={row.precipitation}
          disabled={rowIdsToUpdate.has(row.id) && !rowShouldUpdate(row) && !isPrecipInvalid(row.precipitation)}
          rowId={row.id}
        />
      </DataTableCell>
    )
  }

  const getWindSpeedCell = (row: FBATableRow) => {
    return (
      <DataTableCell>
        <WindSpeedCell
          inputRows={rows}
          updateRow={updateRowDirect}
          inputValue={row.windSpeed}
          calculatedValue={row.wind_speed}
          disabled={rowIdsToUpdate.has(row.id) && !rowShouldUpdate(row) && !isWindSpeedInvalid(row.windSpeed)}
          rowId={row.id}
        />
      </DataTableCell>
    )
  }

  const getHFICell = (row: FBATableRow) => {
    return (
      <LoadingIndicatorCell loading={loading} rowUpdating={rowIdsToUpdate.has(row.id)} initialLoad={initialLoad}>
        <HFICell value={row.head_fire_intensity}></HFICell>
      </LoadingIndicatorCell>
    )
  }

  const getCriticalHours4000Cell = (row: FBATableRow) => {
    return (
      <LoadingIndicatorCell loading={loading} rowUpdating={rowIdsToUpdate.has(row.id)} initialLoad={initialLoad}>
        <CriticalHoursCell value={row.critical_hours_hfi_4000}></CriticalHoursCell>
      </LoadingIndicatorCell>
    )
  }

  const getCriticalHours10000Cell = (row: FBATableRow) => {
    return (
      <LoadingIndicatorCell loading={loading} rowUpdating={rowIdsToUpdate.has(row.id)} initialLoad={initialLoad}>
        <CriticalHoursCell value={row.critical_hours_hfi_10000}></CriticalHoursCell>
      </LoadingIndicatorCell>
    )
  }

  const getCFBCell = (row: FBATableRow) => {
    return (
      <LoadingIndicatorCell loading={loading} rowUpdating={rowIdsToUpdate.has(row.id)} initialLoad={initialLoad}>
        <CrownFractionBurnedCell value={row.percentage_crown_fraction_burned}></CrownFractionBurnedCell>
      </LoadingIndicatorCell>
    )
  }

  const columnCellComponents = (row: FBATableRow, colName: string) => {
    switch (colName) {
      case 'Zone': {
        return getTextDisplayCell(row, 'zone_code')
      }
      case 'Elevation': {
        return getTextDisplayCell(row, 'elevation')
      }
      case 'Temp': {
        return getTextDisplayCell(row, 'temp')
      }
      case 'RH': {
        return getTextDisplayCell(row, 'rh')
      }
      case 'Wind Dir': {
        return getTextDisplayCell(row, 'wind_direction')
      }
      case 'Precip (mm)': {
        return getPrecipCell(row)
      }
      case 'Weather Station': {
        return getWeatherStationCell(row)
      }
      case 'FBP Fuel Type': {
        return getFuelTypeCell(row)
      }
      case 'Grass Cure': {
        return getGrassCureCell(row)
      }
      case 'Status': {
        return getStatusCell(row)
      }
      case 'Wind Speed (km/h)': {
        return getWindSpeedCell(row)
      }
      case 'FFMC': {
        return getFixedDecimalNumberCell(row, 'fine_fuel_moisture_code')
      }
      case 'DMC': {
        return getFixedDecimalNumberCell(row, 'duff_moisture_code')
      }
      case 'DC': {
        return getFixedDecimalNumberCell(row, 'drought_code')
      }
      case 'ISI': {
        return getFixedDecimalNumberCell(row, 'initial_spread_index')
      }
      case 'BUI': {
        return getFixedDecimalNumberCell(row, 'build_up_index')
      }
      case 'FWI': {
        return getFixedDecimalNumberCell(row, 'fire_weather_index')
      }
      case 'HFI': {
        return getHFICell(row)
      }
      case 'Critical Hours (4000 kW/m)': {
        return getCriticalHours4000Cell(row)
      }
      case 'Critical Hours (10000 kW/m)': {
        return getCriticalHours10000Cell(row)
      }
      case 'ROS (m/min)': {
        return getFixedDecimalNumberCell(row, 'rate_of_spread')
      }
      case 'Fire Type': {
        return getTextDisplayCell(row, 'fire_type')
      }
      case 'CFB (%)': {
        return getCFBCell(row)
      }
      case 'Flame Length (m)': {
        return getFixedDecimalNumberCell(row, 'flame_length')
      }
      case '30 min fire size (ha)': {
        return getFixedDecimalNumberCell(row, 'thirty_minute_fire_size')
      }
      case '60 min fire size (ha)': {
        return getFixedDecimalNumberCell(row, 'sixty_minute_fire_size')
      }
    }
  }

  return (
    <React.Fragment>
      {stationsError ||
        (fbaResultsError && <ErrorAlert stationsError={stationsError} fbaResultsError={fbaResultsError} />)}
      <ErrorBoundary>
        <Grid
          container
          spacing={2}
          alignItems="top"
          justifyContent="center"
          paddingTop={theme.spacing(1)}
          paddingBottom={theme.spacing(1)}
        >
          <Grid item xs={4} container spacing={2} justifyContent="flex-start">
            <Grid item>
              <WPSDatePicker date={dateOfInterest} updateDate={updateDate} />
            </Grid>
            <Grid item>
              <Button
                data-testid="add-row"
                variant="contained"
                color="primary"
                spinnercolor="white"
                onClick={addStation}
              >
                Add Row
              </Button>
            </Grid>
            <Grid item>
              <Button
                data-testid="remove-rows"
                disabled={rows.length === 0}
                variant="outlined"
                color="primary"
                spinnercolor="white"
                onClick={deleteSelectedStations}
              >
                Remove Row(s)
              </Button>
            </Grid>
          </Grid>

          <Grid item xs={4} container spacing={2} justifyContent="center">
            <Grid item>
              <Button
                data-testid="export"
                variant="outlined"
                disabled={selected.length === 0}
                onClick={exportSelectedRows}
                sx={{ height: 'auto' }}
              >
                <GetAppIcon />
                Export Selection
              </Button>
            </Grid>
            <Grid item>
              <Button
                data-testid="filter-columns-btn"
                disabled={fireBehaviourResultStations.length === 0}
                onClick={openColumnsModal}
                variant="outlined"
              >
                <ViewColumnOutlinedIcon />
                Columns
              </Button>
            </Grid>
          </Grid>
          <Grid item xs={4} container spacing={2} justifyContent="flex-end">
            <Grid item>
              <Button
                data-testid="reset-selected-btn"
                disabled={selected.length === 0}
                onClick={openResetDialog}
                variant="outlined"
              >
                Reset Selected
              </Button>
            </Grid>
            <Grid item>
              <AboutDataPopover content={FBAAboutDataContent} />
            </Grid>
          </Grid>
        </Grid>

        <FilterColumnsModal
          modalOpen={modalOpen}
          columns={tableColumnLabels}
          setModalOpen={setModalOpen}
          parentCallback={filterColumnsCallback}
        />

        <ResetDialog
          showResetDialog={showResetDialog}
          setShowResetDialog={setShowResetDialog}
          handleResetButtonConfirm={handleResetSelected}
          message="Are you sure you want to reset the adjusted weather values of the selected rows?"
        />

        <FireTable ariaLabel="Fire Behaviour Analysis table" data-testid={props.testId}>
          <FBATableHead
            toggleSorting={toggleSorting}
            order={order}
            rows={rows}
            headerSelected={headerSelected}
            setHeaderSelect={setHeaderSelect}
            setSelected={setSelected}
            loading={loading}
            visibleColumns={visibleColumns}
          />
          <TableBody data-testid="fba-table-body">
            {rows.length === 0 ? (
              <TableRow>
                <TableCell colSpan={30}>
                  <FBATableInstructions />
                </TableCell>
              </TableRow>
            ) : (
              rows.map(row => {
                return (
                  !isUndefined(row) && (
                    <TableRow key={row.id}>
                      <StickyCell left={0} zIndexOffset={1} backgroundColor="#FFFFFF">
                        <SelectionCell
                          selected={selected}
                          updateSelected={(newSelected: number[]) => setSelected(newSelected)}
                          disabled={rowIdsToUpdate.has(row.id) && !rowShouldUpdate(row)}
                          rowId={row.id}
                        />
                      </StickyCell>
                      {visibleColumns.map(colName => {
                        return columnCellComponents(row, colName)
                      })}
                    </TableRow>
                  )
                )
              })
            )}
          </TableBody>
        </FireTable>
      </ErrorBoundary>
    </React.Fragment>
  )
}

export default React.memo(FBATable)
