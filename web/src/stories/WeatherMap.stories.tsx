import React from 'react'
import { Story, Meta } from '@storybook/react/types-6-0'

import WeatherMap from 'features/fireWeather/components/maps/WeatherMap'

export default {
  title: 'component/WeatherMap',
  component: WeatherMap
} as Meta

type PropTypes = React.ComponentProps<typeof WeatherMap>

const Template: Story<PropTypes> = args => <WeatherMap />

export const Default = Template.bind({})
