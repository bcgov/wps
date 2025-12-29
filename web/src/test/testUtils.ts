import rootReducer, { RootState } from '@/app/rootReducer'
import { configureStore, Reducer } from '@reduxjs/toolkit'

export const createTestStore = <S = RootState>(
  initialState?: S,
  reducer: Reducer<S> = rootReducer as Reducer<S>
) => {
  return configureStore({
    reducer,
    preloadedState: initialState,
    middleware: getDefaultMiddleware =>
      getDefaultMiddleware({
        immutableCheck: false,
        serializableCheck: false
      })
  })
}

export const createLayerMock = (name: string) => {
  return {
    set: vi.fn(),
    setStyle: vi.fn(),
    changed: vi.fn(),
    getProperties: vi.fn(() => ({ name })),
    setVisible: vi.fn(),
    setSource: vi.fn(),
    on: vi.fn(),
    un: vi.fn(),
    once: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn()
  }
}
