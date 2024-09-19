import UploadIcon from '@mui/icons-material/Upload'
import { Button } from '@mui/material'
import { isNull } from 'lodash'
import React, { useRef } from 'react'

interface ValuesImportButtonProps {
  growFire: () => Promise<void>
}

export const GrowFireButton = ({ growFire }: ValuesImportButtonProps) => {
  return (
    <Button variant="contained" component="label" startIcon={<UploadIcon />} onClick={() => growFire()}>
      Grow Fire
    </Button>
  )
}
