import { makeStyles, TableCell } from '@material-ui/core'
import { isUndefined } from 'lodash'
import React from 'react'

export interface PrepLevelCellProps {
  testid?: string
  meanIntensityGroup: number | undefined
  areaName: string
}

const prepLevelColours: { [description: string]: string } = {
  green: '#A0CD63',
  blue: '#4CAFEA',
  yellow: '#FFFD54',
  orange: '#F6C142',
  brightRed: '#EA3223',
  bloodRed: '#B02318'
}

const useStyles = makeStyles({
  prepLevel1: {
    background: prepLevelColours.green,
    fontWeight: 'bold',
    textAlign: 'center'
  },
  prepLevel2: {
    background: prepLevelColours.blue,
    fontWeight: 'bold',
    textAlign: 'center'
  },
  prepLevel3: {
    background: prepLevelColours.yellow,
    fontWeight: 'bold',
    textAlign: 'center'
  },
  prepLevel4: {
    background: prepLevelColours.orange,
    fontWeight: 'bold',
    textAlign: 'center'
  },
  prepLevel5: {
    background: prepLevelColours.brightRed,
    fontWeight: 'bold',
    textAlign: 'center',
    color: 'white'
  },
  prepLevel6: {
    background: prepLevelColours.bloodRed,
    fontWeight: 'bold',
    textAlign: 'center',
    color: 'white'
  }
})

export type PrepLevel = 1 | 2 | 3 | 4 | 5 | 6 | undefined

export const calculatePrepLevel = (meanIntensityGroup: number | undefined): PrepLevel => {
  // for now, prep level calculation assumed a fixed Fire Starts value of 0-1
  if (isUndefined(meanIntensityGroup)) {
    return undefined
  }
  if (meanIntensityGroup < 3) {
    return 1
  }
  if (meanIntensityGroup < 4) {
    return 2
  }
  if (meanIntensityGroup < 5) {
    return 3
  }
  return 4
}
const PrepLevelCell = (props: PrepLevelCellProps) => {
  const classes = useStyles()

  const prepLevel = calculatePrepLevel(props.meanIntensityGroup)

  const formatPrepLevelByValue = () => {
    switch (prepLevel) {
      case 1:
        return classes.prepLevel1
      case 2:
        return classes.prepLevel2
      case 3:
        return classes.prepLevel3
      case 4:
        return classes.prepLevel4
      case 5:
        return classes.prepLevel5
      case 6:
        return classes.prepLevel6
      default:
        return
    }
  }

  return (
    <TableCell
      className={formatPrepLevelByValue()}
      data-testid={`weekly-prep-level-${props.areaName}`}
    >
      {prepLevel}
    </TableCell>
  )
}

export default React.memo(PrepLevelCell)
