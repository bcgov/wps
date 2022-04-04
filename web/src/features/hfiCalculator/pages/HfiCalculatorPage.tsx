import React, { useEffect } from 'react'
import { DateTime } from 'luxon'
import { Container, ErrorBoundary, GeneralHeader } from 'components'
import { fetchHFIStations } from 'features/hfiCalculator/slices/stationsSlice'
import {
  FireStartRange,
  PlanningAreaResult,
  setSelectedFireCentre,
  fetchHFIResult,
  fetchLoadDefaultHFIResult,
  fetchSetNewFireStarts,
  fetchSetStationSelected,
  setSaved,
  fetchPDFDownload,
  setSelectedPrepDate
} from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { useDispatch, useSelector } from 'react-redux'
import {
  selectHFIStations,
  selectHFIStationsLoading,
  selectHFICalculatorState
} from 'app/rootReducer'
import {
  CircularProgress,
  FormControl,
  makeStyles,
  Table,
  TableBody
} from '@material-ui/core'
import ViewSwitcher from 'features/hfiCalculator/components/ViewSwitcher'
import SaveButton from 'features/hfiCalculator/components/SaveButton'
import ViewSwitcherToggles from 'features/hfiCalculator/components/ViewSwitcherToggles'
import { formControlStyles, theme } from 'app/theme'
import { FireCentre } from 'api/hfiCalcAPI'
import { HFIPageSubHeader } from 'features/hfiCalculator/components/HFIPageSubHeader'
import { isNull, isUndefined } from 'lodash'
import HFIErrorAlert from 'features/hfiCalculator/components/HFIErrorAlert'
import DownloadPDFButton from 'features/hfiCalculator/components/DownloadPDFButton'
import EmptyFireCentreRow from 'features/hfiCalculator/components/EmptyFireCentre'
import { DateRange } from 'components/dateRangePicker/types'

function constructPlanningAreaFireStarts(
  planning_area_hfi_results: PlanningAreaResult[]
) {
  // TODO: delete this function when it's redundant!
  const fireStarts = {} as { [key: number]: FireStartRange[] }
  planning_area_hfi_results.forEach(planningAreaResult => {
    fireStarts[planningAreaResult.planning_area_id] = []
    planningAreaResult.daily_results.forEach(dailyResult => {
      fireStarts[planningAreaResult.planning_area_id].push(dailyResult.fire_starts)
    })
  })
  return fireStarts
}

const useStyles = makeStyles(() => ({
  ...formControlStyles,
  container: {
    display: 'flex',
    justifyContent: 'center'
  },
  helpIcon: {
    fill: theme.palette.primary.main
  },
  copyToClipboardInfoIcon: {
    marginLeft: '3px'
  },
  clipboardIcon: {
    marginRight: '3px'
  },
  aboutButtonText: {
    color: theme.palette.primary.main,
    textDecoration: 'underline',
    fontWeight: 'bold'
  },
  positionStyler: {
    position: 'absolute',
    right: '20px'
  },
  prepDays: {
    margin: theme.spacing(1),
    minWidth: 100
  },
  saveButton: {
    margin: theme.spacing(1),
    float: 'right'
  }
}))

