import UploadIcon from '@mui/icons-material/Upload'
import { Button } from '@mui/material'
import { isNull } from 'lodash'
import GeoJSON from 'ol/format/GeoJSON'
import React, { useRef } from 'react'
import { Feature } from 'ol'
import { Geometry } from 'ol/geom'

interface ValuesImportButtonProps {
  setValues: React.Dispatch<React.SetStateAction<Feature<Geometry>[]>>
}

export const ValuesImportButton = ({ setValues }: ValuesImportButtonProps) => {
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileInput = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!isNull(files)) {
      const bodyContent = new FormData()
      bodyContent.append('file', files[0])

      const reader = new FileReader()

      reader.onload = e => {
        if (e.target && e.target.result) {
          try {
            const geojsonData = JSON.parse(e.target.result as string)
            const valuesGeoJson = new GeoJSON().readFeatures(geojsonData, {
              featureProjection: 'EPSG:3857'
            })

            valuesGeoJson.forEach((feature, index) => {
              feature.setProperties({ id: index })
              feature.setId(index)
            })

            setValues(valuesGeoJson)
          } catch (error) {
            console.error('Error parsing GeoJSON data:', error)
          }
        }
      }

      reader.readAsText(files[0])

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
