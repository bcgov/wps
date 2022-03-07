import React from 'react'
import { makeStyles, Button } from '@material-ui/core'

export interface SaveButtonProps {
  onClick: () => void
}

const useStyles = makeStyles(() => ({
  button: {}
}))

const DownloadPDFButton = (props: SaveButtonProps) => {
  const classes = useStyles()
  return (
    <React.Fragment>
      <Button
        variant="contained"
        color="primary"
        className={classes.button}
        onClick={props.onClick}
        data-testid={'save-button'}
      >
        Download PDF
      </Button>
    </React.Fragment>
  )
}

export default React.memo(DownloadPDFButton)
