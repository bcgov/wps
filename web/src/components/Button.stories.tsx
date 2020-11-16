import React from 'react'
import { storiesOf } from '@storybook/react'
import { action } from '@storybook/addon-actions'
import { withKnobs, select } from '@storybook/addon-knobs'

import { Button } from 'components'

storiesOf('Button', module)
  .addDecorator(withKnobs)
  .add('collections', () => {
    const style = { margin: 10 }
    const color = select(
      'color',
      { Primary: 'primary', Secondary: 'secondary', Default: 'default' },
      'primary'
    )

    return (
      <>
        <Button
          color={color}
          variant="contained"
          style={style}
          onClick={action('clicked')}
        >
          Button
        </Button>
        <Button color={color} variant="contained" style={style} loading>
          Button
        </Button>
        <Button color={color} variant="contained" style={style} disabled>
          Button
        </Button>
      </>
    )
  })
