import { configureStore } from '@reduxjs/toolkit'
import { CssBaseline } from '@mui/material'
import { ThemeProvider } from '@mui/material/styles'
import { theme } from '@wps/ui/theme'
import { createRoot } from 'react-dom/client'
import { Provider } from 'react-redux'
import { MemoryRouter } from 'react-router-dom'
import './mockApi'
import rootReducer from '@/app/rootReducer'
import { SFMSInsightsPage } from '@/features/sfmsInsights/pages/SFMSInsightsPage'

const store = configureStore({
  reducer: rootReducer,
  middleware: getDefaultMiddleware => getDefaultMiddleware({ immutableCheck: false, serializableCheck: false })
})

createRoot(document.getElementById('root') as HTMLElement).render(
  <Provider store={store}>
    <CssBaseline />
    <ThemeProvider theme={theme}>
      <MemoryRouter>
        <SFMSInsightsPage />
      </MemoryRouter>
    </ThemeProvider>
  </Provider>
)
