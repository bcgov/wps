import rootReducer, { RootState } from '@/app/rootReducer'
import { configureStore } from '@reduxjs/toolkit'

export const createTestStore = (initialState: Partial<RootState> = {}) => {
  return configureStore({
    reducer: rootReducer,
    preloadedState: {
      ...initialState
    }
  })
}

export const createLayerMock = (name: string) => {
  const mockSource = {
    on: vi.fn(),
    un: vi.fn(),
    once: vi.fn()
  }
  return {
    set: vi.fn(),
    setStyle: vi.fn(),
    changed: vi.fn(),
    getProperties: vi.fn(() => ({ name })),
    setVisible: vi.fn(),
    setSource: vi.fn(),
    getSource: vi.fn(() => mockSource),
    getZIndex: vi.fn(() => 52),
    getMinZoom: vi.fn(() => 0),
    on: vi.fn(),
    un: vi.fn(),
    once: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn()
  }
}
