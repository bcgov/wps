import React from 'react'
import { Button } from '@mui/material'
import GetAppIcon from '@mui/icons-material/GetApp'
export interface DownloadPDFButtonProps {
  onClick: () => void
}

const DownloadPDFButton = (props: DownloadPDFButtonProps) => {
  return (
    <React.Fragment>
      <Button variant="text" color="primary" onClick={props.onClick} data-testid={'download-pdf-button'}>
        <GetAppIcon />
        Download PDF
      </Button>
    </React.Fragment>
  )
}

export default React.memo(DownloadPDFButton)
