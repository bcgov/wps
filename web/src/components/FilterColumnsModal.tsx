import React, { useState } from 'react'
import { styled } from '@mui/material/styles'
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogActions,
  IconButton,
  Paper,
  Fab,
  Checkbox,
  Button
} from '@mui/material'
import { Clear } from '@mui/icons-material'
import { ColumnLabel } from 'features/fbaCalculator/components/FBATable'

const PREFIX = 'FilterColumnsModal'

const ModalWindow = styled(Dialog, {
  name: `${PREFIX}-ModalWindow`
})({
  maxWidth: 'md'
})

const ModalCloseIcon = styled(IconButton, {
  name: `${PREFIX}-ModalCloseIcon`
})({
  position: 'absolute',
  right: '0px'
})

const SelectionBox = styled(Checkbox, {
  name: `${PREFIX}-SelectionBox`
})({
  height: '20px',
  boxSizing: 'border-box'
})

export interface ColumnSelectionState {
  label: string
  selected: boolean
}

export interface ModalProps {
  testId?: string
  columns: ColumnLabel[]
  modalOpen: boolean
  setModalOpen: React.Dispatch<React.SetStateAction<boolean>>
  parentCallback: (selectedColumnsLabels: ColumnLabel[]) => void
}

export const FilterColumnsModal = (props: ModalProps): JSX.Element => {
  // set all columns as selected by default
  const [selected, setSelected] = useState<Set<number>>(new Set(Array(props.columns.length).keys()))

  const handleClose = () => {
    props.setModalOpen(false)
  }

  const handleApplyAndClose = () => {
    const selectedColumnLabels = Array.from(selected)
      .sort((a, b) => a - b)
      .map(index => {
        return props.columns[index]
      })
    props.parentCallback(selectedColumnLabels)
    props.setModalOpen(false)
  }

  const toggleSelectedIndex = (index: number) => {
    if (!selected.has(index)) {
      // toggle index ON
      selected.add(index)
    } else if (selected.has(index)) {
      // toggle index OFF
      selected.delete(index)
    }
    setSelected(new Set(selected))
  }

  return (
    <div>
      <ModalWindow fullWidth open={props.modalOpen} onClose={handleClose}>
        <Paper>
          <DialogTitle>
            Show Columns
            <ModalCloseIcon onClick={handleClose} size="large">
              <Clear />
            </ModalCloseIcon>
          </DialogTitle>
          <DialogContent>
            {props.columns.map((column, index) => {
              return (
                <div key={column}>
                  <SelectionBox
                    checked={selected.has(index)}
                    color="primary"
                    onClick={() => {
                      toggleSelectedIndex(index)
                    }}
                    size="small"
                    data-testid={`filter-${column.replaceAll(' ', '-')}`}
                    // below is some jiggery-pokery to get checkboxes to squish closer together vertically
                    // https://stackoverflow.com/questions/64261614/how-to-decrease-vetical-distance-between-two-checkboxes-with-label
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
            >
              Apply
            </Fab>
            <Button aria-label="cancel" onClick={handleClose}>
              Cancel
            </Button>
          </DialogActions>
        </Paper>
      </ModalWindow>
    </div>
  )
}

export default React.memo(FilterColumnsModal)
