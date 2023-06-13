import React, { useEffect } from 'react'
import { DateTime } from 'luxon'
import { Container, ErrorBoundary, GeneralHeader } from 'components'
import { fetchHFIStations } from 'features/hfiCalculator/slices/stationsSlice'
import {
  FireStartRange,
  setSelectedFireCentre,
  fetchSetNewFireStarts,
  fetchGetPrepDateRange,
  fetchSetStationSelected,
  fetchFuelTypes,
  fetchPDFDownload,
  fetchSetFuelType,
  setSelectedPrepDate
} from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { fetchAllReadyStates, fetchToggleReadyState } from 'features/hfiCalculator/slices/hfiReadySlice'
import { useDispatch, useSelector } from 'react-redux'
import {
  selectHFIStations,
  selectHFIStationsLoading,
  selectHFICalculatorState,
  selectAuthentication,
  selectHFIReadyState
} from 'app/rootReducer'
import { FormControl } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import ViewSwitcher from 'features/hfiCalculator/components/ViewSwitcher'
import ViewSwitcherToggles from 'features/hfiCalculator/components/ViewSwitcherToggles'
import { formControlStyles } from 'app/theme'
import { FireCentre } from 'api/hfiCalculatorAPI'
import { HFIPageSubHeader } from 'features/hfiCalculator/components/HFIPageSubHeader'
import { isNull, isUndefined } from 'lodash'
import HFISuccessAlert from 'features/hfiCalculator/components/HFISuccessAlert'
import DownloadPDFButton from 'features/hfiCalculator/components/DownloadPDFButton'
import { DateRange } from 'components/dateRangePicker/types'
import { AppDispatch } from 'app/store'
import HFILoadingDataContainer from 'features/hfiCalculator/components/HFILoadingDataContainer'
import ManageStationsButton from 'features/hfiCalculator/components/stationAdmin/ManageStationsButton'
import { ROLES } from 'features/auth/roles'
import LastUpdatedHeader from 'features/hfiCalculator/components/LastUpdatedHeader'
import { HFI_CALC_DOC_TITLE, HFI_CALC_NAME } from 'utils/constants'

