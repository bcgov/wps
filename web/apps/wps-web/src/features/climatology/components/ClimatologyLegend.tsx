import { Box, Typography } from '@mui/material'
import { BAND_COLOURS, MEDIAN_COLOUR, YEAR_COLOUR } from '@/features/climatology/components/ClimatologyChart'

interface LegendItem {
  label: string
  colour: string
  // A band is keyed with a filled box and a line with a stroke, as each is drawn.
  kind: 'band' | 'line'
  thickness?: number
}

const Key = ({ item }: { item: LegendItem }) => (
  <Box
    aria-hidden
    sx={
      item.kind === 'band'
        ? { width: 14, height: 14, borderRadius: '2px', backgroundColor: item.colour, opacity: 0.85 }
        : { width: 22, height: 0, borderTop: `${item.thickness}px solid ${item.colour}` }
    }
  />
)

const ClimatologyLegend = ({ year }: { year: number }) => {
  const items: LegendItem[] = [
    { label: `${year}`, colour: YEAR_COLOUR, kind: 'line', thickness: 3 },
    { label: 'Historical median', colour: MEDIAN_COLOUR, kind: 'line', thickness: 2 },
    { label: 'Extreme (90th percentile and above)', colour: BAND_COLOURS.extreme, kind: 'band' },
    { label: 'Above normal (75th to 90th)', colour: BAND_COLOURS.aboveNormal, kind: 'band' },
    { label: 'Normal (25th to 75th)', colour: BAND_COLOURS.normal, kind: 'band' },
    { label: 'Below normal (lowest to 25th)', colour: BAND_COLOURS.belowNormal, kind: 'band' }
  ]
  return (
    <Box
      component="ul"
      data-testid="climatology-legend"
      sx={{ display: 'flex', flexWrap: 'wrap', columnGap: 3, rowGap: 1, listStyle: 'none', padding: 0, margin: 0 }}
    >
      {items.map(item => (
        <Box component="li" key={item.label} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Key item={item} />
          <Typography variant="body2">{item.label}</Typography>
        </Box>
      ))}
    </Box>
  )
}

export default ClimatologyLegend
