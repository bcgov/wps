import { FormControl, styled } from '@mui/material'
import type { FireCentre, FireStartRange } from '@wps/api/hfiCalculatorAPI'
import { Container } from '@wps/ui/Container'
import type { DateRange } from '@wps/ui/dateRangePicker/types'
import { ErrorBoundary } from '@wps/ui/ErrorBoundary'
import { GeneralHeader } from '@wps/ui/GeneralHeader'
import { StyledFormControl } from '@wps/ui/StyledFormControl'
import { theme } from '@wps/ui/theme'
import { HFI_CALC_DOC_TITLE, HFI_CALC_NAME } from '@wps/utils/constants'
import {
  selectAuthentication,
  selectHFICalculatorState,
  selectHFIReadyState,
  selectHFIStations,
  selectHFIStationsLoading
} from 'app/rootReducer'
import type { AppDispatch } from 'app/store'
import { ROLES } from 'features/auth/roles'
import DownloadPDFButton from 'features/hfiCalculator/components/DownloadPDFButton'
import HFILoadingDataContainer from 'features/hfiCalculator/components/HFILoadingDataContainer'
import { HFIPageSubHeader } from 'features/hfiCalculator/components/HFIPageSubHeader'
import HFISuccessAlert from 'features/hfiCalculator/components/HFISuccessAlert'
import LastUpdatedHeader from 'features/hfiCalculator/components/LastUpdatedHeader'
import ManageStationsButton from 'features/hfiCalculator/components/stationAdmin/ManageStationsButton'
import ViewSwitcher from 'features/hfiCalculator/components/ViewSwitcher'
import ViewSwitcherToggles from 'features/hfiCalculator/components/ViewSwitcherToggles'
import {
  fetchFuelTypes,
  fetchGetPrepDateRange,
  fetchPDFDownload,
  fetchSetFuelType,
  fetchSetNewFireStarts,
  fetchSetStationSelected,
  setSelectedFireCentre,
  setSelectedPrepDate
} from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { fetchAllReadyStates, fetchToggleReadyState } from 'features/hfiCalculator/slices/hfiReadySlice'
import { fetchHFIStations } from 'features/hfiCalculator/slices/stationsSlice'
import { isNull, isUndefined } from 'lodash'
import { DateTime } from 'luxon'
import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'

export const HFIPageContainer = styled(Container)({
  display: 'flex',
  justifyContent: 'center',
  flexDirection: 'column',
  marginBottom: theme.spacing(3)
})

export const HFIFormControlContainer = styled(StyledFormControl)({
  display: 'flex',
  alignItems: 'center',
  flexDirection: 'row'
})

export const ActionButtonControlContainer = styled(FormControl)({
  marginLeft: 'auto',
  display: 'flex',
  alignItems: 'center',
  flexDirection: 'row'
})

const HfiCalculatorPage: React.FunctionComponent = () => {
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
      const prepDayDate = DateTime.fromISO(`${result.date_range.start_date}T00:00+00:00`, {
        setZone: true
      })
        .plus({ days: dayOffset })
        .toISODate()
      if (!isNull(prepDayDate)) {
        dispatch(
          fetchSetNewFireStarts(
            result.selected_fire_center_id,
            result.date_range.start_date,
            result.date_range.end_date,
            planningAreaId,
            prepDayDate,
            newFireStarts.id,
            { planning_area_id: planningAreaId }
          )
        )
      }
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
      return fireCentresArray.find(centre => centre.name === name)
    }
    const storedFireCentre = findCentre(localStorage.getItem('hfiCalcPreferredFireCentre'))
    if (!isUndefined(storedFireCentre) && storedFireCentre !== selectedFireCentre) {
      dispatch(setSelectedFireCentre(storedFireCentre))
    }
  }

  useEffect(() => {
    dispatch(fetchHFIStations())
    dispatch(fetchFuelTypes())
  }, [dispatch])

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
  }, [updatedPlanningAreaId, dispatch, planningAreaReadyDetails, result])

  useEffect(() => {
    if (selectedFireCentre && selectedFireCentre?.name !== localStorage.getItem('hfiCalcPreferredFireCentre')) {
      localStorage.setItem('hfiCalcPreferredFireCentre', selectedFireCentre?.name)
    }
    if (!isUndefined(selectedFireCentre)) {
      dispatch(setSelectedPrepDate('')) // do this so that the page automatically toggles
      // back to "Prep Period" tab instead of a specific date that may no longer be relevant
      dispatch(fetchGetPrepDateRange(selectedFireCentre.id))
    }
  }, [selectedFireCentre, dispatch])

  useEffect(() => {
    if (!isUndefined(selectedFireCentre) && !isUndefined(dateRange)) {
      dispatch(fetchAllReadyStates(selectedFireCentre.id, dateRange))
    }
  }, [dateRange, dispatch, selectedFireCentre])

  // biome-ignore lint/correctness/useExhaustiveDependencies: setSelectedFireCentreFromLocalStorage changes on every render
  useEffect(() => {
    if (Object.keys(fireCentres).length > 0) {
      setSelectedFireCentreFromLocalStorage()
    }
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
  }, [updatedPlanningAreaId, dispatch, selectedFireCentre, dateRange, planningAreaReadyDetails])

  // biome-ignore lint/correctness/useExhaustiveDependencies: selectedFireCentre/dateRange in deps creates a fetch loop; this effect is only meant to re-sync after a station admin update completes
  useEffect(() => {
    if (!stationsUpdateLoading && !isUndefined(selectedFireCentre) && !isUndefined(dateRange)) {
      dispatch(fetchHFIStations())
      dispatch(fetchAllReadyStates(selectedFireCentre.id, dateRange))
    }
  }, [stationsUpdateLoading, dispatch])

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
      <GeneralHeader isBeta={false} spacing={1} title={HFI_CALC_NAME} />
      <HFIPageSubHeader
        fireCentres={fireCentres}
        setDateRange={updatePrepDateRange}
        result={result}
        selectedFireCentre={selectedFireCentre}
        selectNewFireCentre={selectNewFireCentre}
        padding="1rem"
      />
      <HFIPageContainer maxWidth={false}>
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
          <HFISuccessAlert />
          <HFIFormControlContainer>
            <ViewSwitcherToggles dateRange={dateRange} selectedPrepDate={selectedPrepDate} />
            <LastUpdatedHeader
              dailies={result?.planning_area_hfi_results.flatMap(areaResult =>
                areaResult.daily_results.flatMap(dailyResult =>
                  dailyResult.dailies.map(validatedDaily => validatedDaily.daily)
                )
              )}
            />
            <ActionButtonControlContainer>
              {!isUndefined(result) && roles.includes(ROLES.HFI.STATION_ADMIN) && isAuthenticated && (
                <ManageStationsButton
                  planningAreas={
                    selectedFireCentre ? fireCentres.find(fc => fc.id === selectedFireCentre.id)?.planning_areas : []
                  }
                  planningAreaStationInfo={result.planning_area_station_info}
                />
              )}
              <DownloadPDFButton onClick={handleDownloadClicked} />
            </ActionButtonControlContainer>
          </HFIFormControlContainer>

          <ErrorBoundary>
            {isUndefined(result) ? null : (
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
        </HFILoadingDataContainer>
      </HFIPageContainer>
    </main>
  )
}

export default React.memo(HfiCalculatorPage)
