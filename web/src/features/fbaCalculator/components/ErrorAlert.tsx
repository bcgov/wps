import React from 'react'
import makeStyles from '@mui/styles/makeStyles'
import createStyles from '@mui/styles/createStyles'
import Alert from '@mui/material/Alert'
import IconButton from '@mui/material/IconButton'
import Collapse from '@mui/material/Collapse'
import CloseIcon from '@mui/icons-material/Close'
import { theme } from 'app/theme'

const useStyles = makeStyles(() =>
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

export interface ErrorAlertProps {
  stationsError: string | null
  fbaResultsError: string | null
}

const ErrorAlert = (props: ErrorAlertProps) => {
  const classes = useStyles()
  const [open, setOpen] = React.useState(true)

  return (
    <div className={classes.root}>
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
