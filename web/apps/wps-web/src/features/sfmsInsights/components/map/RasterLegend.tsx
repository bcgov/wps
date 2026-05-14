import { Grid, Icon, List, ListItem, ListItemIcon, ListItemText, Typography } from '@mui/material'
import { styled } from '@mui/material/styles'
import { RASTER_CONFIG, RasterType, ColorBreak } from './rasterConfig'

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
  const { label, colorBreaks } = RASTER_CONFIG[rasterType]

  return (
    <LegendGrid>
      <LegendTitle align="center" gutterBottom>
        {label}
      </LegendTitle>
      <List dense={true} sx={{ padding: 0 }}>
        {colorBreaks.map((colorBreak: ColorBreak) => (
          <ListItem disablePadding key={colorBreak.label}>
            <ListItemIcon>
              <LegendSymbol sx={{ backgroundColor: colorBreak.color }} />
            </ListItemIcon>
            <ListItemText>{colorBreak.label}</ListItemText>
          </ListItem>
        ))}
      </List>
    </LegendGrid>
  )
}

export default RasterLegend
