import React from 'react'
import { Button } from '@material-ui/core'

export interface SaveButtonProps {
  saved: boolean
  onClick: () => void
}

const SaveButton = (props: SaveButtonProps) => {
  return (
    <React.Fragment>
      <Button
        variant="contained"
        color="primary"
        disabled={props.saved}
        onClick={props.onClick}
        data-testid={'save-button'}
      >
        Save changes
      </Button>
    </React.Fragment>
  )
}

export default React.memo(SaveButton)
