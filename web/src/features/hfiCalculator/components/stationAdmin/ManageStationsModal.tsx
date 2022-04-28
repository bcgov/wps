import React, { useState } from 'react'
import {
  Dialog,
  DialogContent,
  IconButton,
  Paper,
  Typography,
  Button
} from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { theme } from 'app/theme'
import ClearIcon from '@mui/icons-material/Clear'
import NewStationForm from 'features/hfiCalculator/components/stationAdmin/NewStationForm'
import HFISuccessAlert from 'features/hfiCalculator/components/HFISuccessAlert'
import { useDispatch, useSelector } from 'react-redux'
import { selectHFICalculatorState } from 'app/rootReducer'
import { setChangeSaved } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { AppDispatch } from 'app/store'
import { isEmpty, values } from 'lodash'
import SaveNewStationButton from 'features/hfiCalculator/components/stationAdmin/SaveNewStationButton'

export interface AdminStation {
  dirty: boolean
  planningArea?: {
    id: number
    name: string
  }
  station?: {
    code: number
    name: string
  }
  fuelType?: {
    id: number
    name: string
  }
}
export interface ModalProps {
  testId?: string
  modalOpen: boolean
  setModalOpen: React.Dispatch<React.SetStateAction<boolean>>
}

const useStyles = makeStyles(() => ({
  modalWindow: {
    maxWidth: 'xl'
  },
  closeIcon: {
    position: 'absolute',
    right: '0px'
  },
  title: {
    textAlign: 'center'
  },
  actionButton: {
    minWidth: 100,
    margin: theme.spacing(1),
    float: 'right'
  }
}))

const invalidNewStation = (newStation: AdminStation) =>
  values(newStation).some(isEmpty) && newStation.dirty

export const ManageStationsModal = (props: ModalProps): JSX.Element => {
  const classes = useStyles()

  const dispatch: AppDispatch = useDispatch()

  const { changeSaved } = useSelector(selectHFICalculatorState)

  const newEmptyStation = { dirty: false }
  const [newStation, setNewStations] = useState<AdminStation>(newEmptyStation)

  const handleClose = () => {
    props.setModalOpen(false)
    setNewStations(newEmptyStation)
  }

  const handleSave = () => {
    // TODO: temporary, this will be dispatched by POST request with new stations
    dispatch(setChangeSaved(true))
  }

  const buildSuccessNotification = () => {
    if (changeSaved) {
      return <HFISuccessAlert message="Changes saved!" />
    }
    return <React.Fragment></React.Fragment>
  }

  return (
    <React.Fragment>
      {buildSuccessNotification()}

      <Dialog
        fullWidth
        maxWidth="md"
        open={props.modalOpen}
        onClose={handleClose}
        data-testid="manage-stations-modal"
      >
        <Paper>
          <IconButton className={classes.closeIcon} onClick={handleClose}>
            <ClearIcon />
          </IconButton>

          <DialogContent>
            <Typography variant="h5" align="center">
              Add New Weather Station
            </Typography>
            <Typography variant="body1" align="center">
              New weather station(s) will be included in the default list moving forward
            </Typography>
            <NewStationForm
              newStation={newStation}
              invalid={invalidNewStation(newStation)}
            />
          </DialogContent>
          <SaveNewStationButton
            newStation={newStation}
            invalidNewStation={invalidNewStation(newStation)}
            handleSave={handleSave}
          />
          <Button
            variant="outlined"
            color="primary"
            className={classes.actionButton}
            onClick={handleClose}
            data-testid={'cancel-new-station-button'}
          >
            Cancel
          </Button>
        </Paper>
      </Dialog>
    </React.Fragment>
  )
}

export default React.memo(ManageStationsModal)
