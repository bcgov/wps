import React from 'react'
import { styled } from '@mui/material/styles'
import { Dialog, DialogContent, DialogTitle, IconButton, Paper } from '@mui/material'
import { Clear } from '@mui/icons-material'

const PREFIX = 'AboutDataModal'

const ModalWindow = styled(Dialog, {
  name: `${PREFIX}-modalWindow`
})({
  maxWidth: 'md'
})

const CloseIconButton = styled(IconButton, {
  name: `${PREFIX}-closeIconButton`
})({
  position: 'absolute',
  right: '0px'
})

export interface ColumnSelectionState {
  label: string
  selected: boolean
}

export interface ModalProps {
  testId?: string
  modalOpen: boolean
  setModalOpen: React.Dispatch<React.SetStateAction<boolean>>
}

export const AboutDataModal = (props: ModalProps): JSX.Element => {
  const handleClose = () => {
    props.setModalOpen(false)
  }

  return (
    <div>
      <ModalWindow fullWidth open={props.modalOpen} onClose={handleClose}>
        <Paper>
          <DialogTitle>
            <CloseIconButton onClick={handleClose} size="large">
              <Clear />
            </CloseIconButton>
          </DialogTitle>
          <DialogContent>
            <h1>About This Data</h1>
            <p>Forecasted weather outputs are for 13:00 and FWI Indices are for 17:00 PDT.</p>
            <p>These fire behaviour calculations assume flat terrain.</p>
            <br />
            <p>Weather and fire behaviour indices are sourced from the Wildfire One API.</p>
            <br />
            <p>
              Values are calculated using the{' '}
              <a target="_blank" rel="noopener noreferrer" href="https://r-forge.r-project.org/projects/cffdrs/">
                Canadian Forest Fire Danger Rating System R Library
              </a>{' '}
              and are intended to provide general guidance for Prep Day.
            </p>
            <br />
            <p>
              If you have any questions about how values are calculated, please{' '}
              <a href="mailto: bcws.predictiveservices@gov.bc.ca?subject= Predictive Services Unit - HFI Calculator">
                contact us.
              </a>
            </p>
          </DialogContent>
        </Paper>
      </ModalWindow>
    </div>
  )
}

export default React.memo(AboutDataModal)
