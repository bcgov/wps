import { getMostRecentProcessedSnowByDate } from '@/api/snow'
import { AppDispatch } from '@/app/store'
import { theme } from '@/app/theme'
import { GeneralHeader } from '@/components/GeneralHeader'
import { StyledFormControl } from '@/components/StyledFormControl'
import ASADatePicker from '@/features/fba/components/ASADatePicker'
import { fetchSFMSBounds, selectEarliestSFMSBounds, selectLatestSFMSBounds } from '@/features/fba/slices/runDatesSlice'
import Footer from '@/features/landingPage/components/Footer'
import { RasterType } from '@/features/sfmsInsights/components/map/rasterConfig'
import SFMSMap from '@/features/sfmsInsights/components/map/SFMSMap'
import RasterTypeDropdown from '@/features/sfmsInsights/components/RasterTypeDropdown'
import { SFMS_INSIGHTS_NAME } from '@/utils/constants'
import { getDateTimeNowPST } from '@/utils/date'
import WarningAmberIcon from '@mui/icons-material/WarningAmber'
import {
  Box,
  Button,
  Checkbox,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  Grid,
  IconButton
} from '@mui/material'
import { isNil, isNull } from 'lodash'
import { DateTime } from 'luxon'
import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'

const SFMS_INSIGHTS_ALWAYS_HIDE_KEY = 'SFMSInsightsAlwaysHideSnowMessage'
const TEMP_LAST_SNOW = DateTime.fromISO('2026-02-12')
export const SFMSInsightsPage = () => {
  const dispatch = useDispatch<AppDispatch>()
  const latestBounds = useSelector(selectLatestSFMSBounds)
  const earliestBounds = useSelector(selectEarliestSFMSBounds)
  const sfmsBounds = useSelector((state: any) => state.runDates.sfmsBounds)
  const sfmsBoundsLoading = useSelector((state: any) => state.runDates.sfmsBoundsLoading)
  const [snowDate, setSnowDate] = useState<DateTime | null>(null)
  const [rasterDate, setRasterDate] = useState<DateTime | null>(getDateTimeNowPST())
  const [maxDate] = useState<DateTime>(getDateTimeNowPST().plus({ days: 10 }))
  const [minDate, setMinDate] = useState<DateTime>(
    DateTime.fromObject({ day: 1, month: 1, year: getDateTimeNowPST().year })
  )

  const [rasterType, setRasterType] = useState<RasterType>('fuel')
  const [showSnow, setShowSnow] = useState<boolean>(true)
  const [showSnowDialog, setShowSnowDialog] = useState<boolean>(false)
  const [showSnowWarningIcon, setShowSnowWarningIcon] = useState<boolean>(false)
  const [alwaysHide, setAlwaysHide] = useState<boolean>(() => {
    const stored = localStorage.getItem(SFMS_INSIGHTS_ALWAYS_HIDE_KEY)
    return stored === 'true'
  })

  useEffect(() => {
    // Only fetch SFMS bounds if we haven't fetched yet (undefined) and aren't already loading
    if (sfmsBounds === undefined && !sfmsBoundsLoading) {
      dispatch(fetchSFMSBounds())
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    // Display warning about stale snow data if user hasn't chosen to always hide the dialog
    if (showSnow && !alwaysHide) {
      setShowSnowDialog(true)
    }
  }, [alwaysHide, showSnow])

  useEffect(() => {
    if (
      !isNil(snowDate?.ordinal) &&
      snowDate?.ordinal === TEMP_LAST_SNOW.ordinal &&
      !isNil(rasterDate?.ordinal) &&
      rasterDate?.ordinal > TEMP_LAST_SNOW.ordinal
    ) {
      setShowSnowWarningIcon(true)
    } else {
      setShowSnowWarningIcon(false)
    }
  }, [rasterDate, snowDate])

  useEffect(() => {
    if (earliestBounds?.minimum) {
      setMinDate(DateTime.fromISO(earliestBounds.minimum))
    }
  }, [earliestBounds])

  useEffect(() => {
    // Only fetch snow data once rasterDate is set
    if (!rasterDate) {
      return
    }

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

    fetchLastProcessedSnow(rasterDate)
  }, [rasterDate])

  const handleAlwaysHide = () => {
    localStorage.setItem(SFMS_INSIGHTS_ALWAYS_HIDE_KEY, `${!alwaysHide}`)
    setAlwaysHide(!alwaysHide)
  }

  const renderSnowWarningIcon = () => {
    if (showSnowWarningIcon) {
      return (
        <IconButton onClick={() => setShowSnowDialog(true)} sx={{ pl: 0, pt: 0 }}>
          <WarningAmberIcon fontSize="large" sx={{ color: theme.palette.warning.main, pt: theme.spacing() }} />
        </IconButton>
      )
    }
  }

  const renderSnowWarningDialog = () => {
    if (showSnow && showSnowDialog) {
      return (
        <Dialog maxWidth="sm" open={showSnowDialog} sx={{ zIndex: 2000 }}>
          <DialogTitle>Snow Coverage Imagery Warning</DialogTitle>
          <DialogContent dividers>
            The VIIRS satellite sensor that supplies snow coverage imagery experienced an anomaly on March 9, 2026 and
            updated imagery is currently unavailable.
          </DialogContent>
          <DialogActions>
            <FormControlLabel
              control={
                <Checkbox
                  checked={alwaysHide}
                  onChange={handleAlwaysHide}
                  size="small"
                  style={{ color: theme.palette.warning.contrastText }}
                />
              }
              label="Don't show again"
              style={{ fontSize: '0.8rem', color: theme.palette.warning.contrastText }}
            />
            <Button variant="contained" title="Dismiss" onClick={() => setShowSnowDialog(false)}>
              Dismiss
            </Button>
          </DialogActions>
        </Dialog>
      )
    }
  }

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <GeneralHeader isBeta={true} spacing={1} title={SFMS_INSIGHTS_NAME} />
      <Box
        sx={{
          paddingTop: '0.5em',
          borderBottomWidth: 2,
          borderBottomStyle: 'solid',
          borderBottomColor: 'secondary.main'
        }}
      >
        <Grid container spacing={1} alignItems={'center'}>
          {sfmsBoundsLoading ? (
            <Grid item>
              <StyledFormControl>
                <Box sx={{ display: 'flex', alignItems: 'center', padding: 2 }}>
                  <CircularProgress size={24} />
                </Box>
              </StyledFormControl>
            </Grid>
          ) : (
            <Grid item>
              <StyledFormControl>
                <ASADatePicker
                  date={rasterDate}
                  updateDate={setRasterDate}
                  historicalMinDate={minDate}
                  historicalMaxDate={maxDate}
                  currentYearMinDate={minDate}
                  currentYearMaxDate={maxDate}
                />
              </StyledFormControl>
            </Grid>
          )}
          <Grid item>
            <StyledFormControl>
              <RasterTypeDropdown
                selectedRasterType={rasterType}
                setSelectedRasterType={setRasterType}
                rasterDataAvailable={!!latestBounds?.maximum}
              />
            </StyledFormControl>
          </Grid>
          <Grid item>
            <FormControlLabel
              control={<Checkbox checked={showSnow} onChange={e => setShowSnow(e.target.checked)} />}
              label={snowDate ? `Show Latest Snow: ${snowDate.toLocaleString(DateTime.DATE_MED)}` : 'Show Latest Snow'}
            />
            {renderSnowWarningIcon()}
          </Grid>
        </Grid>
      </Box>
      <Box sx={{ flex: 1, position: 'relative' }}>
        <SFMSMap snowDate={snowDate} rasterDate={rasterDate} rasterType={rasterType} showSnow={showSnow} />
      </Box>
      {renderSnowWarningDialog()}
      <Footer />
    </Box>
  )
}
