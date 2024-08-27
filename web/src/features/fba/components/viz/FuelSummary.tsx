import React, { useEffect, useState } from 'react'
import { FireShape, FireZoneThresholdFuelTypeArea } from 'api/fbaAPI'
import { Box, Tooltip, Typography } from '@mui/material'
import { groupBy, isUndefined } from 'lodash'
import { DateTime } from 'luxon'
import FuelDistribution from 'features/fba/components/viz/FuelDistribution'
import { DataGridPro, GridColDef, GridColumnHeaderParams, GridRenderCellParams } from '@mui/x-data-grid-pro'
import { styled, useTheme } from '@mui/material/styles'

export interface FuelTypeInfoSummary {
  area: number
  criticalHoursStart?: DateTime
  criticalHoursEnd?: DateTime
  id: number
  code: string
  description: string
  percent?: number
  selected: boolean
}

interface FuelSummaryProps {
  fuelTypeInfo: Record<number, FireZoneThresholdFuelTypeArea[]>
  selectedFireZoneUnit: FireShape | undefined
}

const StyledHeader = styled('div')({
  whiteSpace: 'normal',
  wordWrap: 'break-word',
  textAlign: 'center',
  fontSize: '0.75rem',
  fontWeight: '700'
})

// Column definitions for fire zone unit fuel summary table
const columns: GridColDef[] = [
  {
    field: 'code',
    headerClassName: 'fuel-summary-header',
    headerName: 'Primary Fuels',
    sortable: false,
    width: 120,
    renderHeader: (params: GridColumnHeaderParams) => <StyledHeader>{params.colDef.headerName}</StyledHeader>,
    renderCell: (params: GridRenderCellParams) => (
      <Tooltip placement="right" title={params.row['description']}>
        <Typography sx={{ fontSize: '0.75rem' }}>{params.row[params.field]}</Typography>
      </Tooltip>
    )
  },
  {
    field: 'area',
    flex: 3,
    headerClassName: 'fuel-summary-header',
    headerName: 'Proportion of Advisory Area',
    minWidth: 200,
    sortable: false,
    renderHeader: (params: GridColumnHeaderParams) => <StyledHeader>{params.colDef.headerName}</StyledHeader>,
    renderCell: (params: GridRenderCellParams) => {
      return <FuelDistribution code={params.row['code']} percent={params.row['percent']} />
    }
  }
]

const FuelSummary = ({ fuelTypeInfo, selectedFireZoneUnit }: FuelSummaryProps) => {
  const theme = useTheme()
  const [fuelTypeInfoRollup, setFuelTypeInfoRollup] = useState<FuelTypeInfoSummary[]>([])

  useEffect(() => {
    if (isUndefined(fuelTypeInfo) || isUndefined(selectedFireZoneUnit)) {
      setFuelTypeInfoRollup([])
      return
    }
    const shapeId = selectedFireZoneUnit.fire_shape_id
    const fuelDetails = fuelTypeInfo[shapeId]
    if (isUndefined(fuelDetails)) {
      setFuelTypeInfoRollup([])
      return
    }
    // Sum the total area with HFI > 4000 for all fuel types
    const totalHFIArea4K = fuelDetails.reduce((acc, { area }) => acc + area, 0)
    const rollUp: FuelTypeInfoSummary[] = []
    // We receive HFI area per fuel type per HFI threshold (4-10K and >10K), so group fuel type.
    // Iterate through the groups adding the area for both HFI thresholds' we're interested in all
    // HFI > 4,000.
    const groupedFuelDetails = groupBy(fuelDetails, 'fuel_type.fuel_type_id')
    for (const key in groupedFuelDetails) {
      const groupedFuelDetail = groupedFuelDetails[key]
      if (groupedFuelDetail.length) {
        const area = groupedFuelDetail.reduce((acc, { area }) => acc + area, 0)
        const fuelType = groupedFuelDetail[0].fuel_type
        const fuelInfo: FuelTypeInfoSummary = {
          area,
          code: fuelType.fuel_type_code,
          description: fuelType.description,
          id: fuelType.fuel_type_id,
          percent: totalHFIArea4K ? (area / totalHFIArea4K) * 100 : 0,
          selected: false
        }
        rollUp.push(fuelInfo)
      }
    }
    setFuelTypeInfoRollup(rollUp)
  }, [fuelTypeInfo]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <Box sx={{ paddingBottom: theme.spacing(2), paddingTop: theme.spacing(2) }}>
      {fuelTypeInfoRollup.length === 0 ? (
        <Typography>No fuel type information available.</Typography>
      ) : (
        <DataGridPro
          columns={columns}
          density="compact"
          disableColumnMenu
          disableChildrenSorting
          disableRowSelectionOnClick
          hideFooter={true}
          initialState={{
            sorting: {
              sortModel: [{ field: 'area', sort: 'desc' }]
            }
          }}
          rows={fuelTypeInfoRollup}
          showCellVerticalBorder
          showColumnVerticalBorder
          sx={{
            backgroundColor: 'white',
            maxHeight: '147px',
            minHeight: '100px',
            overflow: 'hidden',
            '& .MuiDataGrid-columnHeaderTitle': {
              fontWeight: 'bold'
            },
            '& .fuel-summary-header': {
              background: '#F1F1F1'
            }
          }}
        ></DataGridPro>
      )}
    </Box>
  )
}

export default FuelSummary