const useStyles = makeStyles(theme => ({
  ...formControlStyles,
  container: {
    display: 'flex',
    justifyContent: 'center',
    flexDirection: 'column',
    marginBottom: theme.spacing(3)
  },
  controlContainer: {
    display: 'flex',
    alignItems: 'center',
    flexDirection: 'row',
    margin: theme.spacing(1),
    minWidth: 210
  },
  actionButtonContainer: {
    marginLeft: 'auto',
    display: 'flex',
    alignItems: 'center',
    flexDirection: 'row'
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
    stationsUpdateLoading,
    dateRange,
    error: hfiError,
    fuelTypes,
    updatedPlanningAreaId
  } = useSelector(selectHFICalculatorState)
  const { planningAreaReadyDetails } = useSelector(selectHFIReadyState)

  const setSelectedStation = (planningAreaId: number, code: number, selected: boolean) => {
    if (!isUndefined(result) && !isUndefined(result.date_range.start_date)) {
      dispatch(
        fetchSetStationSelected(
          result.selected_fire_center_id,
          result.date_range.start_date,
          result.date_range.end_date,
          planningAreaId,
          code,
          selected,
          { planning_area_id: planningAreaId }
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
          fuel_type_id,
          { planning_area_id: planningAreaId }
        )
      )
    }
  }

  const setNewFireStarts = (planningAreaId: number, dayOffset: number, newFireStarts: FireStartRange) => {
    if (!isUndefined(result) && !isUndefined(result.date_range)) {
      dispatch(
        fetchSetNewFireStarts(
          result.selected_fire_center_id,
          result.date_range.start_date,
          result.date_range.end_date,
          planningAreaId,
          DateTime.fromISO(result.date_range.start_date + 'T00:00+00:00', {
            setZone: true
          })
            .plus({ days: dayOffset })
            .toISODate(),
          newFireStarts.id,
          { planning_area_id: planningAreaId }
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
          newDateRange.startDate.toISOString().split('T')[0],
          newDateRange.endDate.toISOString().split('T')[0]
        )
      )
    }
  }

  const setSelectedFireCentreFromLocalStorage = () => {
    const findCentre = (name: string | null): FireCentre | undefined => {
      const fireCentresArray = Object.values(fireCentres)
      return fireCentresArray.find(centre => centre.name == name)
    }
    const storedFireCentre = findCentre(localStorage.getItem('hfiCalcPreferredFireCentre'))
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
      !isUndefined(result) &&
      !isUndefined(result.date_range) &&
      !isNull(updatedPlanningAreaId) &&
      !isUndefined(planningAreaReadyDetails[updatedPlanningAreaId.planning_area_id]) &&
      planningAreaReadyDetails[updatedPlanningAreaId.planning_area_id].ready === true
    ) {
      dispatch(
        fetchToggleReadyState(result.selected_fire_center_id, updatedPlanningAreaId.planning_area_id, result.date_range)
      )
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [updatedPlanningAreaId])

  useEffect(() => {
    if (selectedFireCentre && selectedFireCentre?.name !== localStorage.getItem('hfiCalcPreferredFireCentre')) {
      localStorage.setItem('hfiCalcPreferredFireCentre', selectedFireCentre?.name)
    }
    if (!isUndefined(selectedFireCentre)) {
      dispatch(setSelectedPrepDate('')) // do this so that the page automatically toggles
      // back to "Prep Period" tab instead of a specific date that may no longer be relevant
      dispatch(fetchGetPrepDateRange(selectedFireCentre.id))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedFireCentre])

  useEffect(() => {
    if (!isUndefined(selectedFireCentre) && !isUndefined(dateRange)) {
      dispatch(fetchAllReadyStates(selectedFireCentre.id, dateRange))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dateRange])

  useEffect(() => {
    if (Object.keys(fireCentres).length > 0) {
      setSelectedFireCentreFromLocalStorage()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fireCentres])

  useEffect(() => {
    if (
      !isNull(updatedPlanningAreaId) &&
      isUndefined(planningAreaReadyDetails[updatedPlanningAreaId.planning_area_id]) &&
      !isUndefined(selectedFireCentre) &&
      !isUndefined(dateRange)
    ) {
      // Request all ready states for hfi request unique by date and fire centre
      dispatch(fetchAllReadyStates(selectedFireCentre.id, dateRange))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [updatedPlanningAreaId])

  useEffect(() => {
    if (!stationsUpdateLoading && !isUndefined(selectedFireCentre) && !isUndefined(dateRange)) {
      dispatch(fetchHFIStations())
      dispatch(fetchAllReadyStates(selectedFireCentre.id, dateRange))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stationsUpdateLoading])

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
          fetchPDFDownload(result.selected_fire_center_id, result.date_range.start_date, result.date_range.end_date)
        )
      }
    }
  }

  useEffect(() => {
    document.title = HFI_CALC_DOC_TITLE
  }, [])

  return (
    <main data-testid="hfi-calculator-page">
      <GeneralHeader isBeta={false} spacing={1} title={HFI_CALC_NAME} productName={HFI_CALC_NAME} />
      <HFIPageSubHeader
        fireCentres={fireCentres}
        setDateRange={updatePrepDateRange}
        result={result}
        selectedFireCentre={selectedFireCentre}
        selectNewFireCentre={selectNewFireCentre}
        padding="1rem"
      />
      <Container maxWidth={false} className={classes.container}>
        <HFILoadingDataContainer
          pdfLoading={pdfLoading}
          fuelTypesLoading={fuelTypesLoading}
          stationDataLoading={stationDataLoading}
          fireCentresLoading={fireCentresLoading}
          stationsUpdateLoading={stationsUpdateLoading}
          fireCentresError={fireCentresError}
          hfiError={hfiError}
          selectedFireCentre={selectedFireCentre}
          dateRange={dateRange}
        >
          <React.Fragment>
            <HFISuccessAlert />
            <FormControl className={classes.controlContainer}>
              <ViewSwitcherToggles dateRange={dateRange} selectedPrepDate={selectedPrepDate} />
              <LastUpdatedHeader
                dailies={result?.planning_area_hfi_results.flatMap(areaResult =>
                  areaResult.daily_results.flatMap(dailyResult =>
                    dailyResult.dailies.map(validatedDaily => validatedDaily.daily)
                  )
                )}
              />
              <FormControl className={classes.actionButtonContainer}>
                {!isUndefined(result) && roles.includes(ROLES.HFI.STATION_ADMIN) && isAuthenticated && (
                  <ManageStationsButton
                    planningAreas={
                      selectedFireCentre ? fireCentres.find(fc => fc.id === selectedFireCentre.id)?.planning_areas : []
                    }
                    planningAreaStationInfo={result.planning_area_station_info}
                  />
                )}
                <DownloadPDFButton onClick={handleDownloadClicked} />
              </FormControl>
            </FormControl>

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
        </HFILoadingDataContainer>
      </Container>
    </main>
  )
}

export default React.memo(HfiCalculatorPage)
