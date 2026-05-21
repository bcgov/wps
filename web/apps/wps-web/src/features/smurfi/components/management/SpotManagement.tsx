import { AppDispatch } from '@/app/store'
import SpotAdmin from '@/features/smurfi/components/management/SpotManagementTable'
import SMURFIMap, { SelectedCoordinates } from '@/features/smurfi/components/map/SMURFIMap'
import { fetchSpotRequests, selectSmurfi } from '@/features/smurfi/slices/smurfiSlice'
import { selectFireCentres } from '@/app/rootReducer'
import { fetchFireCentres } from '@/commonSlices/fireCentresSlice'
import { Box, Button, CircularProgress, Typography } from '@mui/material'
import { SpotAdminRow, SpotRequestOutput } from '@wps/api/SMURFIAPI'
import { DateTime } from 'luxon'
import { useEffect, useMemo, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'

const toMillis = (dateTime: string | null | undefined) => {
  if (!dateTime) {
    return null
  }
  const parsedDateTime = DateTime.fromISO(dateTime)
  return parsedDateTime.isValid ? parsedDateTime.toMillis() : null
}

const getFireCentreName = (fireCentreId: number, fireCentres: { id: number; name: string }[]) =>
  fireCentres.find(fireCentre => fireCentre.id === fireCentreId)?.name ?? String(fireCentreId)

const buildSpotAdminRow = (
  spotRequest: SpotRequestOutput,
  fireCentres: { id: number; name: string }[]
): SpotAdminRow => ({
  id: spotRequest.id,
  spot_id: spotRequest.id,
  fire_id: spotRequest.fire_number?.[0] ?? '',
  forecaster: 'Unassigned',
  fire_centre: getFireCentreName(spotRequest.fire_centre, fireCentres),
  status: spotRequest.status,
  last_updated: toMillis(spotRequest.requested_at),
  latitude: spotRequest.latitude,
  longitude: spotRequest.longitude,
  spot_start: toMillis(spotRequest.start_at) ?? 0,
  spot_end: toMillis(spotRequest.end_at) ?? 0,
  spot_request: spotRequest
})

const SpotManagement = () => {
  const dispatch: AppDispatch = useDispatch()
  const { spotRequests, spotRequestsError, spotRequestsLoading } = useSelector(selectSmurfi)
  const { fireCentres } = useSelector(selectFireCentres)
  const [selectedRowId, setSelectedRowId] = useState<number | undefined>(undefined)
  useEffect(() => {
    dispatch(fetchSpotRequests())
    dispatch(fetchFireCentres())
  }, [dispatch])

  const spotAdminRows = useMemo(
    () => spotRequests.map(spotRequest => buildSpotAdminRow(spotRequest, fireCentres)),
    [fireCentres, spotRequests]
  )

  // Get coordinates of selected row for map highlighting
  const selectedCoordinates: SelectedCoordinates | null = useMemo(() => {
    if (selectedRowId === undefined) return null
    const selectedRow = spotAdminRows.find(row => row.id === selectedRowId)
    if (!selectedRow) return null
    return {
      latitude: selectedRow.latitude,
      longitude: selectedRow.longitude
    }
  }, [selectedRowId, spotAdminRows])

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 0 }}>
      {spotRequestsLoading && <CircularProgress aria-label="Loading spot requests" sx={{ mt: 2 }} />}
      {spotRequestsError && (
        <Typography color="error" sx={{ mt: 2 }}>
          Unable to load spot requests.
        </Typography>
      )}
      <Box sx={{ height: '100%', display: 'flex', flex: 1, flexDirection: 'row', minHeight: 0, pt: 2 }}>
        <Box sx={{ flex: 1 }}>
          <Box sx={{ display: 'flex', flexGrow: 1 }}>
            <SpotAdmin
              spotAdminRows={spotAdminRows}
              selectedRowId={selectedRowId}
              setSelectedRowId={setSelectedRowId}
            />
          </Box>
        </Box>
        <Box sx={{ height: '100%', flex: 1, position: 'relative', minHeight: 0 }}>
          <SMURFIMap selectedCoordinates={selectedCoordinates} spotRequests={spotRequests} />
        </Box>
      </Box>
    </Box>
  )
}

export default SpotManagement
