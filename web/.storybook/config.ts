import { configure, addDecorator } from '@storybook/react'
import { ThemeDecorator } from './decorators/ThemeDecorator'
import 'index.css'

const req = require.context('../src', true, /\.stories\.tsx$/)

function loadStories() {
  req.keys().forEach(req)
}

addDecorator(ThemeDecorator)

configure(loadStories, module)
