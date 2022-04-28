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
import AddStationButton from 'features/hfiCalculator/components/stationAdmin/AddStationButton'
import StationList from 'features/hfiCalculator/components/stationAdmin/StationsList'
import HFISuccessAlert from 'features/hfiCalculator/components/HFISuccessAlert'
import { useDispatch, useSelector } from 'react-redux'
import { selectHFICalculatorState } from 'app/rootReducer'
import { setChangeSaved } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { AppDispatch } from 'app/store'
import { isEmpty, isUndefined, some } from 'lodash'

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

export const someEmptyStations = (newStations: AdminStation[]) =>
  some(
    newStations,
    newStation =>
      (isUndefined(newStation.planningArea) ||
        isUndefined(newStation.station) ||
        isUndefined(newStation.fuelType)) &&
      newStation.dirty
  )

export const ManageStationsModal = (props: ModalProps): JSX.Element => {
  const classes = useStyles()

  const dispatch: AppDispatch = useDispatch()

  const { changeSaved } = useSelector(selectHFICalculatorState)

  const [newStations, setNewStations] = useState<AdminStation[]>([{ dirty: false }])

  const handleClose = () => {
    props.setModalOpen(false)
    setNewStations([])
  }

  const handleSave = () => {
    // TODO: temporary, this will be dispatched by POST request with new stations
    dispatch(setChangeSaved(true))
  }

  const handleAddStation = () => {
    console.log(newStations)
    setNewStations([...newStations, { dirty: false }])
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
        maxWidth="lg"
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
            <AddStationButton clickHandler={handleAddStation} />
            <StationList
              newStations={newStations}
              someStationsEmpty={someEmptyStations(newStations)}
            />
          </DialogContent>
          <Button
            variant="contained"
            color="primary"
            disabled={isEmpty(newStations) || someEmptyStations(newStations)}
            className={classes.actionButton}
            onClick={handleSave}
            data-testid={'cancel-hfi-admin-button'}
          >
            Save
          </Button>
          <Button
            variant="outlined"
            color="primary"
            className={classes.actionButton}
            onClick={handleClose}
            data-testid={'cancel-hfi-admin-button'}
          >
            Cancel
          </Button>
        </Paper>
      </Dialog>
    </React.Fragment>
  )
}

export default React.memo(ManageStationsModal)
