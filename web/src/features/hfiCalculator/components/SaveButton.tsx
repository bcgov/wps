import React from 'react'
import { makeStyles, Button } from '@material-ui/core'

export interface SaveButtonProps {
  saved: boolean
  onClick: () => void
}

const useStyles = makeStyles(() => ({
  button: {}
}))

const SaveButton = (props: SaveButtonProps) => {
  const classes = useStyles()
  return (
    <React.Fragment>
      <Button
        variant="contained"
        color="primary"
        disabled={props.saved}
        className={classes.button}
        onClick={props.onClick}
        data-testid={'save-button'}
      >
        Save changes
      </Button>
    </React.Fragment>
  )
}

export default React.memo(SaveButton)
