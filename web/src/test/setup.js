import '@testing-library/jest-dom'

// Mock API base URL for tests
global.API_BASE_URL = 'http://localhost:8000'

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
global.localStorage = localStorageMock

// Mock fetch for API calls
global.fetch = vi.fn()

// Reset mocks before each test
beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
})