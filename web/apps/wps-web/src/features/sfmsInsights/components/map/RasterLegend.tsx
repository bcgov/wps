import { Grid, Icon, List, ListItem, ListItemIcon, ListItemText, Typography } from '@mui/material'
import { styled } from '@mui/material/styles'
import { type ColourBreak, NON_FUEL_COLOUR_BREAKS, RASTER_CONFIG, type RasterType } from './rasterConfig'

const LegendGrid = styled(Grid)({
  position: 'absolute',
  bottom: '1rem',
  left: '1rem',
  display: 'flex',
  flexDirection: 'column',
  minWidth: '200px',
  backgroundColor: '#fffafa',
  border: '2px solid black',
  padding: '0 0.5rem',
  zIndex: 1000
})

const LegendTitle = styled(Typography)({
  fontVariant: 'h1',
  fontSize: '1.2rem',
  fontWeight: 'bold',
  margin: '0.8rem 0.6rem'
})

const LegendSymbol = styled(Icon)({
  width: '2.5rem',
  height: '1rem'
})

interface RasterLegendProps {
  rasterType: RasterType
}

const RasterLegend = ({ rasterType }: RasterLegendProps) => {
  const { label, colourBreaks, group } = RASTER_CONFIG[rasterType]
  const legendBreaks = group === 'fbp' ? [...colourBreaks, ...NON_FUEL_COLOUR_BREAKS] : colourBreaks

  return (
    <LegendGrid>
      <LegendTitle align="center" gutterBottom>
        {label}
      </LegendTitle>
      <List dense={true} sx={{ padding: 0 }}>
        {legendBreaks.map((colourBreak: ColourBreak) => (
          <ListItem disablePadding key={colourBreak.label}>
            <ListItemIcon>
              <LegendSymbol sx={{ backgroundColor: colourBreak.colour }} />
            </ListItemIcon>
            <ListItemText sx={{ pl: 1 }}>{colourBreak.label}</ListItemText>
          </ListItem>
        ))}
      </List>
    </LegendGrid>
  )
}

export default RasterLegend
