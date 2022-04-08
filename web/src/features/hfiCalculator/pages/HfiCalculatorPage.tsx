import React, { useEffect } from 'react'
import { DateTime } from 'luxon'
import { Container, ErrorBoundary, GeneralHeader } from 'components'
import { fetchHFIStations } from 'features/hfiCalculator/slices/stationsSlice'
import {
  FireStartRange,
  setSelectedFireCentre,
  fetchLoadDefaultHFIResult,
  fetchSetNewFireStarts,
  fetchSetNewPrepDateRange,
  fetchSetStationSelected,
  fetchPDFDownload,
  setSelectedPrepDate
} from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { useDispatch, useSelector } from 'react-redux'
import {
  selectHFIStations,
  selectHFIStationsLoading,
  selectHFICalculatorState
} from 'app/rootReducer'
import { CircularProgress, FormControl, Table, TableBody } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import ViewSwitcher from 'features/hfiCalculator/components/ViewSwitcher'
import ViewSwitcherToggles from 'features/hfiCalculator/components/ViewSwitcherToggles'
import { formControlStyles, theme } from 'app/theme'
import { FireCentre } from 'api/hfiCalcAPI'
import { HFIPageSubHeader } from 'features/hfiCalculator/components/HFIPageSubHeader'
import { isNull, isUndefined } from 'lodash'
import HFIErrorAlert from 'features/hfiCalculator/components/HFIErrorAlert'
import DownloadPDFButton from 'features/hfiCalculator/components/DownloadPDFButton'
import EmptyFireCentreRow from 'features/hfiCalculator/components/EmptyFireCentre'
import { DateRange } from 'components/dateRangePicker/types'
import LiveChangesAlert from 'features/hfiCalculator/components/LiveChangesAlert'

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
  pdfButton: {
    margin: theme.spacing(1),
    float: 'right'
  }
}))

const HfiCalculatorPage: React.FunctionComponent = () => {
  const classes = useStyles()

  const dispatch = useDispatch()
  const { fireCentres, error: fireCentresError } = useSelector(selectHFIStations)
  const stationDataLoading = useSelector(selectHFIStationsLoading)
  const {
    selectedPrepDate,
    result,
    selectedFireCentre,
    loading,
    dateRange,
    error: hfiError
  } = useSelector(selectHFICalculatorState)

  const setSelectedStation = (
    planningAreaId: number,
    code: number,
    selected: boolean
  ) => {
    if (!isUndefined(result) && !isUndefined(result.date_range.start_date)) {
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
      !isUndefined(result) &&
      !isUndefined(newDateRange) &&
      !isUndefined(newDateRange.startDate) &&
      !isUndefined(newDateRange.endDate)
    ) {
      dispatch(
        fetchSetNewPrepDateRange(
          result.selected_fire_center_id,
          newDateRange.startDate,
          newDateRange.endDate
        )
      )
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

  const handleDownloadClicked = () => {
    if (!isUndefined(result)) {
      if (!isUndefined(result) && !isUndefined(result.date_range.start_date)) {
        dispatch(
          fetchPDFDownload(result.selected_fire_center_id, result.date_range.start_date)
        )
      }
    }
  }

  const buildErrorNotification = () => {
    if (!isNull(fireCentresError) || !isNull(hfiError)) {
      return (
        <HFIErrorAlert hfiDailiesError={hfiError} fireCentresError={fireCentresError} />
      )
    }
    return <React.Fragment></React.Fragment>
  }

  const isLoadingWithoutError = () => {
    return (
      (loading || stationDataLoading || isUndefined(result)) &&
      isNull(fireCentresError) &&
      isNull(hfiError)
    )
  }

  const buildHFIContent = () => {
    const errorNotification = buildErrorNotification()
    if (isUndefined(selectedFireCentre) || isUndefined(dateRange)) {
      return (
        <React.Fragment>
          {errorNotification}
          <Table>
            <TableBody>
              <EmptyFireCentreRow />
            </TableBody>
          </Table>
        </React.Fragment>
      )
    } else if (isLoadingWithoutError()) {
      return (
        <Container className={classes.container}>
          {errorNotification}
          <CircularProgress />
        </Container>
      )
    }
    return (
      <React.Fragment>
        <Container maxWidth={'xl'}>
          <LiveChangesAlert />
          {errorNotification}
          <FormControl className={classes.formControl}>
            <ViewSwitcherToggles
              dateRange={dateRange}
              selectedPrepDate={selectedPrepDate}
            />
          </FormControl>

          <FormControl className={classes.pdfButton}>
            <DownloadPDFButton onClick={handleDownloadClicked} />
          </FormControl>

          <ErrorBoundary>
            <ViewSwitcher
              selectedFireCentre={selectedFireCentre}
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
