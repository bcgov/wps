import React from 'react'
import { Grid, Typography, Checkbox, List, ListItem, ListItemText } from '@mui/material'
import { styled } from '@mui/material/styles'

interface SubItem {
  label: string
}
interface LegendItemProps {
  label: string
  checked: boolean
  onChange: (event: React.ChangeEvent<HTMLInputElement>, checked: boolean) => void
  subItems?: SubItem[]
}

const LegendItem: React.FC<LegendItemProps> = ({ label, checked, onChange, subItems }) => (
  <div>
    <Grid container alignItems={'center'}>
      <Grid item>
        <Checkbox checked={checked} onChange={onChange} />
      </Grid>
      <Grid item>
        <Typography variant="body2">{label}</Typography>
      </Grid>
    </Grid>
    {subItems && (
      <List dense={true} sx={{ marginLeft: '5rem', marginTop: '-1rem' }}>
        {subItems.map(subItem => (
          <ListItem disablePadding key={subItem.label}>
            <ListItemText>{subItem.label}</ListItemText>
          </ListItem>
        ))}
      </List>
    )}
  </div>
)

const LegendGrid = styled(Grid)({
  display: 'flex',
  flexDirection: 'column',
  width: 'fit-content',
  backgroundColor: '#fffafa',
  paddingRight: '1rem',
  marginLeft: '1rem'
})

interface LegendProps {
  onToggleLayer: (layerName: string, isVisible: boolean) => void
}

const Legend = ({ onToggleLayer }: LegendProps) => {
  const [zoneStatusChecked, setZoneStatusChecked] = React.useState(true)
  const [hfiChecked, setHFIChecked] = React.useState(false)

  const handleFireZoneLayerChange = () => {
    setZoneStatusChecked(!zoneStatusChecked)
    onToggleLayer('fireZoneVector', !zoneStatusChecked)
  }

  const handleHFILayerChange = () => {
    setHFIChecked(!hfiChecked)
    onToggleLayer('hfiVector', !hfiChecked)
  }

  const zoneStatusSubItems: SubItem[] = [{ label: 'Advisory' }, { label: 'Warning' }]
  const hfiSubItems: SubItem[] = [{ label: '4,000 to 9,999' }, { label: '≥10,000' }]

  return (
    <LegendGrid>
      <LegendItem
        label="Zone Status"
        checked={zoneStatusChecked}
        onChange={handleFireZoneLayerChange}
        subItems={zoneStatusSubItems}
      />
      <LegendItem
        label="HFI Potential (kW/h)"
        checked={hfiChecked}
        onChange={handleHFILayerChange}
        subItems={hfiSubItems}
      />
    </LegendGrid>
  )
}

export default Legend
