import React from 'react'
import { Story, Meta } from '@storybook/react/types-6-0'

import { Button } from 'components'

export default {
  title: 'component/Button',
  component: Button
} as Meta

type PropTypes = React.ComponentProps<typeof Button>

const Template: Story<PropTypes> = args => {
  return (
    <>
      <Button {...args} />
      <Button {...args} color="secondary" />
      <Button {...args} loading />
      <Button {...args} disabled />
      <Button {...args} loading spinnerColor="white" />
    </>
  )
}

export const MultipleStates = Template.bind({})
MultipleStates.args = {
  color: 'primary',
  variant: 'contained',
  children: 'Button',
  style: { marginRight: 20 }
}
