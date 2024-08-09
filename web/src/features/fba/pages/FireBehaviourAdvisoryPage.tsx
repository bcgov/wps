import { Box, FormControl, FormControlLabel, Grid, styled } from '@mui/material'
import { GeneralHeader, ErrorBoundary } from 'components'
import React, { useEffect, useState, useRef } from 'react'
import FBAMap from 'features/fba/components/map/FBAMap'
import FireCenterDropdown from 'components/FireCenterDropdown'
import { DateTime } from 'luxon'
import {
  selectFireZoneElevationInfo,
  selectFireCenters,
  selectHFIFuelTypes,
  selectRunDates,
  selectFireShapeAreas
} from 'app/rootReducer'
import { useDispatch, useSelector } from 'react-redux'
import { fetchFireCenters } from 'commonSlices/fireCentersSlice'
import { theme } from 'app/theme'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { getStations, StationSource } from 'api/stationAPI'
import { FireCenter, FireShape } from 'api/fbaAPI'
import { ASA_DOC_TITLE, FIRE_BEHAVIOUR_ADVISORY_NAME, PST_UTC_OFFSET } from 'utils/constants'
import WPSDatePicker from 'components/WPSDatePicker'
import { AppDispatch } from 'app/store'
import AdvisoryThresholdSlider from 'features/fba/components/map/AdvisoryThresholdSlider'
import AdvisoryMetadata from 'features/fba/components/AdvisoryMetadata'
import { fetchSFMSRunDates } from 'features/fba/slices/runDatesSlice'
import { isNull, isUndefined } from 'lodash'
import { fetchHighHFIFuels } from 'features/fba/slices/hfiFuelTypesSlice'
import { fetchFireShapeAreas } from 'features/fba/slices/fireZoneAreasSlice'
import { fetchfireZoneElevationInfo } from 'features/fba/slices/fireZoneElevationInfoSlice'
import { StyledFormControl } from 'components/StyledFormControl'
import { getMostRecentProcessedSnowByDate } from 'api/snow'
import InfoPanel from 'features/fba/components/infoPanel/InfoPanel'
import ProvincialSummary from 'features/fba/components/infoPanel/ProvincialSummary'
import FireZoneUnitSummary from 'features/fba/components/infoPanel/FireZoneUnitSummary'
import { fetchProvincialSummary } from 'features/fba/slices/provincialSummarySlice'
import AdvisoryReport from 'features/fba/components/infoPanel/AdvisoryReport'

export enum RunType {
  FORECAST = 'FORECAST',
  ACTUAL = 'ACTUAL'
}

export const FireCentreFormControl = styled(FormControl)({
  margin: theme.spacing(1),
  minWidth: 280
})

export const ForecastActualDropdownFormControl = styled(FormControl)({
  margin: theme.spacing(1),
  minWidth: 280
})

