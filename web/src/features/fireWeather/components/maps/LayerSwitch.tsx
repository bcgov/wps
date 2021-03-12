import React, { useState } from 'react'
import { makeStyles } from '@material-ui/core/styles'
import Radio from '@material-ui/core/Radio'
import RadioGroup from '@material-ui/core/RadioGroup'
import FormControlLabel from '@material-ui/core/FormControlLabel'
import FormControl from '@material-ui/core/FormControl'
import Popover from '@material-ui/core/Popover'
import Fab from '@material-ui/core/Fab'
import LayersIcon from '@material-ui/icons/Layers'

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
  layersMap: { [k: string]: string }
  layerUrl: string
  setLayerUrl: (url: string) => void
}

const LayerSwitch = ({ layersMap, layerUrl, setLayerUrl }: Props) => {
  const classes = useStyles()
  const [anchorEl, setAnchorEl] = useState<HTMLButtonElement | null>(null)

  const openPopover = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget)
  }
  const closePopover = () => {
    setAnchorEl(null)
  }
  const handleLayerChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setLayerUrl((event.target as HTMLInputElement).value)
  }

  const open = Boolean(anchorEl)

  return (
    <div className={classes.root}>
      <div className={classes.btnWrapper}>
        <Fab onMouseOver={openPopover} color="primary" size="small">
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
        >
          <RadioGroup
            aria-label="base-layer"
            value={layerUrl}
            onChange={handleLayerChange}
          >
            {Object.keys(layersMap).map(key => {
              return (
                <FormControlLabel
                  key={key}
                  label={key}
                  value={layersMap[key]}
                  control={<Radio size="small" />}
                />
              )
            })}
          </RadioGroup>
        </FormControl>
      </Popover>
    </div>
  )
}

export default React.memo(LayerSwitch)
