import { Collapse, IconButton, Alert } from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'
import React from 'react'
import { isNull } from 'lodash'

export interface HFIErrorAlertProps {
  errors: Array<string | null>
  disableGeneralInstructions?: boolean
}

const HFIErrorAlert = ({ errors, disableGeneralInstructions }: HFIErrorAlertProps) => {
  const [open, setOpen] = React.useState(true)

  const formatErrorMessages = () => {
    return (
      <>
        {errors
          .filter(err => !isNull(err))
          .map(err => `${err}`)
          .join('\n')}
      </>
    )
  }

  const generalInstructions = () => {
    if (disableGeneralInstructions) {
      return <></>
    }
    return (
      <>
        The following errors have occurred. Please refresh the page. If the problem persists, please&nbsp;
        <a
          id="contact-hfi-error"
          href={`mailto:bcws.predictiveservices@gov.bc.ca?subject=Predictive Services Unit - HFI Error`}
        >
          contact us
        </a>
        :
        <br />
      </>
    )
  }

  return (
    <Collapse in={open}>
      <Alert
        data-testid="hfi-error-alert"
        severity="error"
        action={
          <IconButton
            aria-label="close"
            size="small"
            onClick={() => {
              setOpen(false)
            }}
          >
            <CloseIcon fontSize="inherit" />
          </IconButton>
        }
      >
        {generalInstructions()}
        {formatErrorMessages()}
      </Alert>
    </Collapse>
  )
}

export default React.memo(HFIErrorAlert)
