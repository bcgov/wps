import React, { useEffect } from 'react'
import { DateTime } from 'luxon'
import { Container, ErrorBoundary, GeneralHeader } from 'components'
import { fetchHFIStations } from 'features/hfiCalculator/slices/stationsSlice'
import {
  FireStartRange,
  setSelectedFireCentre,
  fetchLoadDefaultHFIResult,
  fetchSetNewFireStarts,
  fetchGetPrepDateRange,
  fetchSetStationSelected,
  fetchFuelTypes,
  fetchPDFDownload,
  setSelectedPrepDate,
  fetchSetFuelType
} from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { useDispatch, useSelector } from 'react-redux'
import {
  selectHFIStations,
  selectHFIStationsLoading,
  selectHFICalculatorState,
  selectAuthentication
} from 'app/rootReducer'
import { FormControl } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import ViewSwitcher from 'features/hfiCalculator/components/ViewSwitcher'
import ViewSwitcherToggles from 'features/hfiCalculator/components/ViewSwitcherToggles'
import { formControlStyles } from 'app/theme'
import { FireCentre } from 'api/hfiCalculatorAPI'
import { HFIPageSubHeader } from 'features/hfiCalculator/components/HFIPageSubHeader'
import { isUndefined } from 'lodash'
import HFISuccessAlert from 'features/hfiCalculator/components/HFISuccessAlert'
import DownloadPDFButton from 'features/hfiCalculator/components/DownloadPDFButton'
import { DateRange } from 'components/dateRangePicker/types'
import LiveChangesAlert from 'features/hfiCalculator/components/LiveChangesAlert'
import { AppDispatch } from 'app/store'
import HFILoadingDataView from 'features/hfiCalculator/components/HFILoadingDataView'
import AddStationButton from 'features/hfiCalculator/components/stationAdmin/AddStationButton'
import { ROLES } from 'features/auth/roles'

const useStyles = makeStyles(theme => ({
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
  actionButton: {
    margin: theme.spacing(1),
    float: 'right'
  }
}))

const HfiCalculatorPage: React.FunctionComponent = () => {
  const classes = useStyles()

  const dispatch: AppDispatch = useDispatch()
  const { roles, isAuthenticated } = useSelector(selectAuthentication)
  const { fireCentres, error: fireCentresError } = useSelector(selectHFIStations)
  const stationDataLoading = useSelector(selectHFIStationsLoading)
  const {
    selectedPrepDate,
    result,
    selectedFireCentre,
    pdfLoading,
    fuelTypesLoading,
    fireCentresLoading,
    dateRange,
    error: hfiError,
    changeSaved,
    fuelTypes
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
          result.date_range.end_date,
          planningAreaId,
          code,
          selected
        )
      )
    }
  }

  const setFuelType = (planningAreaId: number, code: number, fuel_type_id: number) => {
    if (!isUndefined(result) && !isUndefined(result.date_range.start_date)) {
      dispatch(
        fetchSetFuelType(
          result.selected_fire_center_id,
          result.date_range.start_date,
          result.date_range.end_date,
          planningAreaId,
          code,
          fuel_type_id
        )
      )
    }
  }

  const setNewFireStarts = (
    areaId: number,
    dayOffset: number,
    newFireStarts: FireStartRange
  ) => {
    if (!isUndefined(result) && !isUndefined(result.date_range)) {
      dispatch(
        fetchSetNewFireStarts(
          result.selected_fire_center_id,
          result.date_range.start_date,
          result.date_range.end_date,
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
        fetchGetPrepDateRange(
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
    dispatch(fetchFuelTypes())
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
      if (
        !isUndefined(result) &&
        !isUndefined(result.date_range.start_date) &&
        !isUndefined(result.date_range.end_date)
      ) {
        dispatch(
          fetchPDFDownload(
            result.selected_fire_center_id,
            result.date_range.start_date,
            result.date_range.end_date
          )
        )
      }
    }
  }

  const buildSuccessNotification = () => {
    if (changeSaved) {
      return <HFISuccessAlert message="Changes saved!" />
    }
    return <React.Fragment></React.Fragment>
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
      <Container maxWidth={'xl'}>
        <HFILoadingDataView
          pdfLoading={pdfLoading}
          fuelTypesLoading={fuelTypesLoading}
          stationDataLoading={stationDataLoading}
          fireCentresLoading={fireCentresLoading}
          fireCentresError={fireCentresError}
          hfiError={hfiError}
          selectedFireCentre={selectedFireCentre}
          dateRange={dateRange}
        >
          <React.Fragment>
            <LiveChangesAlert />
            {buildSuccessNotification()}
            <FormControl className={classes.formControl}>
              <ViewSwitcherToggles
                dateRange={dateRange}
                selectedPrepDate={selectedPrepDate}
              />
            </FormControl>

            <FormControl className={classes.actionButton}>
              <DownloadPDFButton onClick={handleDownloadClicked} />
            </FormControl>

            {roles.includes(ROLES.HFI.STATION_ADMIN) && isAuthenticated && (
              <FormControl className={classes.actionButton}>
                <AddStationButton />
              </FormControl>
            )}

            <ErrorBoundary>
              {isUndefined(result) ? (
                <React.Fragment></React.Fragment>
              ) : (
                <ViewSwitcher
                  selectedFireCentre={selectedFireCentre}
                  dateRange={dateRange}
                  setSelected={setSelectedStation}
                  setNewFireStarts={setNewFireStarts}
                  setFuelType={setFuelType}
                  selectedPrepDay={selectedPrepDate}
                  fuelTypes={fuelTypes}
                  planningAreaStationInfo={result.planning_area_station_info}
                />
              )}
            </ErrorBoundary>
          </React.Fragment>
        </HFILoadingDataView>
      </Container>
    </main>
  )
}

export default React.memo(HfiCalculatorPage)
