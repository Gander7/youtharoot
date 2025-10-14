import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PersonList from '../../components/PersonList.jsx';

// Mock the API module
vi.mock('../../stores/auth', () => ({
  apiRequest: vi.fn()
}));

// Mock Material-UI ThemeProvider
vi.mock('@mui/material/styles', () => ({
  ThemeProvider: ({ children }) => children,
  createTheme: () => ({})
}));

import { apiRequest } from '../../stores/auth';

describe('PersonList Component - SMS Opt-Out Features', () => {
  beforeEach(() => {
    // Reset all mocks before each test
    vi.clearAllMocks();
    
    // Mock successful API responses by default
    apiRequest.mockImplementation((url) => {
      if (url === '/person/youth') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([
            {
              id: 1,
              first_name: 'Alex',
              last_name: 'Johnson',
              phone_number: '+14165551234',
              sms_opt_out: false,
              grade: 10,
              type: 'youth'
            }
          ])
        });
      }
      if (url === '/person/leaders') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([
            {
              id: 2,
              first_name: 'Sarah',
              last_name: 'Wilson',
              phone_number: '+14165555678',
              sms_opt_out: true,
              role: 'Youth Pastor',
              type: 'leader'
            }
          ])
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });
  });

  describe('Basic Component Rendering', () => {
    it('should render the PersonList component', async () => {
      render(<PersonList />);
      
      expect(screen.getByText('People')).toBeInTheDocument();
      expect(screen.getByText('Add Youth')).toBeInTheDocument();
      expect(screen.getByText('Add Leader')).toBeInTheDocument();
    });

    it('should display existing persons with phone numbers', async () => {
      render(<PersonList />);
      
      // Wait for API data to load
      await waitFor(() => {
        expect(screen.getByText('Alex Johnson')).toBeInTheDocument();
      });
      
      // Check if phone number is displayed
      await waitFor(() => {
        expect(screen.getByText('📱 +14165551234')).toBeInTheDocument();
      });
    });

    it('should show different counts for youth and leaders', async () => {
      render(<PersonList />);
      
      await waitFor(() => {
        expect(screen.getByText(/Youth \(1\)/)).toBeInTheDocument();
        expect(screen.getByText(/Leaders \(1\)/)).toBeInTheDocument();
      });
    });
  });

  describe('Add Youth Dialog', () => {
    it('should open add youth dialog when button is clicked', async () => {
      const user = userEvent.setup();
      render(<PersonList />);
      
      // Click the first "Add Youth" button (not the submit button in the dialog)
      const addYouthButtons = screen.getAllByText('Add Youth');
      await user.click(addYouthButtons[0]); // Click the first one (the main button)
      
      // Dialog should open with form fields
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
        // Check for dialog title instead of all "Add Youth" text
        expect(screen.getByRole('heading', { name: /Add Youth/i })).toBeInTheDocument();
      });
    });
  });

  describe('Phone Number Validation Features', () => {
    it('should show tel input type when dialog is open', async () => {
      const user = userEvent.setup();
      render(<PersonList />);
      
      const addYouthButtons = screen.getAllByText('Add Youth');
      await user.click(addYouthButtons[0]); // Click the main button
      
      await waitFor(() => {
        const phoneInputs = screen.getAllByDisplayValue('');
        const phoneInput = phoneInputs.find(input => 
          input.getAttribute('type') === 'tel' && 
          input.getAttribute('placeholder') === '(416) 555-1234'
        );
        expect(phoneInput).toBeInTheDocument();
      });
    });

    it('should have Canadian phone pattern validation', async () => {
      const user = userEvent.setup();
      render(<PersonList />);
      
      const addYouthButtons = screen.getAllByText('Add Youth');
      await user.click(addYouthButtons[0]); // Click the main button
      
      await waitFor(() => {
        const phoneInputs = screen.getAllByDisplayValue('');
        const phoneInput = phoneInputs.find(input => 
          input.getAttribute('pattern')?.includes('\\+?1[\\-\\s]?')
        );
        expect(phoneInput).toBeInTheDocument();
      });
    });

    it('should show helpful text for Canadian format', async () => {
      const user = userEvent.setup();
      render(<PersonList />);
      
      const addYouthButtons = screen.getAllByText('Add Youth');
      await user.click(addYouthButtons[0]); // Click the main button
      
      await waitFor(() => {
        // Use getAllByText since there are multiple instances (phone and emergency contact)
        const helpTexts = screen.getAllByText(/Canadian format: \(416\) 555-1234/);
        expect(helpTexts.length).toBeGreaterThan(0); // At least one should exist
        expect(helpTexts[0]).toBeInTheDocument();
      });
    });
  });

  describe('SMS Opt-Out Checkbox Logic', () => {
    it('should conditionally show SMS opt-out checkbox', async () => {
      const user = userEvent.setup();
      render(<PersonList />);
      
      const addYouthButtons = screen.getAllByText('Add Youth');
      await user.click(addYouthButtons[0]); // Click the main button
      
      // Initially, no phone number means no opt-out checkbox
      await waitFor(() => {
        expect(screen.queryByText(/Opt out of SMS notifications/)).not.toBeInTheDocument();
      });
      
      // Find and type in phone input
      const phoneInputs = screen.getAllByDisplayValue('');
      const phoneInput = phoneInputs.find(input => 
        input.getAttribute('placeholder') === '(416) 555-1234'
      );
      
      if (phoneInput) {
        await user.type(phoneInput, '4165551234');
        
        // Now the opt-out checkbox should appear
        await waitFor(() => {
          expect(screen.getByText(/Opt out of SMS notifications/)).toBeInTheDocument();
        });
      }
    });
  });

  describe('API Integration', () => {
    it('should handle API errors gracefully', async () => {
      // Mock API to fail
      apiRequest.mockImplementation(() => {
        throw new Error('Network error');
      });
      
      render(<PersonList />);
      
      // Component should still render even with API errors
      expect(screen.getByText('People')).toBeInTheDocument();
      expect(screen.getByText('Add Youth')).toBeInTheDocument();
    });

    it('should call youth API endpoint on mount', async () => {
      render(<PersonList />);
      
      await waitFor(() => {
        expect(apiRequest).toHaveBeenCalledWith('/person/youth');
      });
    });

    it('should call leaders API endpoint on mount', async () => {
      render(<PersonList />);
      
      await waitFor(() => {
        expect(apiRequest).toHaveBeenCalledWith('/person/leaders');
      });
    });
  });

  describe('Search and Filter Functionality', () => {
    it('should have search input', () => {
      render(<PersonList />);
      
      const searchInput = screen.getByPlaceholderText('Search people...');
      expect(searchInput).toBeInTheDocument();
    });

    it('should have toggle buttons for youth and leaders', async () => {
      render(<PersonList />);
      
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Youth \(1\)/ })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Leaders \(1\)/ })).toBeInTheDocument();
      });
    });
  });
});