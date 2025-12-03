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

export const baseLayerMock = {
  set: vi.fn(),
  setStyle: vi.fn(),
  changed: vi.fn(),
  getProperties: vi.fn(() => ({})),
  setVisible: vi.fn(),
  setSource: vi.fn(),
  on: vi.fn(),
  un: vi.fn(),
  once: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
};

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
    removeEventListener: vi.fn(),
  };
};
