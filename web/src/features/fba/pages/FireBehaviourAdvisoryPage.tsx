import {
  Dialog,
  FormControl,
  Grid,
  DialogContent,
  DialogTitle,
  DialogActions,
  IconButton,
  Paper,
  Fab,
  Button
} from '@mui/material'
import { Clear } from '@mui/icons-material'
import makeStyles from '@mui/styles/makeStyles'
import { GeneralHeader, Container } from 'components'
import React, { useEffect, useState } from 'react'
import FBAMap from 'features/fba/components/FBAMap'
import FireCenterDropdown from 'features/fbaCalculator/components/FireCenterDropdown'
import FormalFBATable from 'features/fba/components/FormalFBATable'
import { DateTime } from 'luxon'
import { selectFireCenters } from 'app/rootReducer'
import { useDispatch, useSelector } from 'react-redux'
import ReactPDF from '@react-pdf/renderer'
import { fetchFireCenters } from 'features/fbaCalculator/slices/fireCentersSlice'
import { formControlStyles, theme } from 'app/theme'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { getStations, StationSource } from 'api/stationAPI'
import { FireCenter } from 'api/fbaAPI'
import { PST_UTC_OFFSET } from 'utils/constants'
import WPSDatePicker from 'components/WPSDatePicker'
import { AppDispatch } from 'app/store'
import AdvisoryPDF from 'features/fba/components/AdvisoryPDF'

const useStyles = makeStyles(() => ({
  ...formControlStyles,
  listContainer: {
    width: 700,
    height: 700
  },
  mapContainer: {
    width: 900,
    height: 700
  },
  fireCenter: {
    minWidth: 280,
    margin: theme.spacing(1)
  },
  instructions: {
    textAlign: 'left'
  },
  closeIcon: {
    position: 'absolute',
    right: '0px'
  }
}))

export const FireBehaviourAdvisoryPage: React.FunctionComponent = () => {
  const classes = useStyles()
  const dispatch: AppDispatch = useDispatch()
  const { fireCenters } = useSelector(selectFireCenters)
  const [modalOpen, setModalOpen] = useState<boolean>(false)

  const emptyInstructions = (
    <div data-testid={'fba-instructions'} className={classes.instructions}>
      <p>Select a fire center to get started.</p>
      <p>A selected fire center will populate this pane with its station details.</p>
    </div>
  )

  const [fireCenter, setFireCenter] = useState<FireCenter | undefined>(undefined)

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

  const [dateOfInterest, setDateOfInterest] = useState(
    DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`)
  )

  const updateDate = (newDate: DateTime) => {
    if (newDate !== dateOfInterest) {
      setDateOfInterest(newDate)
    }
  }

  useEffect(() => {
    dispatch(fetchFireCenters())
    dispatch(fetchWxStations(getStations, StationSource.wildfire_one))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const openPDFPreviewModal = () => {
    setModalOpen(true)
  }

  const handleClose = () => {
    setModalOpen(false)
  }

  const handleSave = () => {
    console.log('Saving PDF...')
    // return ReactPDF.render(<AdvisoryPDF />, `${__dirname}/example.pdf`)
    ReactPDF.renderToFile(<AdvisoryPDF />, `${__dirname}/example.pdf`)
  }

  return (
    <React.Fragment>
      <GeneralHeader
        spacing={1}
        title="Predictive Services Unit"
        productName="Predictive Services Unit"
      />
      <Dialog open={modalOpen}>
        <Paper>
          <DialogTitle>
            Preview PDF
            <IconButton className={classes.closeIcon} onClick={handleClose} size="large">
              <Clear />
            </IconButton>
          </DialogTitle>
          <DialogContent>
            <AdvisoryPDF />
          </DialogContent>
          <DialogActions>
            <Fab
              color="primary"
              aria-label="apply"
              onClick={handleSave}
              variant="extended"
              data-testId="apply-btn"
            >
              Save
            </Fab>
            <Button aria-label="cancel" onClick={handleClose}>
              Cancel
            </Button>
          </DialogActions>
        </Paper>
      </Dialog>
      <Container maxWidth={'xl'}>
        <h1>
          {/* (🔥🦇) */}
          Fire Behaviour Advisory Tool
        </h1>
        <Grid container direction={'row'}>
          <Grid container spacing={2}>
            <Grid item>
              <FormControl className={classes.formControl}>
                <WPSDatePicker date={dateOfInterest} updateDate={updateDate} />
              </FormControl>
            </Grid>
            <Grid item xs={2}>
              <FormControl className={classes.fireCenter}>
                <FireCenterDropdown
                  fireCenterOptions={fireCenters}
                  selectedFireCenter={fireCenter}
                  setSelectedFireCenter={setFireCenter}
                />
              </FormControl>
            </Grid>
          </Grid>
          <Grid container spacing={2}>
            <Grid item xs>
              {fireCenter ? (
                <FormalFBATable
                  fireCenter={fireCenter}
                  className={classes.listContainer}
                />
              ) : (
                emptyInstructions
              )}
            </Grid>
            <Grid item xs>
              <FBAMap selectedFireCenter={fireCenter} className={classes.mapContainer} />
            </Grid>
          </Grid>
        </Grid>
        <Button onClick={openPDFPreviewModal}>Export to PDF</Button>
      </Container>
    </React.Fragment>
  )
}

export default React.memo(FireBehaviourAdvisoryPage)
