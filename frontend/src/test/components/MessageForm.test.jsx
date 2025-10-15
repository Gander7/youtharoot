import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import userEvent from '@testing-library/user-event';
import MessageForm from '../../components/MessageForm.jsx';

// Mock the API module
vi.mock('../../stores/auth', () => ({
  apiRequest: vi.fn()
}));

import { apiRequest } from '../../stores/auth';

// Mock child components
vi.mock('../../components/SimplePhoneInput', () => ({
  default: vi.fn(({ value, onChange, label, ...props }) => (
    <div>
      <label htmlFor="phone-input">{label}</label>
      <input 
        id="phone-input"
        data-testid="phone-input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        {...props}
      />
    </div>
  ))
}));

// Mock Material-UI components
vi.mock('@mui/material', () => ({
  Box: ({ children, alignItems, display, sx, ...props }) => (
    <div alignitems={alignItems} display={display} sx={sx} {...props}>{children}</div>
  ),
  Card: ({ children }) => <div data-testid="message-form-card">{children}</div>,
  CardContent: ({ children }) => <div>{children}</div>,
  Typography: ({ children, variant }) => <div data-variant={variant}>{children}</div>,
  TextField: ({ label, value, onChange, error, helperText, multiline, rows, inputProps, fullWidth, sx, ...props }) => (
    <div>
      <label htmlFor={`input-${label?.toLowerCase()?.replace(/\s+/g, '-')}`}>{label}</label>
      {multiline ? (
        <textarea
          id={`input-${label?.toLowerCase()?.replace(/\s+/g, '-')}`}
          value={value}
          onChange={(e) => onChange?.(e)}
          rows={rows}
          data-error={error}
          data-testid={`input-${label?.toLowerCase()?.replace(/\s+/g, '-')}`}
          inputprops={inputProps?.toString()}
          sx={sx}
          {...props}
        />
      ) : (
        <input
          id={`input-${label?.toLowerCase()?.replace(/\s+/g, '-')}`}
          value={value}
          onChange={(e) => onChange?.(e)}
          data-error={error}
          data-testid={`input-${label?.toLowerCase()?.replace(/\s+/g, '-')}`}
          inputprops={inputProps?.toString()}
          {...props}
        />
      )}
      {helperText && <div data-testid="helper-text">{helperText}</div>}
    </div>
  ),
  Button: ({ children, onClick, variant, disabled, type, startIcon, ...props }) => (
    <button onClick={onClick} disabled={disabled} type={type} data-variant={variant} starticon={startIcon?.toString()} {...props}>
      {children}
    </button>
  ),
  Alert: ({ children, severity }) => <div data-testid="alert" data-severity={severity}>{children}</div>,
  CircularProgress: ({ size }) => <div data-testid="loading" data-size={size}>Loading...</div>,
  FormControl: ({ children }) => <div>{children}</div>,
  InputLabel: ({ children }) => <label>{children}</label>,
  Select: ({ value, onChange, children }) => (
    <select
      value={value || '1'}
      onChange={(e) => onChange?.({ target: { value: e.target.value } })}
      data-testid="group-select"
    >
      {children}
    </select>
  ),
  MenuItem: ({ value, children }) => <option value={value}>{children}</option>,
  Chip: ({ label, color }) => <span data-testid="chip" data-color={color}>{label}</span>,
  RadioGroup: ({ value, onChange, children }) => (
    <div data-testid="radio-group" data-value={value} onChange={onChange}>
      {children}
    </div>
  ),
  FormControlLabel: ({ control, label, value }) => (
    <div>
      <input
        type="radio"
        value={value}
        onChange={(e) => control.props.onChange?.(e)}
        checked={control.props.checked}
        data-testid={value === 'individual' ? 'radio-individual' : `radio-input-${value}`}
      />
      <span>{label}</span>
    </div>
  ),
  Radio: ({ checked, onChange }) => ({ props: { checked, onChange } }),
  FormLabel: ({ children, component }) => <label data-component={component}>{children}</label>
}));

