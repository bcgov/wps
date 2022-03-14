import React from 'react'
import { Button } from '@material-ui/core'

export interface SaveButtonProps {
  onClick: () => void
}

const DownloadPDFButton = (props: SaveButtonProps) => {
  return (
    <React.Fragment>
      <Button
        variant="contained"
        color="primary"
        onClick={props.onClick}
        data-testid={'save-button'}
      >
        Download PDF
      </Button>
    </React.Fragment>
  )
}

export default React.memo(DownloadPDFButton)
