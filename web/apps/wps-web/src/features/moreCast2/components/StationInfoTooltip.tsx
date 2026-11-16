import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'
import { IconButton, Tooltip, Typography } from '@mui/material'

interface StationInfoTooltipProps {
  stationCode: number
  stationName: string
  elevationLabel: string
  tabIndex: number
}

const StationInfoTooltip = ({ stationCode, stationName, elevationLabel, tabIndex }: StationInfoTooltipProps) => {
  return (
    <Tooltip
      arrow
      describeChild
      placement="top-start"
      slotProps={{
        // tooltip events still bubble through the station cell
        popper: {
          onClick: event => event.stopPropagation(),
          onDoubleClick: event => event.stopPropagation()
        }
      }}
      title={
        <>
          <Typography component="div" variant="body2" sx={{ fontWeight: 600 }}>
            {stationName}
          </Typography>
          <Typography component="div" variant="body2">
            Station code: {stationCode}
          </Typography>
          <Typography component="div" variant="body2">
            Station elevation: {elevationLabel}
          </Typography>
        </>
      }
    >
      <IconButton
        size="small"
        aria-label={`Station metadata for ${stationName}`}
        tabIndex={tabIndex}
        onClick={event => event.stopPropagation()}
        onDoubleClick={event => event.stopPropagation()}
        onKeyDown={event => {
          // keep button activation from selecting or editing a grid row
          if (event.key === 'Enter' || event.key === ' ') event.stopPropagation()
        }}
      >
        <InfoOutlinedIcon sx={{ fontSize: 16 }} />
      </IconButton>
    </Tooltip>
  )
}

export default StationInfoTooltip
