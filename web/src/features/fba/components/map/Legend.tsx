import React from 'react'
import { Grid, Typography, Checkbox } from '@mui/material'
import { styled } from '@mui/material/styles'

interface LegendItemProps {
  label: string
  checked: boolean
  onChange: (event: React.ChangeEvent<HTMLInputElement>, checked: boolean) => void
}

const LegendItem: React.FC<LegendItemProps> = ({ label, checked, onChange }) => (
  <Grid container alignItems={'center'}>
    <Grid item>
      <Checkbox checked={checked} onChange={onChange} />
    </Grid>
    <Grid item>
      <Typography variant="body2">{label}</Typography>
    </Grid>
  </Grid>
)

const LegendGrid = styled(Grid)({
  display: 'flex',
  flexDirection: 'column',
  width: 'fit-content',
  backgroundColor: '#fffafa',
  paddingRight: '1rem'
})

interface LegendProps {
  onToggleLayer: (layerName: string, isVisible: boolean) => void
}

const Legend = ({ onToggleLayer }: LegendProps) => {
  const [fireZoneChecked, setFireZoneChecked] = React.useState(true)
  const [hfiChecked, setHFIChecked] = React.useState(false)

  const handleLayer1Change = () => {
    setFireZoneChecked(!fireZoneChecked)
    onToggleLayer('fireZoneVector', !fireZoneChecked)
  }

  const handleLayer2Change = () => {
    setHFIChecked(!hfiChecked)
    onToggleLayer('hfiVector', !hfiChecked)
  }

  return (
    <LegendGrid>
      <LegendItem label="Zone Status" checked={fireZoneChecked} onChange={handleLayer1Change} />
      <LegendItem label="HFI Potential (kW/h)" checked={hfiChecked} onChange={handleLayer2Change} />
    </LegendGrid>
  )
}

export default Legend
