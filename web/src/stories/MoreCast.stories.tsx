import React from 'react'
import { Story, Meta } from '@storybook/react/types-6-0'

import MoreCastPage from 'features/fireWeather/pages/NewMoreCastPage'

export default {
  title: 'component/NewMoreCastPage',
  component: MoreCastPage
} as Meta

const Template: Story = args => {
  return <MoreCastPage {...args} />
}

export const Default = Template.bind({})
