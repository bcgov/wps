import { theme } from '@/app/theme'
import { BurnWatchRow } from '@/features/fireWatch/components/FireWatchDashboard'
import { BurnForecast } from '@/features/fireWatch/interfaces'
import { Box } from '@mui/material'
import { DataGridPro, GridColDef, GridValueFormatterParams } from '@mui/x-data-grid-pro'
import { isNull } from 'lodash'
import { DateTime } from 'luxon'
import { useState } from 'react'

interface DetailPanelContentProps {
  row: BurnWatchRow
}

const DetailPanelContent = ({ row }: DetailPanelContentProps) => {
  const [rows, setRows] = useState<BurnForecast[]>(row.burnForecasts)

  const numberFormatter = (value: number, precision: number) => {
    if (isNaN(value)) {
      return ''
    }
    if (isNaN(precision)) {
      return value
    }
    return value.toFixed(precision)
  }

  const columns: GridColDef<BurnForecast>[] = [
    {
      field: 'date',
      headerName: 'Date',
      width: 150,
      valueFormatter: (params: GridValueFormatterParams<DateTime>) => {
        return isNull(params.value) ? '' : params.value.toISODate()
      }
    },
    {
      field: 'temp',
      headerName: 'Temp',
      width: 80,
      valueFormatter: (params: GridValueFormatterParams<number>) => numberFormatter(params.value, 1)
    },
    {
      field: 'rh',
      headerName: 'RH',
      width: 80,
      valueFormatter: (params: GridValueFormatterParams<number>) => numberFormatter(params.value, 0)
    },
    {
      field: 'windSpeed',
      headerName: 'Wind Spd',
      width: 100,
      valueFormatter: (params: GridValueFormatterParams<number>) => numberFormatter(params.value, 0)
    },
    {
      field: 'ffmc',
      headerName: 'FFMC',
      width: 80,
      valueFormatter: (params: GridValueFormatterParams<number>) => numberFormatter(params.value, 0)
    },
    {
      field: 'dmc',
      headerName: 'DMC',
      width: 80,
      valueFormatter: (params: GridValueFormatterParams<number>) => numberFormatter(params.value, 0)
    },
    {
      field: 'dc',
      headerName: 'DC',
      width: 80,
      valueFormatter: (params: GridValueFormatterParams<number>) => numberFormatter(params.value, 0)
    },
    {
      field: 'isi',
      headerName: 'ISI',
      width: 80,
      valueFormatter: (params: GridValueFormatterParams<number>) => numberFormatter(params.value, 0)
    },
    {
      field: 'bui',
      headerName: 'BUI',
      width: 80,
      valueFormatter: (params: GridValueFormatterParams<number>) => numberFormatter(params.value, 0)
    },
    {
      field: 'hfi',
      headerName: 'HFI',
      width: 80,
      valueFormatter: (params: GridValueFormatterParams<number>) => numberFormatter(params.value, 0)
    },
    {
      field: 'inPrescription',
      headerName: 'In Prescription',
      width: 120
    }
  ]

  return (
    <Box sx={{ pb: theme.spacing(2), pl: theme.spacing(4) }}>
      <DataGridPro
        density="compact"
        disableRowSelectionOnClick
        hideFooter
        columns={columns}
        rows={rows}
        getRowClassName={params => `in-prescription-${params.row.inPrescription}`}
        sx={{
          '.in-prescription-yes': {
            bgcolor: '#e1f1df',
            '&:hover': { bgcolor: '#cddfc9' }
          },
          '.in-prescription-hfi': {
            bgcolor: '#fef4cf',
            '&:hover': { bgcolor: '#fce9b3' }
          },
          '&.MuiDataGrid-root .in-prescription-no': {
            bgcolor: '#ffffff',
            '&:hover': { bgcolor: '#ffffff' }
          }
        }}
      />
    </Box>
  )
}

export default DetailPanelContent
