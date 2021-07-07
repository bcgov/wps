import { DataGrid } from '@material-ui/data-grid'
import React from 'react'
import { FuelTypes } from '../fuelTypes'

interface FBCInputGridProps {
  testId?: string
}

const FBCInputGrid = (props: FBCInputGridProps) => {
  const fuelTypes = FuelTypes.getFriendlyNames()
  return (
    <div style={{ display: 'flex', height: 350, width: '100%' }}>
      <div style={{ flexGrow: 1 }}>
        <DataGrid
          rowHeight={30}
          columns={[
            {
              field: 'weatherStation',
              headerName: 'Weather Station',
              flex: 1,
              type: 'singleSelect',
              editable: true,
              valueOptions: ['AFTON', 'ALLISON PASS']
            },
            {
              field: 'fuelType',
              flex: 1,
              headerName: 'Fuel Type',
              type: 'singleSelect',
              editable: true,
              valueOptions: fuelTypes
            },
            {
              field: 'grassCure',
              headerName: 'Grass Cure %',
              flex: 1,
              type: 'number',
              editable: true
            }
          ]}
          rows={[{ id: 1, weatherStation: 'Afton', fuelType: 'C1', grassCure: 0 }]}
        />
      </div>
    </div>
  )
}

export default React.memo(FBCInputGrid)
