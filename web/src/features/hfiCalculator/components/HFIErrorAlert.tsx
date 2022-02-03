import { Collapse, IconButton } from '@material-ui/core'
import { createStyles, makeStyles, Theme } from '@material-ui/core/styles'
import { Alert } from '@material-ui/lab'
import CloseIcon from '@material-ui/icons/Close'
import React from 'react'

export interface HFIErrorAlertProps {
  hfiDailiesError: string | null
  fireCentresError: string | null
}

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      width: '100%',
      '& > * + *': {
        marginTop: theme.spacing(2)
      },
      marginBottom: theme.spacing(2)
    }
  })
)

const HFIErrorAlert = ({ hfiDailiesError, fireCentresError }: HFIErrorAlertProps) => {
  const classes = useStyles()
  const [open, setOpen] = React.useState(true)

  return (
    <div className={classes.root}>
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
          The following errors have occurred. Please refresh the page. If the problem
          persists, please&nbsp;
          <a
            id="contact-hfi-error"
            href={`mailto:bcws.predictiveservices@gov.bc.ca?subject=Predictive Services Unit - HFI Error`}
          >
            contact us
          </a>
          :
          <br />
          {hfiDailiesError ? ` - ${hfiDailiesError}` : ''}
          {fireCentresError ? <br /> + ` - ${fireCentresError}` : ''}
        </Alert>
      </Collapse>
    </div>
  )
}

export default React.memo(HFIErrorAlert)
