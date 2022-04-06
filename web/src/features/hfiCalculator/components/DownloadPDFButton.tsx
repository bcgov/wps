import React from 'react'
import { Button } from '@mui/material'

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
        data-testid={'download-pdf-button'}
      >
        Download PDF
      </Button>
    </React.Fragment>
  )
}

export default React.memo(DownloadPDFButton)
