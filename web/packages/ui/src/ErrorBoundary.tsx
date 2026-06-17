import WarningSharp from '@mui/icons-material/WarningSharp'
import type React from 'react'
import { Component } from 'react'

interface Props {
  children: React.ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  errorInfo?: React.ErrorInfo
}

export class ErrorBoundary extends Component<Props, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  render() {
    const { hasError } = this.state

    if (hasError) {
      // Render fallback UI
      return (
        <div
          style={{
            border: '1px solid crimson',
            borderRadius: '7px',
            padding: '12px',
            color: 'crimson',
            display: 'flex',
            alignItems: 'center'
          }}
        >
          <WarningSharp style={{ marginRight: '6px' }} fontSize="small" />
          <span>
            Unexpected error occurred in this section. You may want to reload the page and try it again.{' '}
            <button
              type="button"
              style={{
                cursor: 'pointer',
                color: '#0077FF',
                background: 'none',
                border: 'none',
                padding: 0,
                font: 'inherit'
              }}
              onClick={() => {
                window.location.reload()
              }}
            >
              Reload
            </button>
          </span>
        </div>
      )
    }

    return this.props.children
  }
}