const HfiCalculatorPage: React.FunctionComponent = () => {
  const classes = useStyles()

  const dispatch = useDispatch()
  const { fireCentres, error: fireCentresError } = useSelector(selectHFIStations)
  const stationDataLoading = useSelector(selectHFIStationsLoading)
  const { selectedPrepDate, result, selectedFireCentre, loading, saved, dateRange } =
    useSelector(selectHFICalculatorState)

  const setSelectedStation = (
    planningAreaId: number,
    code: number,
    selected: boolean
  ) => {
    if (!isUndefined(result) && !isUndefined(result.date_range.start_date)) {
      dispatch(setSaved(false))
      dispatch(
        fetchSetStationSelected(
          result.selected_fire_center_id,
          result.date_range.start_date,
          planningAreaId,
          code,
          selected
        )
      )
    }
  }

  const setNewFireStarts = (
    areaId: number,
    dayOffset: number,
    newFireStarts: FireStartRange
  ) => {
    if (!isUndefined(result) && !isUndefined(result.date_range.start_date)) {
      dispatch(setSaved(false))
      dispatch(
        fetchSetNewFireStarts(
          result.selected_fire_center_id,
          result.date_range.start_date,
          areaId,
          DateTime.fromISO(result.date_range.start_date + 'T00:00+00:00', {
            setZone: true
          })
            .plus({ days: dayOffset })
            .toISODate(),
          newFireStarts.id
        )
      )
    }
  }

  const updatePrepDateRange = (newDateRange: DateRange) => {
    if (
      newDateRange !== dateRange &&
      !isUndefined(selectedFireCentre) &&
      !isUndefined(result)
    ) {
      dispatch(
        fetchHFIResult({
          selected_station_code_ids: result.selected_station_code_ids,
          selected_fire_center_id: result.selected_fire_center_id,
          planning_area_fire_starts: constructPlanningAreaFireStarts(
            result.planning_area_hfi_results
          ),
          date_range: {
            start_date: newDateRange.startDate?.toISOString().split('T')[0],
            end_date: newDateRange.endDate?.toISOString().split('T')[0]
          }
        })
      )
      dispatch(setSaved(false))
    }
  }

  const setSelectedFireCentreFromLocalStorage = () => {
    const findCentre = (name: string | null): FireCentre | undefined => {
      const fireCentresArray = Object.values(fireCentres)
      return fireCentresArray.find(centre => centre.name == name)
    }
    const storedFireCentre = findCentre(
      localStorage.getItem('hfiCalcPreferredFireCentre')
    )
    if (!isUndefined(storedFireCentre) && storedFireCentre !== selectedFireCentre) {
      dispatch(setSelectedFireCentre(storedFireCentre))
    }
  }

  useEffect(() => {
    dispatch(fetchHFIStations())
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (
      selectedFireCentre &&
      selectedFireCentre?.name !== localStorage.getItem('hfiCalcPreferredFireCentre')
    ) {
      localStorage.setItem('hfiCalcPreferredFireCentre', selectedFireCentre?.name)
    }
    if (!isUndefined(selectedFireCentre)) {
      dispatch(fetchLoadDefaultHFIResult(selectedFireCentre.id))
      dispatch(setSelectedPrepDate(''))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedFireCentre])

  useEffect(() => {
    if (Object.keys(fireCentres).length > 0) {
      setSelectedFireCentreFromLocalStorage()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fireCentres])

  const selectNewFireCentre = (newSelection: FireCentre | undefined) => {
    dispatch(setSelectedFireCentre(newSelection))
  }

  const handleSaveClicked = () => {
    if (!isUndefined(result)) {
      dispatch(
        fetchHFIResult({
          selected_station_code_ids: result.selected_station_code_ids,
          selected_fire_center_id: result.selected_fire_center_id,
          planning_area_fire_starts: constructPlanningAreaFireStarts(
            result.planning_area_hfi_results
          ),
          date_range: result.date_range,
          persist_request: true
        })
      )
    }
  }

  const handleDownloadClicked = () => {
    if (!isUndefined(result)) {
      dispatch(
        fetchPDFDownload({
          selected_station_code_ids: result.selected_station_code_ids,
          selected_fire_center_id: result.selected_fire_center_id,
          planning_area_fire_starts: constructPlanningAreaFireStarts(
            result.planning_area_hfi_results
          ),
          date_range: result.date_range
        })
      )
    }
  }

  const buildHFIContent = () => {
    if (isUndefined(selectedFireCentre) || isUndefined(dateRange)) {
      return (
        <Table>
          <TableBody>
            <EmptyFireCentreRow />
          </TableBody>
        </Table>
      )
    } else if (loading || stationDataLoading || isUndefined(result)) {
      return (
        <Container className={classes.container}>
          <CircularProgress />
        </Container>
      )
    }
    return (
      <React.Fragment>
        <Container maxWidth={'xl'}>
          {!isNull(fireCentresError) && (
            <HFIErrorAlert hfiDailiesError={null} fireCentresError={fireCentresError} />
          )}

          <FormControl className={classes.formControl}>
            <ViewSwitcherToggles
              dateRange={dateRange}
              selectedPrepDate={selectedPrepDate}
            />
          </FormControl>

          <FormControl className={classes.saveButton}>
            <DownloadPDFButton onClick={handleDownloadClicked} />
          </FormControl>

          <FormControl className={classes.saveButton}>
            <SaveButton saved={saved} onClick={handleSaveClicked} />
          </FormControl>

          <ErrorBoundary>
            <ViewSwitcher
              selectedFireCentre={selectedFireCentre}
              result={result}
              dateRange={dateRange}
              setSelected={setSelectedStation}
              setNewFireStarts={setNewFireStarts}
              selectedPrepDay={selectedPrepDate}
            />
          </ErrorBoundary>
        </Container>
      </React.Fragment>
    )
  }

  return (
    <main data-testid="hfi-calculator-page">
      <GeneralHeader
        padding="3em"
        spacing={0.985}
        title="HFI Calculator"
        productName="HFI Calculator"
      />
      <HFIPageSubHeader
        fireCentres={fireCentres}
        setDateRange={updatePrepDateRange}
        result={result}
        selectedFireCentre={selectedFireCentre}
        selectNewFireCentre={selectNewFireCentre}
        padding="1rem"
      />
      {buildHFIContent()}
    </main>
  )
}

export default React.memo(HfiCalculatorPage)
