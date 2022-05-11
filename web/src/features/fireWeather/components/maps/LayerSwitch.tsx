import React, { useState } from 'react'
import makeStyles from '@mui/styles/makeStyles'
import Radio from '@mui/material/Radio'
import RadioGroup from '@mui/material/RadioGroup'
import FormControlLabel from '@mui/material/FormControlLabel'
import FormControl from '@mui/material/FormControl'
import Popover from '@mui/material/Popover'
import Fab from '@mui/material/Fab'
import LayersIcon from '@mui/icons-material/Layers'

const useStyles = makeStyles({
  root: {
    position: 'absolute',
    right: 8,
    top: 8,
    zIndex: 1
  },
  btnWrapper: {
    padding: 3,
    borderRadius: '50%',
    backgroundColor: 'rgba(255,255,255,0.7)',
    opacity: 0.7
  },
  popOverContent: {
    padding: 12
  }
})

interface Props {
  map: { [k: string]: string }
  value: string
  setValue: (url: string) => void
}

const LayerSwitch = ({ map, value, setValue }: Props) => {
  const classes = useStyles()
  const [anchorEl, setAnchorEl] = useState<HTMLButtonElement | null>(null)

  const openPopover = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget)
  }
  const closePopover = () => {
    setAnchorEl(null)
  }
  const handleLayerChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setValue((event.target as HTMLInputElement).value)
  }

  const open = Boolean(anchorEl)

  return (
    <div className={classes.root}>
      <div className={classes.btnWrapper}>
        <Fab onMouseOver={openPopover} color="primary" size="small" data-testid="layer-switch">
          <LayersIcon />
        </Fab>
      </div>
      <Popover
        open={open}
        anchorEl={anchorEl}
        anchorOrigin={{
          vertical: 'top',
          horizontal: 'right'
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right'
        }}
      >
        <FormControl
          onMouseLeave={closePopover}
          className={classes.popOverContent}
          component="fieldset"
          data-testid="layer-switch-form"
        >
          <RadioGroup aria-label="base-layers" value={value} onChange={handleLayerChange}>
            {Object.keys(map).map(key => {
              return <FormControlLabel key={key} label={key} value={map[key]} control={<Radio size="small" />} />
            })}
          </RadioGroup>
        </FormControl>
      </Popover>
    </div>
  )
}

export default React.memo(LayerSwitch)
