import { render, screen } from '@testing-library/react'
import { NoMatchPage } from './NoMatchPage'

describe('NoMatchPage', () => {
  it('renders page not found message', () => {
    render(<NoMatchPage />)
    expect(screen.getByText('Page Not Found')).toBeInTheDocument()
  })
})
