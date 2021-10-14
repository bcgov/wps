import React, { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogActions,
  IconButton,
  Paper,
  makeStyles,
  Fab,
  Checkbox
} from '@material-ui/core'
import { Clear } from '@material-ui/icons'

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
  floatingActionButton: {
    bottom: 40,
    left: 25,
    top: 'auto',
    right: 'auto',
    position: 'relative',
    margin: 0
  },
  selectionBox: {
    marginBottom: '3px',
    marginTop: '3px'
  }
}))

export const FilterColumnsModal = (props: ModalProps) => {
  const classes = useStyles()

  // set all columns as selected by default
  const [selected, setSelected] = useState<number[]>(
    Array.from(Array(props.columns.length).keys())
  )
  // having a set for selected as well as an array might seem like overkill, but because of the
  // inherent delays associated with useState for selected, this duplication is the only way to have the
  // checkboxes updated immediately once they're clicked
  const selectedSet = new Set(selected)

  const handleClose = () => {
    props.setModalOpen(false)
  }

  const handleApplyAndClose = () => {
    const selectedColumnLabels = selected.map(index => {
      return props.columns[index]
    })
    props.parentCallback(selectedColumnLabels)
    props.setModalOpen(false)
  }

  const toggleSelectedIndex = (index: number) => {
    if (!selectedSet.has(index)) {
      // toggle index ON
      selectedSet.add(index)
    } else if (selectedSet.has(index)) {
      // toggle index OFF
      selectedSet.delete(index)
    }
    setSelected(Array.from(selectedSet).sort((a, b) => a - b))
  }

  return (
    <Dialog
      fullWidth
      className={classes.modalWindow}
      open={props.modalOpen}
      onClose={handleClose}
    >
      <Paper>
        <DialogTitle>
          Show Columns
          <IconButton className={classes.closeIcon} onClick={handleClose}>
            <Clear />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          {props.columns.map((column, index) => {
            return (
              <div key={column}>
                <Checkbox
                  checked={selectedSet.has(index)}
                  onClick={() => {
                    toggleSelectedIndex(index)
                  }}
                  data-testid={`filter-${column.replaceAll(' ', '-')}`}
                  className={classes.selectionBox}
                />
                <a>{column}</a>
              </div>
            )
          })}
        </DialogContent>
        <DialogActions>
          <Fab
            color="primary"
            aria-label="apply"
            onClick={handleApplyAndClose}
            variant="extended"
            data-testId="apply-btn"
            className={classes.floatingActionButton}
          >
            Apply
          </Fab>
          <Fab
            color="secondary"
            aria-label="cancel"
            onClick={handleClose}
            variant="extended"
            className={classes.floatingActionButton}
          >
            Cancel
          </Fab>
        </DialogActions>
      </Paper>
    </Dialog>
  )
}

export default React.memo(FilterColumnsModal)
