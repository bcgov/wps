import React from 'react'
import { render } from '@testing-library/react'
import App from 'app/App'

test('renders Hello World!', () => {
  const { getByText } = render(<App />)
  const linkElement = getByText(/Hello World!/i)
  expect(linkElement).toBeInTheDocument()
})
