import React from 'react'
import { storiesOf } from '@storybook/react'

import { PercentileCalcDocumentation } from 'features/percentileCalculator/components/PercentileCalcDocumentation'

storiesOf('PercentileCalcDocumentation', module).add('default', () => {
  return <PercentileCalcDocumentation />
})
