import { Alert, Box } from '@mui/material'
import ClimatologyView from '@/features/climatology/components/ClimatologyView'
import type { StationOption } from '@/features/climatology/stationGroups'

export interface StationClimatologyPanelProps {
  chosen: StationOption[]
  // The name of the stations when they were chosen by drawing an area.
  label: string | null
  error: string | null
}

/** The climatology of the stations chosen on the map beside it. */
const StationClimatologyPanel = ({ chosen, label, error }: StationClimatologyPanelProps) => (
  <Box
    data-testid="station-climatology-panel"
    sx={{ flex: 1, minWidth: 0, overflowY: 'auto', padding: 2, display: 'flex', flexDirection: 'column', gap: 2 }}
  >
    {error && <Alert severity="error">The list of weather stations could not be loaded.</Alert>}
    <ClimatologyView
      stations={chosen}
      groupLabel={label}
      emptyMessage="Click a station on the map, or draw an area around several, to compare a year of daily observations with their history."
    />
  </Box>
)

export default StationClimatologyPanel