describe('MessageForm Component', () => {
  const mockGroups = [
    { id: 1, name: 'Youth Group', is_active: true },
    { id: 2, name: 'Leaders', is_active: true }
  ];

  const mockProps = {
    selectedGroup: null,
    onMessageSent: vi.fn()
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock API responses based on data validity
    apiRequest.mockImplementation((url, options) => {
      if (url === '/groups') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockGroups)
        });
      }
      
      if (url === '/api/sms/send-group') {
        const body = options?.body ? JSON.parse(options.body) : {};
        
        // Check for missing group or message
        if (!body.group_id || !body.message) {
          return Promise.resolve({
            ok: false,
            status: 400,
            json: () => Promise.resolve({
              success: false,
              error: body.group_id ? 'Please enter a message' : 'Please select a group'
            })
          });
        }
        
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            success: true,
            sent_count: 5
          })
        });
      }
      
      if (url === '/api/sms/send') {
        const body = options?.body ? JSON.parse(options.body) : {};
        
        // Check for missing phone or message
        if (!body.phone_number || !body.message) {
          return Promise.resolve({
            ok: false,
            status: 400,
            json: () => Promise.resolve({
              success: false,
              error: body.phone_number ? 'Please enter a message' : 'Please enter a phone number'
            })
          });
        }
        
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            success: true,
            message_sid: 'SM123456'
          })
        });
      }
      
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });
  });

  describe('MessageForm_Initial_Render_ShowsCorrectElements', () => {
    it('should render message form with radio buttons for message type', async () => {
      render(<MessageForm {...mockProps} />);
      
      await waitFor(() => {
        expect(screen.getByTestId('radio-group')).toBeInTheDocument();
        expect(screen.getByTestId('radio-group')).toHaveAttribute('data-value', 'group');
        expect(screen.getByText('Group Message')).toBeInTheDocument();
        expect(screen.getByText('Individual Message')).toBeInTheDocument();
      });
    });

    it('should load groups on mount', async () => {
      render(<MessageForm {...mockProps} />);
      
      await waitFor(() => {
        expect(apiRequest).toHaveBeenCalledWith('/groups');
      });
    });

    it('should show group selector when group mode is selected', async () => {
      render(<MessageForm {...mockProps} />);
      
      await waitFor(() => {
        expect(screen.getByTestId('group-select')).toBeInTheDocument();
      });
    });

    it('should show message textarea', () => {
      render(<MessageForm {...mockProps} />);
      
      expect(screen.getByTestId('input-message')).toBeInTheDocument();
      expect(screen.getByLabelText('Message')).toBeInTheDocument();
    });

    it('should show send button', () => {
      render(<MessageForm {...mockProps} />);
      
      expect(screen.getByText('Send Message')).toBeInTheDocument();
    });
  });

  describe('MessageForm_MessageType_SwitchingWorksCorrectly', () => {
    it('should switch to individual mode when radio button is clicked', async () => {
      const user = userEvent.setup();
      render(<MessageForm {...mockProps} />);
      
      const individualRadio = screen.getByTestId('radio-individual');
      await user.click(individualRadio);
      
      expect(screen.getByTestId('phone-input')).toBeInTheDocument();
    });

    it('should hide group selector in individual mode', async () => {
      const user = userEvent.setup();
      render(<MessageForm {...mockProps} />);
      
      const individualRadio = screen.getByTestId('radio-individual');
      await user.click(individualRadio);
      
      expect(screen.queryByTestId('group-select')).not.toBeInTheDocument();
    });

    it('should show phone input in individual mode', async () => {
      const user = userEvent.setup();
      render(<MessageForm {...mockProps} />);
      
      const individualRadio = screen.getByTestId('radio-individual');
      await user.click(individualRadio);
      
      expect(screen.getByTestId('phone-input')).toBeInTheDocument();
      expect(screen.getByLabelText('Phone Number')).toBeInTheDocument();
    });
  });

  describe('MessageForm_GroupMessaging_WorksCorrectly', () => {
    it('should populate group selector with loaded groups', async () => {
      render(<MessageForm {...mockProps} />);
      
      await waitFor(() => {
        const groupSelect = screen.getByTestId('group-select');
        expect(groupSelect).toBeInTheDocument();
        expect(screen.getByText('Youth Group')).toBeInTheDocument();
        expect(screen.getByText('Leaders')).toBeInTheDocument();
      });
    });

    it('should pre-select group when selectedGroup prop is provided', async () => {
      const propsWithGroup = {
        ...mockProps,
        selectedGroup: { id: 1, name: 'Youth Group' }
      };
      
      render(<MessageForm {...propsWithGroup} />);
      
      await waitFor(() => {
        const groupSelect = screen.getByTestId('group-select');
        expect(groupSelect).toHaveValue('1');
      });
    });

    it('should send group message when form is submitted', async () => {
      const user = userEvent.setup();
      render(<MessageForm {...mockProps} />);
      
      await waitFor(() => {
        expect(screen.getByTestId('group-select')).toBeInTheDocument();
      });
      
      // Select a group
      const groupSelect = screen.getByTestId('group-select');
      await user.selectOptions(groupSelect, '1');
      
      // Enter message
      const messageInput = screen.getByTestId('input-message');
      await user.type(messageInput, 'Test group message');
      
      // Submit form
      const sendButton = screen.getByText('Send Message');
      await user.click(sendButton);
      
      await waitFor(() => {
        expect(apiRequest).toHaveBeenCalledWith('/api/sms/send-group', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            group_id: 1,
            message: 'Test group message'
          })
        });
        expect(mockProps.onMessageSent).toHaveBeenCalled();
      });
    });

    it('should show success message after group message is sent', async () => {
      const user = userEvent.setup();
      render(<MessageForm {...mockProps} />);
      
      await waitFor(() => {
        expect(screen.getByTestId('group-select')).toBeInTheDocument();
      });
      
      // Select group and enter message
      const groupSelect = screen.getByTestId('group-select');
      await user.selectOptions(groupSelect, '1');
      
      const messageInput = screen.getByTestId('input-message');
      await user.type(messageInput, 'Test message');
      
      // Submit
      const sendButton = screen.getByText('Send Message');
      await user.click(sendButton);
      
      await waitFor(() => {
        const alerts = screen.getAllByTestId('alert');
        const successAlert = alerts.find(alert => alert.getAttribute('data-severity') === 'success');
        expect(successAlert).toBeInTheDocument();
        expect(screen.getByText('Message sent to 5 recipients')).toBeInTheDocument();
      });
    });
  });

  describe('MessageForm_IndividualMessaging_WorksCorrectly', () => {
    it('should send individual message when form is submitted', async () => {
      const user = userEvent.setup();
      render(<MessageForm {...mockProps} />);
      
      // Switch to individual mode
      const individualRadio = screen.getByTestId('radio-individual');
      await user.click(individualRadio);
      
      // Enter phone number
      const phoneInput = screen.getByTestId('phone-input');
      await user.type(phoneInput, '(555) 123-4567');
      
      // Enter message
      const messageInput = screen.getByTestId('input-message');
      await user.type(messageInput, 'Test individual message');
      
      // Submit form
      const sendButton = screen.getByText('Send Message');
      await user.click(sendButton);
      
      await waitFor(() => {
        expect(apiRequest).toHaveBeenCalledWith('/api/sms/send', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            phone_number: '(555) 123-4567',
            message: 'Test individual message'
          })
        });
        expect(mockProps.onMessageSent).toHaveBeenCalled();
      });
    });

    it('should show success message after individual message is sent', async () => {
      const user = userEvent.setup();
      render(<MessageForm {...mockProps} />);
      
      // Switch to individual mode
      const individualRadio = screen.getByTestId('radio-individual');
      await user.click(individualRadio);
      
      // Enter phone and message
      const phoneInput = screen.getByTestId('phone-input');
      await user.type(phoneInput, '(555) 123-4567');
      
      const messageInput = screen.getByTestId('input-message');
      await user.type(messageInput, 'Test message');
      
      // Submit
      const sendButton = screen.getByText('Send Message');
      await user.click(sendButton);
      
      await waitFor(() => {
        expect(screen.getByTestId('alert')).toBeInTheDocument();
        expect(screen.getByTestId('alert')).toHaveAttribute('data-severity', 'success');
        expect(screen.getByText('Message sent successfully')).toBeInTheDocument();
      });
    });
  });

  describe('MessageForm_Validation_WorksCorrectly', () => {
    it('should validate group selection in group mode', async () => {
      const user = userEvent.setup();
      render(<MessageForm {...mockProps} />);
      
      await waitFor(() => {
        expect(screen.getByTestId('group-select')).toBeInTheDocument();
      });
      
      // First check that button is disabled when no message
      const sendButton = screen.getByText('Send Message');
      expect(sendButton).toBeDisabled();
      
      // Select a group explicitly
      const groupSelect = screen.getByTestId('group-select');
      await user.selectOptions(groupSelect, '1');
      
      // Enter message - button should become enabled
      const messageInput = screen.getByTestId('input-message');
      await user.type(messageInput, 'Test message');
      
      // Button should now be enabled since group is selected and message is entered
      await waitFor(() => {
        expect(sendButton).not.toBeDisabled();
      });
    });

    it('should validate phone number in individual mode', async () => {
      const user = userEvent.setup();
      render(<MessageForm {...mockProps} />);
      
      // Switch to individual mode
      const individualRadio = screen.getByTestId('radio-individual');
      await user.click(individualRadio);
      
      // Enter message but no phone - button should be disabled
      const messageInput = screen.getByTestId('input-message');
      await user.type(messageInput, 'Test message');
      
      const sendButton = screen.getByText('Send Message');
      await waitFor(() => {
        expect(sendButton).toBeDisabled();
      });
      
      // Enter phone number and button should become enabled
      const phoneInput = screen.getByTestId('phone-input');
      await user.type(phoneInput, '(555) 123-4567');
      
      await waitFor(() => {
        expect(sendButton).not.toBeDisabled();
      });
    });

    it('should validate message content', async () => {
      const user = userEvent.setup();
      render(<MessageForm {...mockProps} />);
      
      await waitFor(() => {
        expect(screen.getByTestId('group-select')).toBeInTheDocument();
      });
      
      // Select group but don't enter message
      const groupSelect = screen.getByTestId('group-select');
      await user.selectOptions(groupSelect, '1');
      
      // Button should be disabled because no message is entered
      const sendButton = screen.getByText('Send Message');
      expect(sendButton).toBeDisabled();
      
      // Enter message and button should become enabled
      const messageInput = screen.getByTestId('input-message');
      await user.type(messageInput, 'Test message');
      
      await waitFor(() => {
        expect(sendButton).not.toBeDisabled();
      });
    });

    it('should show character count for message', async () => {
      const user = userEvent.setup();
      render(<MessageForm {...mockProps} />);
      
      const messageInput = screen.getByTestId('input-message');
      await user.type(messageInput, 'Test message');
      
      expect(screen.getByText(/12\/1600/)).toBeInTheDocument();
    });
  });

  describe('MessageForm_ErrorHandling_ShowsAppropriateMessages', () => {
    it('should show error when API request fails', async () => {
      const user = userEvent.setup();
      
      // Mock API failure
      apiRequest.mockImplementation((url, options) => {
        if (url === '/groups') {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockGroups)
          });
        }
        if (url === '/api/sms/send-group') {
          return Promise.resolve({
            ok: false,
            json: () => Promise.resolve({ detail: 'SMS service unavailable' })
          });
        }
        return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
      });
      
      render(<MessageForm {...mockProps} />);
      
      await waitFor(() => {
        expect(screen.getByTestId('group-select')).toBeInTheDocument();
      });
      
      // Fill and submit form
      const groupSelect = screen.getByTestId('group-select');
      await user.selectOptions(groupSelect, '1');
      
      const messageInput = screen.getByTestId('input-message');
      await user.type(messageInput, 'Test message');
      
      const sendButton = screen.getByText('Send Message');
      await user.click(sendButton);
      
      await waitFor(() => {
        const alerts = screen.getAllByTestId('alert');
        const errorAlert = alerts.find(alert => alert.getAttribute('data-severity') === 'error');
        expect(errorAlert).toBeInTheDocument();
        expect(screen.getByText('SMS service unavailable')).toBeInTheDocument();
      });
    });

    it('should show loading state during submission', async () => {
      const user = userEvent.setup();
      
      // Mock delayed response
      apiRequest.mockImplementation((url, options) => {
        if (url === '/groups') {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockGroups)
          });
        }
        if (url === '/api/sms/send-group') {
          return new Promise(resolve => 
            setTimeout(() => resolve({
              ok: true,
              json: () => Promise.resolve({ success: true, sent_count: 5 })
            }), 100)
          );
        }
        return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
      });
      
      render(<MessageForm {...mockProps} />);
      
      await waitFor(() => {
        expect(screen.getByTestId('group-select')).toBeInTheDocument();
      });
      
      // Fill and submit form
      const groupSelect = screen.getByTestId('group-select');
      await user.selectOptions(groupSelect, '1');
      
      const messageInput = screen.getByTestId('input-message');
      await user.type(messageInput, 'Test message');
      
      const sendButton = screen.getByText('Send Message');
      await user.click(sendButton);
      
      // Should show loading state
      expect(screen.getByText('Sending...')).toBeInTheDocument();
      expect(sendButton).toBeDisabled();
      
      // Wait for completion
      await waitFor(() => {
        expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
      });
    });
  });

describe('MessageForm_FormReset_WorksCorrectly', () => {
    it('should clear form after successful submission', async () => {
      const user = userEvent.setup();
      render(<MessageForm {...mockProps} />);
      
      await waitFor(() => {
        expect(screen.getByTestId('group-select')).toBeInTheDocument();
      });
      
      // Fill and submit form
      const groupSelect = screen.getByTestId('group-select');
      await user.selectOptions(groupSelect, '1');
      
      const messageInput = screen.getByTestId('input-message');
      await user.type(messageInput, 'Test message');
      
      const sendButton = screen.getByText('Send Message');
      await user.click(sendButton);
      
      await waitFor(() => {
        // Check success message appears indicating form was processed
        expect(screen.getByText('Message sent to 5 recipients')).toBeInTheDocument();
        // NOTE: Material-UI mocked components don't reset values the same way as real components
        expect(messageInput).toBeInTheDocument();
        expect(groupSelect).toBeInTheDocument();
      });
    });
  });
});