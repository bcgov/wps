import React from 'react'
import { Grid, Typography, Checkbox, List, ListItem, ListItemText, ListItemIcon, Icon } from '@mui/material'
import { styled } from '@mui/material/styles'
import {
  ADVISORY_ORANGE_FILL,
  ADVISORY_RED_FILL,
  HFI_ADVISORY,
  HFI_WARNING
} from 'features/fba/components/map/featureStylers'
import { isEqual } from 'lodash'
import { hfiLayerName, zoneStatusLayerName } from '@/features/fba/components/map/FBAMap'

const LegendGrid = styled(Grid)({
  display: 'flex',
  flexDirection: 'column',
  width: 'fit-content',
  backgroundColor: '#fffafa',
  marginLeft: '0.5rem',
  border: '2px solid black'
})

const LegendSymbol = styled(Icon)({
  width: '2.5rem',
  height: '1rem'
})

const LegendTitle = styled(Typography)({
  fontVariant: 'h1',
  fontSize: '1.2rem',
  fontWeight: 'bold',
  margin: '0.8rem 0.6rem'
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
  description?: string | null
  renderEmptyDescription?: boolean
}

const LegendItem: React.FC<LegendItemProps> = ({
  label,
  checked,
  onChange,
  subItems,
  description,
  renderEmptyDescription = false
}) => {
  return (
    <div>
      <Grid>
        <Grid container alignItems={'center'}>
          <Grid item>
            <Checkbox
              data-testid={`${label.toLowerCase().split(' ')[0]}-checkbox`}
              checked={checked}
              onChange={onChange}
            />
          </Grid>
          <Grid item>
            <Typography variant="h2" sx={{ fontSize: '1rem', fontWeight: 'bold' }}>
              {label}
            </Typography>
          </Grid>
        </Grid>
        <Grid container alignItems={'center'}>
          <Grid item sx={{ transform: 'translate(50%, -50%)' }}>
            <Typography variant="body1" sx={{ fontSize: '0.75rem' }}>
              {description ?? (renderEmptyDescription && <span>&nbsp;</span>)}
            </Typography>
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
      </Grid>
    </div>
  )
}

interface LegendProps {
  onToggleLayer: (layerName: string, isVisible: boolean) => void
  showShapeStatus: boolean
  setShowShapeStatus: React.Dispatch<React.SetStateAction<boolean>>
  showHFI: boolean
  setShowHFI: React.Dispatch<React.SetStateAction<boolean>>
}

const Legend = ({ onToggleLayer, showShapeStatus, setShowShapeStatus, showHFI, setShowHFI }: LegendProps) => {
  const handleLayerChange = (
    layerName: string,
    isVisible: boolean,
    setShowLayer: React.Dispatch<React.SetStateAction<boolean>>
  ) => {
    if (isEqual(layerName, hfiLayerName)) {
      localStorage.setItem(hfiLayerName, `${!isVisible}`)
    }
    setShowLayer(!isVisible)
    onToggleLayer(layerName, !isVisible)
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
    <LegendGrid padding={'0 0.5rem'} data-testid={`asa-map-legend`}>
      <LegendTitle align="center" gutterBottom>
        BC Fire Advisories
      </LegendTitle>
      <LegendItem
        label="Zone Unit Status"
        checked={showShapeStatus}
        onChange={() => handleLayerChange(zoneStatusLayerName, showShapeStatus, setShowShapeStatus)}
        subItems={zoneStatusSubItems}
      />
      <LegendItem
        label="HFI Potential (kW/m)"
        checked={showHFI}
        onChange={() => handleLayerChange(hfiLayerName, showHFI, setShowHFI)}
        subItems={hfiSubItems}
      />
    </LegendGrid>
  )
}

export default Legend
