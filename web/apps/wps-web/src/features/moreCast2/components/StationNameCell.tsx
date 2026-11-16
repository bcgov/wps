import { Box, Typography } from '@mui/material'
import type { RootState } from 'app/rootReducer'
import StationInfoTooltip from 'features/moreCast2/components/StationInfoTooltip'
import { selectSelectedStations } from 'features/moreCast2/slices/selectedStationsSlice'
import { useSelector } from 'react-redux'

interface StationNameCellProps {
  stationCode: number
  stationName: string
  hasFocus?: boolean
}

const elevationFormatter = new Intl.NumberFormat('en-CA', { maximumFractionDigits: 0 })

const StationNameCell = ({ stationCode, stationName, hasFocus = false }: StationNameCellProps) => {
  const elevation = useSelector(
    (state: RootState) => selectSelectedStations(state).find(station => station.station_code === stationCode)?.elevation
  )
  const elevationLabel =
    typeof elevation === 'number' && Number.isFinite(elevation)
      ? `${elevationFormatter.format(elevation)} m`
      : 'Unknown'

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 0.5,
        minWidth: 0,
        width: '100%',
        height: '100%'
      }}
    >
      <Typography component="span" variant="body2" noWrap>
        {stationName}
      </Typography>
      <StationInfoTooltip
        stationCode={stationCode}
        stationName={stationName}
        elevationLabel={elevationLabel}
        tabIndex={hasFocus ? 0 : -1}
      />
    </Box>
  )
}

export default StationNameCell
