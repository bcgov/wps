import UploadIcon from '@mui/icons-material/Upload'
import { Button, ListItemIcon, ListItemText, MenuItem } from '@mui/material'
import { isNull } from 'lodash'
import React, { useRef } from 'react'
import { useDispatch } from 'react-redux'

export const ImportButton = () => {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const dispatch = useDispatch()

  const handleFileInput = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!isNull(files)) {
      const bodyContent = new FormData()
      bodyContent.append('file', files[0])

      // TODO upload to endpoint

      // Reset the file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }
  return (
    <Button variant="contained" component="label" startIcon={<UploadIcon />}>
      Upload Values file
      <input
        ref={fileInputRef}
        hidden
        accept="text/html,.csv"
        multiple
        type="file"
        onChange={handleFileInput}
        onClick={e => {
          ;(e.target as HTMLInputElement).value = ''
        }}
      />
    </Button>
  )
}
