import UploadIcon from '@mui/icons-material/Upload'
import { Button } from '@mui/material'
import { isNull } from 'lodash'
import React, { useRef } from 'react'

interface ImportButtonProps {
  setFile: React.Dispatch<React.SetStateAction<File | null>>
}

export const ImportButton = ({ setFile }: ImportButtonProps) => {
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileInput = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!isNull(files)) {
      const bodyContent = new FormData()
      bodyContent.append('file', files[0])

      // TODO upload to endpoint
      console.log(files[0])
      setFile(files[0])

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
        accept=".shp,.csv,.geojson"
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
