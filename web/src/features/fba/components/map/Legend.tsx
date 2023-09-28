import React from 'react'
import { Grid, Typography, Checkbox, List, ListItem, ListItemText, ListItemIcon, Icon } from '@mui/material'
import { styled } from '@mui/material/styles'
import {
  ADVISORY_ORANGE_FILL,
  ADVISORY_RED_FILL,
  HFI_ADVISORY,
  HFI_WARNING
} from 'features/fba/components/map/featureStylers'

const LegendGrid = styled(Grid)({
  display: 'flex',
  flexDirection: 'column',
  width: 'fit-content',
  backgroundColor: '#fffafa',
  paddingRight: '0.5rem',
  paddingLeft: '0.5rem',
  marginLeft: '0.5rem',
  border: '2px solid black'
})

const LegendSymbol = styled(Icon)({
  width: '2.5rem',
  height: '1rem'
})

interface SubItem {
  label: string
  symbol: string
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
      <List dense={true} sx={{ marginLeft: '2.5rem', marginTop: '-1rem' }}>
        {subItems.map(subItem => (
          <ListItem disablePadding key={subItem.label}>
            <ListItemIcon>
              <LegendSymbol sx={{ backgroundColor: subItem.symbol }} />
            </ListItemIcon>
            <ListItemText>{subItem.label}</ListItemText>
          </ListItem>
        ))}
      </List>
    )}
  </div>
)

interface LegendProps {
  onToggleLayer: (layerName: string, isVisible: boolean) => void
  showZoneStatus: boolean
  setShowZoneStatus: React.Dispatch<React.SetStateAction<boolean>>
  showHFI: boolean
  setShowHFI: React.Dispatch<React.SetStateAction<boolean>>
}

const Legend = ({ onToggleLayer, showZoneStatus, setShowZoneStatus, showHFI, setShowHFI }: LegendProps) => {
  const handleFireZoneLayerChange = () => {
    setShowZoneStatus(!showZoneStatus)
    onToggleLayer('fireZoneVector', !showZoneStatus)
  }

  const handleHFILayerChange = () => {
    setShowHFI(!showHFI)
    onToggleLayer('hfiVector', !showHFI)
  }

  const zoneStatusSubItems: SubItem[] = [
    { label: 'Advisory', symbol: ADVISORY_ORANGE_FILL },
    { label: 'Warning', symbol: ADVISORY_RED_FILL }
  ]
  const hfiSubItems: SubItem[] = [
    { label: '4,000 to 9,999', symbol: HFI_ADVISORY },
    { label: '≥10,000', symbol: HFI_WARNING }
  ]

  return (
    <LegendGrid>
      <Typography align="center" variant="body2" gutterBottom sx={{ fontWeight: 'bold' }}>
        BC Fire Advisory Legend
      </Typography>
      <LegendItem
        label="Zone Status"
        checked={showZoneStatus}
        onChange={handleFireZoneLayerChange}
        subItems={zoneStatusSubItems}
      />
      <LegendItem
        label="HFI Potential (kW/h)"
        checked={showHFI}
        onChange={handleHFILayerChange}
        subItems={hfiSubItems}
      />
    </LegendGrid>
  )
}

export default Legend