const FireBehaviourAdvisoryPage: React.FunctionComponent = () => {
  const dispatch: AppDispatch = useDispatch()
  const { fireCenters } = useSelector(selectFireCenters)
  const { hfiThresholdsFuelTypes } = useSelector(selectHFIFuelTypes)
  const { fireZoneElevationInfo } = useSelector(selectFireZoneElevationInfo)

  const [fireCenter, setFireCenter] = useState<FireCenter | undefined>(undefined)

  const [advisoryThreshold, setAdvisoryThreshold] = useState(20)
  const [selectedFireShape, setSelectedFireShape] = useState<FireShape | undefined>(undefined)
  const [dateOfInterest, setDateOfInterest] = useState(
    DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`).hour < 13
      ? DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`)
      : DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`).plus({ days: 1 })
  )
  const [runType, setRunType] = useState(RunType.FORECAST)
  const [showSummaryPanel, setShowSummaryPanel] = useState(true)
  const [snowDate, setSnowDate] = useState<DateTime | null>(null)
  const { mostRecentRunDate } = useSelector(selectRunDates)
  const { fireShapeAreas } = useSelector(selectFireShapeAreas)

  // Query our API for the most recently processed snow coverage date <= the currently selected date.
  const fetchLastProcessedSnow = async (selectedDate: DateTime) => {
    const data = await getMostRecentProcessedSnowByDate(selectedDate)
    if (isNull(data)) {
      setSnowDate(null)
    } else {
      const newSnowDate = data.forDate
      setSnowDate(newSnowDate)
    }
  }

  useEffect(() => {
    const findCenter = (id: string | null): FireCenter | undefined => {
      return fireCenters.find(center => center.id.toString() == id)
    }
    setFireCenter(findCenter(localStorage.getItem('preferredFireCenter')))
  }, [fireCenters])

  useEffect(() => {
    if (fireCenter?.id) {
      localStorage.setItem('preferredFireCenter', fireCenter?.id.toString())
    }
  }, [fireCenter])

  const updateDate = (newDate: DateTime) => {
    if (newDate !== dateOfInterest) {
      setDateOfInterest(newDate)
    }
  }

  useEffect(() => {
    const doiISODate = dateOfInterest.toISODate()
    if (!isNull(doiISODate)) {
      dispatch(fetchSFMSRunDates(runType, doiISODate))
    }
  }, [runType]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    dispatch(fetchFireCenters())
    const doiISODate = dateOfInterest.toISODate()
    if (!isNull(doiISODate)) {
      dispatch(fetchSFMSRunDates(runType, doiISODate))
    }
    dispatch(fetchWxStations(getStations, StationSource.wildfire_one))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const doiISODate = dateOfInterest.toISODate()
    if (!isNull(doiISODate)) {
      dispatch(fetchSFMSRunDates(runType, doiISODate))
    }
    fetchLastProcessedSnow(dateOfInterest)
  }, [dateOfInterest]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const doiISODate = dateOfInterest.toISODate()
    if (
      !isNull(mostRecentRunDate) &&
      !isNull(doiISODate) &&
      !isUndefined(mostRecentRunDate) &&
      !isUndefined(selectedFireShape)
    ) {
      dispatch(fetchHighHFIFuels(runType, doiISODate, mostRecentRunDate.toString(), selectedFireShape.fire_shape_id))
      dispatch(
        fetchfireZoneElevationInfo(selectedFireShape.fire_shape_id, runType, doiISODate, mostRecentRunDate.toString())
      )
    }
  }, [mostRecentRunDate, selectedFireShape]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const doiISODate = dateOfInterest.toISODate()
    if (!isNull(doiISODate)) {
      dispatch(fetchFireShapeAreas(runType, mostRecentRunDate, doiISODate))
      dispatch(fetchProvincialSummary(runType, mostRecentRunDate, doiISODate))
    }
  }, [mostRecentRunDate]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    document.title = ASA_DOC_TITLE
  }, [])

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <GeneralHeader
        isBeta={true}
        spacing={1}
        title={FIRE_BEHAVIOUR_ADVISORY_NAME}
        productName={FIRE_BEHAVIOUR_ADVISORY_NAME}
      />
      <Box sx={{ paddingTop: '0.5em' }}>
        <Grid container spacing={1}>
          <Grid item>
            <StyledFormControl>
              <WPSDatePicker date={dateOfInterest} updateDate={updateDate} />
            </StyledFormControl>
          </Grid>
          <Grid item>
            <FireCentreFormControl>
              <FireCenterDropdown
                fireCenterOptions={fireCenters}
                selectedFireCenter={fireCenter}
                setSelectedFireCenter={setFireCenter}
              />
            </FireCentreFormControl>
          </Grid>
          <ErrorBoundary>
            <Grid item>
              <ForecastActualDropdownFormControl>
                <AdvisoryMetadata runType={runType.toString()} setRunType={setRunType} />
              </ForecastActualDropdownFormControl>
            </Grid>
          </ErrorBoundary>
          <Grid item>
            <StyledFormControl>
              <FormControlLabel
                label="
                Percentage of combustible land threshold"
                labelPlacement="top"
                control={
                  <AdvisoryThresholdSlider
                    advisoryThreshold={advisoryThreshold}
                    setAdvisoryThreshold={setAdvisoryThreshold}
                  />
                }
              />
            </StyledFormControl>
          </Grid>
        </Grid>
      </Box>
      <Box sx={{ display: 'flex', flexGrow: 1, overflow: 'hidden' }}>
        <InfoPanel>
          <ProvincialSummary advisoryThreshold={advisoryThreshold} />
          <AdvisoryReport
            issueDate={mostRecentRunDate !== null ? DateTime.fromISO(mostRecentRunDate) : null}
            forDate={dateOfInterest}
            selectedFireZoneUnit={selectedFireShape}
            fireShapeAreas={fireShapeAreas}
            advisoryThreshold={advisoryThreshold}
          />
          <FireZoneUnitSummary
            fireShapeAreas={fireShapeAreas}
            fuelTypeInfo={hfiThresholdsFuelTypes}
            hfiElevationInfo={fireZoneElevationInfo}
            selectedFireZoneUnit={selectedFireShape}
          />
        </InfoPanel>
        <Grid sx={{ display: 'flex', flex: 1 }} item>
          <FBAMap
            forDate={dateOfInterest}
            runType={runType}
            selectedFireShape={selectedFireShape}
            selectedFireCenter={fireCenter}
            advisoryThreshold={advisoryThreshold}
            setSelectedFireShape={setSelectedFireShape}
            fireShapeAreas={fireShapeAreas}
            showSummaryPanel={showSummaryPanel}
            snowDate={snowDate}
            setShowSummaryPanel={setShowSummaryPanel}
          />
        </Grid>
      </Box>
    </Box>
  )
}

export default React.memo(FireBehaviourAdvisoryPage)
