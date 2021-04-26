import React from 'react'
import { Story, Meta } from '@storybook/react/types-6-0'

import WeatherMap from 'features/fireWeather/components/maps/WeatherMap'
import { Provider } from 'react-redux'
import store from 'app/store'
import { CENTER_OF_BC } from 'utils/constants'

export default {
  title: 'morecast/WeatherMap',
  component: WeatherMap
} as Meta

type PropTypes = React.ComponentProps<typeof WeatherMap>

const Template: Story<PropTypes> = () => (
  <div style={{ height: '500px' }}>
    <Provider store={store}>{/* <WeatherMap /> */}</Provider>
  </div>
)

export const Default = Template.bind({})
