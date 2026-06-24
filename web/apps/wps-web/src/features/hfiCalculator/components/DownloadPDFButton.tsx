import GetAppIcon from '@mui/icons-material/GetApp'
import { Button } from '@mui/material'
import React from 'react'
export interface DownloadPDFButtonProps {
  onClick: () => void
}

const DownloadPDFButton = (props: DownloadPDFButtonProps) => {
  return (
    <Button variant="text" color="primary" onClick={props.onClick} data-testid={'download-pdf-button'}>
      <GetAppIcon />
      Download PDF
    </Button>
  )
}

export default React.memo(DownloadPDFButton)
