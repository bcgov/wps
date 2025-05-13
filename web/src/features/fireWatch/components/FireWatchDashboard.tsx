import {
  BurnForecast,
  BurnStatusEnum,
  FireWatch,
  FireWatchBurnForecast,
  FuelTypeEnum,
  InPrescriptionEnum
} from '@/features/fireWatch/interfaces'
import { Box, styled, Typography, useTheme } from '@mui/material'
import {
  DataGridPro,
  DataGridProProps,
  GridActionsCellItem,
  GridColDef,
  GridValueFormatterParams
} from '@mui/x-data-grid-pro'
import { DateTime } from 'luxon'
import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { selectBurnForecasts } from '@/app/rootReducer'
import { fetchBurnForecasts } from '@/features/fireWatch/slices/burnForecastSlice'
import { AppDispatch } from '@/app/store'
import React from 'react'
import DetailPanelContent from '@/features/fireWatch/components/DetailPanelContent'
import { isNull } from 'lodash'
import InfoIcon from '@mui/icons-material/Info'
import FireWatchDetailsModal from '@/features/fireWatch/components/FireWatchDetailsModal'

export interface BurnWatchRow {
  id: number
  title: string
  fireCentre: string
  station: string
  fuelType: FuelTypeEnum
  status: BurnStatusEnum
  burnWindowStart: DateTime
  burnWindowEnd: DateTime
  inPrescription: InPrescriptionEnum
  fireWatch: FireWatch
  burnForecasts: BurnForecast[]
}

const StyledDataGrid = styled(DataGridPro)(({ theme }) => ({
  ['&.in-prescription-yes']: { backGroundColor: theme.palette.success },
  ['&.in-prescription-hfi']: { backGroundColor: theme.palette.warning }
}))

const FireWatchDashboard = () => {
  const dispatch: AppDispatch = useDispatch()
  const burnForecasts = useSelector(selectBurnForecasts)
  const theme = useTheme()
  const [rows, setRows] = useState<BurnWatchRow[]>([])
  const [modalOpen, setModalOpen] = useState(false)
  const [selectedFireWatch, setSelectedFireWatch] = useState<FireWatchBurnForecast | null>(null)

  const getInPrescription = (burnForecasts: BurnForecast[]): InPrescriptionEnum => {
    let inPrescription = InPrescriptionEnum.NO
    for (const burnForecast of burnForecasts) {
      if (burnForecast.inPrescription === InPrescriptionEnum.HFI) {
        inPrescription = InPrescriptionEnum.HFI
      }
      if (burnForecast.inPrescription === InPrescriptionEnum.YES) {
        inPrescription = InPrescriptionEnum.YES
        break
      }
    }
    return inPrescription
  }

  const shapeRows = (values: FireWatchBurnForecast[]) => {
    const newRows = values.map((value: FireWatchBurnForecast) => {
      return {
        id: value.fireWatch.id,
        title: value.fireWatch.title,
        fireCentre: value.fireWatch.fireCentre?.name ?? '',
        station: value.fireWatch.station?.name ?? '',
        fuelType: value.fireWatch.fuelType,
        status: value.fireWatch.status,
        burnWindowStart: value.fireWatch.burnWindowStart,
        burnWindowEnd: value.fireWatch.burnWindowEnd,
        inPrescription: getInPrescription(value.burnForecasts),
        fireWatch: value.fireWatch,
        burnForecasts: value.burnForecasts
      }
    })
    return newRows
  }

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
      field: 'burnWindowStart',
      headerName: 'Watch Start',
      width: 120,
      valueFormatter: (params: GridValueFormatterParams<DateTime>) => {
        return isNull(params.value) ? '' : params.value.toISODate()
      }
    },
    {
      field: 'burnWindowEnd',
      headerName: 'Watch End',
      width: 120,
      valueFormatter: (params: GridValueFormatterParams<DateTime>) => {
        return isNull(params.value) ? '' : params.value.toISODate()
      }
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
          icon={<InfoIcon />}
          label="View details"
          onClick={() => handleOpenModal(params.row)}
          showInMenu={false}
        />
      ]
    }
  ]

  useEffect(() => {
    dispatch(fetchBurnForecasts)
  }, [])

  useEffect(() => {
    const newRows = shapeRows(burnForecasts)
    setRows(newRows)
  }, [burnForecasts])

  const getDetailPanelContent = React.useCallback<NonNullable<DataGridProProps['getDetailPanelContent']>>(
    ({ row }) => <DetailPanelContent row={row} />,
    []
  )

  return (
    <Box id="fire-watch-dashboard" sx={{ flexGrow: 1 }}>
      <Typography sx={{ padding: theme.spacing(2) }} variant="h4">
        Dashboard
      </Typography>
      <Box sx={{ padding: theme.spacing(2) }}>
        <DataGridPro
          density="compact"
          disableRowSelectionOnClick
          hideFooter
          columns={columns}
          rows={rows}
          getDetailPanelContent={getDetailPanelContent}
          getDetailPanelHeight={() => 'auto'}
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
              bgcolor: '#ffffff'
            }
          }}
        />
      </Box>
      <FireWatchDetailsModal open={modalOpen} onClose={handleCloseModal} selectedFireWatch={selectedFireWatch} />
    </Box>
  )
}

export default FireWatchDashboard
