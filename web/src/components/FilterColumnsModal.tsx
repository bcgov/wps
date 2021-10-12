import React, { useState } from 'react'
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  IconButton,
  Paper,
  Typography,
  makeStyles,
  Fab
} from '@material-ui/core'
import { CheckOutlined, Clear } from '@material-ui/icons'
import SelectionCell from 'features/fbaCalculator/components/SelectionCell'

export interface ColumnSelectionState {
  label: string
  selected: boolean
}

export interface ModalProps {
  testId?: string
  columns: string[]
  modalOpen: boolean
  setModalOpen: React.Dispatch<React.SetStateAction<boolean>>
  parentCallback: (selectedColumnsLabels: string[]) => void
}

const useStyles = makeStyles(() => ({
  modalWindow: {
    maxWidth: 'md'
  },
  closeIcon: {
    position: 'absolute',
    right: '0px'
  },
  modalTitle: {
    textAlign: 'center'
  }
}))

export const FilterColumnsModal = (props: ModalProps) => {
  const classes = useStyles()

  // set all columns as selected by default
  const [selected, setSelected] = useState<number[]>(
    Array.from(Array(props.columns.length).keys())
  )

  const translateSelectedFromNumbersToStrings = (): string[] => {
    const selectedColumnsAsStrings: string[] = []
    for (const index of selected) {
      selectedColumnsAsStrings.push(props.columns[index])
    }
    return selectedColumnsAsStrings
  }

  const handleClose = () => {
    props.setModalOpen(false)
  }

  const handleApplyAndClose = () => {
    const selectedColumnLabels = translateSelectedFromNumbersToStrings()
    props.parentCallback(selectedColumnLabels)
    props.setModalOpen(false)
  }

  return (
    <Dialog
      fullWidth
      className={classes.modalWindow}
      open={props.modalOpen}
      onClose={handleClose}
    >
      <Paper>
        <div>
          <Typography variant="h5" component="h5" className={classes.modalTitle}>
            Show Columns
            <IconButton className={classes.closeIcon} onClick={handleClose}>
              <Clear />
            </IconButton>
          </Typography>
        </div>
        <DialogContent>
          {props.columns.map((column, index) => {
            return (
              <div key={column}>
                <SelectionCell
                  selected={selected}
                  updateSelected={(newSelected: number[]) => setSelected(newSelected)}
                  disabled={false}
                  rowId={index}
                  testId={`filter-${column.replaceAll(' ', '-')}`}
                />
                <a>{column}</a>
              </div>
            )
          })}
          <Fab
            color="primary"
            aria-label="apply"
            onClick={handleApplyAndClose}
            variant="extended"
            data-testId="apply-btn"
          >
            Apply
          </Fab>
          <Fab
            color="secondary"
            aria-label="cancel"
            onClick={handleClose}
            variant="extended"
          >
            Cancel
          </Fab>
        </DialogContent>
      </Paper>
    </Dialog>
  )
}

export default React.memo(FilterColumnsModal)
