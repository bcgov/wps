import React from 'react'
import { Story, Meta } from '@storybook/react/types-6-0'

import { PercentileCalcDocumentation } from 'features/percentileCalculator/components/PercentileCalcDocumentation'

export default {
  title: 'percentile/PercentileCalcDocumentation',
  component: PercentileCalcDocumentation
} as Meta

type PropTypes = React.ComponentProps<typeof PercentileCalcDocumentation>

const Template: Story<PropTypes> = args => <PercentileCalcDocumentation />

export const Default = Template.bind({})
