import { AppDispatch } from '@/app/store'
import DetailPanelContent from '@/features/fireWatch/components/DetailPanelContent'
import FireWatchDetailsModal from '@/features/fireWatch/components/FireWatchDetailsModal'
import {
  BurnForecast,
  BurnStatusEnum,
  FireWatch,
  FireWatchBurnForecast,
  FuelTypeEnum,
  PrescriptionEnum
} from '@/features/fireWatch/interfaces'
import { fetchBurnForecasts, selectBurnForecasts } from '@/features/fireWatch/slices/burnForecastSlice'
import InfoIcon from '@mui/icons-material/Info'
import { Box, styled, Typography, useTheme } from '@mui/material'
import {
  DataGridPro,
  DataGridProProps,
  GridActionsCellItem,
  GridColDef,
  GridValueFormatterParams
} from '@mui/x-data-grid-pro'
import { isNull } from 'lodash'
import { DateTime } from 'luxon'
import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { FireWatchPrescriptionColors } from 'app/theme'

export interface BurnWatchRow {
  id: number
  title: string
  fireCentre: string
  station: string
  fuelType: FuelTypeEnum
  status: BurnStatusEnum
  burnWindowStart: DateTime | null
  burnWindowEnd: DateTime | null
  inPrescription: PrescriptionEnum
  fireWatch: FireWatch
  burnForecasts: BurnForecast[]
}

const StyledDataGrid = styled(DataGridPro)(({ theme }) => ({
  ['&.in-prescription-all']: { backGroundColor: theme.palette.success },
  ['&.in-prescription-hfi']: { backGroundColor: theme.palette.warning }
}))

const FireWatchDashboard = () => {
  const dispatch: AppDispatch = useDispatch()
  const burnForecasts = useSelector(selectBurnForecasts)
  const theme = useTheme()
  const [modalOpen, setModalOpen] = useState(false)
  const [selectedFireWatch, setSelectedFireWatch] = useState<FireWatchBurnForecast | null>(null)

  const getFireWatchDetails = (row: BurnWatchRow) => {
    const fireWatchID = row.id
    const fireWatch = burnForecasts.find(fireWatch => fireWatch.fireWatch.id === fireWatchID)
    if (fireWatch) {
      return fireWatch
    }
  }

  const handleOpenModal = (row: BurnWatchRow) => {
    const fireWatch = getFireWatchDetails(row)
    if (fireWatch) {
      setSelectedFireWatch(fireWatch)
    }
    setModalOpen(true)
  }

  const handleCloseModal = () => {
    setSelectedFireWatch(null)
    setModalOpen(false)
  }

  const columns: GridColDef<BurnWatchRow>[] = [
    {
      field: 'id',
      headerName: 'ID',
      width: 80
    },
    {
      field: 'title',
      headerName: 'Burn Name',
      width: 120
    },
    {
      field: 'fireCentre',
      headerName: 'Fire Centre',
      width: 120
    },
    {
      field: 'station',
      headerName: 'Weather Station',
      width: 120
    },
    {
      field: 'fuelType',
      headerName: 'Fuel Type',
      width: 100
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 100
    },
    {
      field: 'inPrescription',
      headerName: 'In Prescription',
      width: 120
    },
    {
      field: 'details',
      headerName: 'Details',
      type: 'actions',
      width: 80,
      getActions: (params: { row: BurnWatchRow }) => [
        <GridActionsCellItem
          key={params.row.id}
          icon={<InfoIcon />}
          label="View details"
          onClick={() => handleOpenModal(params.row)}
          showInMenu={false}
        />
      ]
    }
  ]

  useEffect(() => {
    dispatch(fetchBurnForecasts())
  }, [])

  const getDetailPanelContent = React.useCallback<NonNullable<DataGridProProps['getDetailPanelContent']>>(
    ({ row }) => <DetailPanelContent row={row} />,
    []
  )

  return (
    <Box data-testid="fire-watch-dashboard" id="fire-watch-dashboard" sx={{ flexGrow: 1 }}>
      <Typography sx={{ padding: theme.spacing(2) }} variant="h4">
        Dashboard
      </Typography>
      <Box sx={{ padding: theme.spacing(2) }}>
        <DataGridPro
          density="compact"
          disableRowSelectionOnClick
          disableVirtualization
          hideFooter
          columns={columns}
          rows={burnForecasts}
          getDetailPanelContent={getDetailPanelContent}
          getDetailPanelHeight={() => 'auto'}
          getRowClassName={params => `in-prescription-${params.row.inPrescription}`}
          initialState={{
            sorting: {
              sortModel: [{ field: 'id', sort: 'asc' }]
            }
          }}
          sx={{
            '.in-prescription-all': {
              bgcolor: FireWatchPrescriptionColors.all.bgcolor,
              '&:hover': { bgcolor: FireWatchPrescriptionColors.all.hover }
            },
            '.in-prescription-hfi': {
              bgcolor: FireWatchPrescriptionColors.hfi.bgcolor,
              '&:hover': { bgcolor: FireWatchPrescriptionColors.hfi.hover }
            },
            '&.MuiDataGrid-root .in-prescription-no': {
              bgcolor: FireWatchPrescriptionColors.no.bgcolor
            }
          }}
        />
      </Box>
      <FireWatchDetailsModal open={modalOpen} onClose={handleCloseModal} selectedFireWatch={selectedFireWatch} />
    </Box>
  )
}

export default FireWatchDashboard
