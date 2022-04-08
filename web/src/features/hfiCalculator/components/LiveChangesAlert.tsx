import { Collapse, IconButton } from '@material-ui/core'
import { createStyles, makeStyles, Theme } from '@material-ui/core/styles'
import CloseIcon from '@mui/icons-material/Close'
import Alert from '@mui/material/Alert'
import AlertTitle from '@mui/material/AlertTitle'
import React from 'react'

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

const LiveChangesAlert = () => {
  const classes = useStyles()
  const [open, setOpen] = React.useState(true)

  return (
    <div className={classes.root}>
      <Collapse in={open}>
        <Alert
          severity="warning"
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
          <AlertTitle>Warning</AlertTitle>
          Any changes made to dates, fire starts or selected stations will be reflected
          for all users in this Fire Centre and captured as an official decision. More
          nuanced controls and permissions are presently in development.
        </Alert>
      </Collapse>
    </div>
  )
}

export default React.memo(LiveChangesAlert)
