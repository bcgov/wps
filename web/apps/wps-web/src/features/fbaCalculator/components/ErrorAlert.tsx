import React from 'react'
import Alert from '@mui/material/Alert'
import IconButton from '@mui/material/IconButton'
import Collapse from '@mui/material/Collapse'
import CloseIcon from '@mui/icons-material/Close'

export interface ErrorAlertProps {
  stationsError: string | null
  fbaResultsError: string | null
}

const ErrorAlert = (props: ErrorAlertProps) => {
  const [open, setOpen] = React.useState(true)

  return (
    <div>
      <Collapse in={open}>
        <Alert
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
          The following errors have occurred. Please refresh the page. If the problem persists, please&nbsp;
          <a
            id="contact-fba-error"
            href={`mailto:bcws.predictiveservices@gov.bc.ca?subject=Predictive Services Unit - FBA Error`}
          >
            contact us
          </a>
          :
          <br />
          {props.fbaResultsError ? ` - ${props.fbaResultsError}` : ''}
          {props.stationsError ? <br /> + ` - ${props.fbaResultsError}` : ''}
        </Alert>
      </Collapse>
    </div>
  )
}

export default React.memo(ErrorAlert)
