import React from 'react'
import {
  Box,
  Dialog,
  DialogContent,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Paper,
  Typography
} from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { theme } from 'app/theme'
import ClearIcon from '@mui/icons-material/Clear'
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline'
import { Button } from '@mui/material'

export interface ColumnSelectionState {
  label: string
  selected: boolean
}

export interface ModalProps {
  testId?: string
  modalOpen: boolean
  setModalOpen: React.Dispatch<React.SetStateAction<boolean>>
}

const useStyles = makeStyles(() => ({
  modalWindow: {
    maxWidth: 'lg'
  },
  closeIcon: {
    position: 'absolute',
    right: '0px'
  },
  title: {
    textAlign: 'center'
  },
  addStation: {
    margin: theme.spacing(1),
    float: 'right'
  }
}))

export const ManageStationsModal = (props: ModalProps): JSX.Element => {
  const classes = useStyles()

  const handleClose = () => {
    props.setModalOpen(false)
  }

  return (
    <React.Fragment>
      <Dialog
        fullWidth
        className={classes.modalWindow}
        open={props.modalOpen}
        onClose={handleClose}
      >
        <Paper>
          <IconButton className={classes.closeIcon} onClick={handleClose}>
            <ClearIcon />
          </IconButton>

          <DialogContent>
            <Typography variant="h5" align="center">
              Manage Weather Stations
            </Typography>
            <Button
              variant="text"
              color="primary"
              className={classes.addStation}
              onClick={() => {
                /** no op */
              }}
              data-testid={'add-station-button'}
            >
              <AddCircleOutlineIcon />
              Add Station
            </Button>
            <Box sx={{ marginTop: 5 }}>
              <List dense>
                <Typography>Kamloops</Typography>

                <ListItem>
                  <ListItemText primary="Clearwater Hub" />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Wells Gray" />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Sparks Lake" />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Afton" />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Mayson" />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Blue River 2" />
                </ListItem>
              </List>
              <List dense>
                <Typography>Vernon</Typography>
                <ListItem>
                  <ListItemText primary="Turtle" />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Fintry" />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Station Bay 2" />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Seymour Arm" />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Salmon Arm" />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Kettle 2" />
                </ListItem>
              </List>
            </Box>
          </DialogContent>
        </Paper>
      </Dialog>
    </React.Fragment>
  )
}

export default React.memo(ManageStationsModal)
