import React from 'react'
import { Story, Meta } from '@storybook/react/types-6-0'

import WeatherMap from 'features/fireWeather/components/maps/WeatherMap'

export default {
  title: 'morecast/WeatherMap',
  component: WeatherMap
} as Meta

type PropTypes = React.ComponentProps<typeof WeatherMap>

const Template: Story<PropTypes> = args => (
  <div style={{ height: '500px' }}>
    <WeatherMap />
  </div>
)

export const Default = Template.bind({})
