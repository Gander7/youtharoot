/**
 * Test suite for GroupMemberManager component
 * Following TDD methodology - tests written before implementation
 * 
 * Component responsibilities:
 * - Display current group members
 * - Allow adding individual people to group
 * - Allow removing people from group
 * - Support bulk adding multiple people
 * - Handle API errors gracefully
 * - Show loading states appropriately
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Mock the auth store before importing the component
vi.mock('../../stores/auth', () => ({
  apiRequest: vi.fn()
}));

// Mock MUI icons
vi.mock('@mui/icons-material', () => ({
  Delete: () => 'Delete',
  PersonAdd: () => 'PersonAdd',
  Search: () => 'Search',
  Close: () => 'Close'
}));

import GroupMemberManager from '../../components/GroupMemberManager';
import { apiRequest } from '../../stores/auth';

describe('GroupMemberManager Component', () => {
  const mockGroup = {
    id: 1,
    name: 'Test Group',
    description: 'Test Description',
    member_count: 2
  };

  const mockMembers = [
    {
      id: 1,
      person_id: 101,
      person: {
        id: 101,
        first_name: 'John',
        last_name: 'Doe',
        person_type: 'youth',
        phone_number: '+1234567890'
      },
      joined_at: '2024-01-15T10:00:00Z'
    },
    {
      id: 2,
      person_id: 102,
      person: {
        id: 102,
        first_name: 'Jane',
        last_name: 'Smith',
        person_type: 'leader',
        phone_number: '+1987654321'
      },
      joined_at: '2024-01-16T11:00:00Z'
    }
  ];

  const mockAvailablePeople = [
    {
      id: 103,
      first_name: 'Bob',
      last_name: 'Johnson',
      person_type: 'youth',
      phone_number: '+1555555555'
    },
    {
      id: 104,
      first_name: 'Alice',
      last_name: 'Williams',
      person_type: 'leader',
      phone_number: '+1666666666'
    }
  ];

  const defaultProps = {
    open: true,
    onClose: vi.fn(),
    group: mockGroup,
    onMembershipChange: vi.fn()
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Default API responses
    apiRequest.mockImplementation((url) => {
      if (url === `/groups/${mockGroup.id}/members`) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockMembers)
        });
      }
      if (url === '/persons') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockAvailablePeople.concat(mockMembers.map(m => m.person)))
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
    });
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render dialog when open is true', async () => {
      render(<GroupMemberManager {...defaultProps} />);
      
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('Manage Members - Test Group')).toBeInTheDocument();
    });

    it('should not render dialog when open is false', () => {
      render(<GroupMemberManager {...defaultProps} open={false} />);
      
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('should display loading state initially', () => {
      render(<GroupMemberManager {...defaultProps} />);
      
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });
  });

  describe('Member List Display', () => {
    it('should load and display current group members', async () => {
      render(<GroupMemberManager {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
        expect(screen.getByText('Jane Smith')).toBeInTheDocument();
      });
      
      // Verify API call
      expect(apiRequest).toHaveBeenCalledWith(`/groups/${mockGroup.id}/members`);
    });

    it('should display member details correctly', async () => {
      render(<GroupMemberManager {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      // Check person type badges
      expect(screen.getByText('Youth')).toBeInTheDocument();
      expect(screen.getByText('Leader')).toBeInTheDocument();
      
      // Check phone numbers are displayed
      expect(screen.getByText('+1234567890')).toBeInTheDocument();
      expect(screen.getByText('+1987654321')).toBeInTheDocument();
    });

    it('should show empty state when no members exist', async () => {
      apiRequest.mockImplementation((url) => {
        if (url === `/groups/${mockGroup.id}/members`) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve([])
          });
        }
        if (url === '/persons') {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockAvailablePeople)
          });
        }
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
      });

      render(<GroupMemberManager {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('No members in this group yet.')).toBeInTheDocument();
      });
    });
  });

  describe('Adding Members', () => {
    it('should show available people for adding', async () => {
      render(<GroupMemberManager {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      // Click Add Member button
      const addButton = screen.getByText('Add Member');
      fireEvent.click(addButton);
      
      await waitFor(() => {
        expect(screen.getByText('Bob Johnson')).toBeInTheDocument();
        expect(screen.getByText('Alice Williams')).toBeInTheDocument();
      });
    });

    it('should filter out existing members from available people', async () => {
      render(<GroupMemberManager {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      const addButton = screen.getByText('Add Member');
      fireEvent.click(addButton);
      
      await waitFor(() => {
        // Should show available people
        expect(screen.getByText('Bob Johnson')).toBeInTheDocument();
        expect(screen.getByText('Alice Williams')).toBeInTheDocument();
        
        // Should NOT show existing members in the add dialog
        const addDialog = screen.getByRole('dialog', { name: /add member/i });
        expect(within(addDialog).queryByText('John Doe')).not.toBeInTheDocument();
        expect(within(addDialog).queryByText('Jane Smith')).not.toBeInTheDocument();
      });
    });

    it('should add single member successfully', async () => {
      const user = userEvent.setup();
      
      apiRequest.mockImplementation((url, options) => {
        if (url === `/groups/${mockGroup.id}/members` && options?.method === 'POST') {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              id: 3,
              person_id: 103,
              person: mockAvailablePeople[0],
              joined_at: '2024-01-17T12:00:00Z'
            })
          });
        }
        // Return default responses for other calls
        return apiRequest.getMockImplementation()(url, options);
      });

      render(<GroupMemberManager {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      // Click Add Member
      const addButton = screen.getByText('Add Member');
      await user.click(addButton);
      
      // Select a person
      await waitFor(() => {
        expect(screen.getByText('Bob Johnson')).toBeInTheDocument();
      });
      
      const bobOption = screen.getByText('Bob Johnson');
      await user.click(bobOption);
      
      // Confirm addition
      const confirmButton = screen.getByText('Add Selected');
      await user.click(confirmButton);
      
      // Verify API call
      await waitFor(() => {
        expect(apiRequest).toHaveBeenCalledWith(
          `/groups/${mockGroup.id}/members`,
          expect.objectContaining({
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ person_id: 103 })
          })
        );
      });
      
      // Verify callback
      expect(defaultProps.onMembershipChange).toHaveBeenCalled();
    });

    it('should handle bulk member addition', async () => {
      const user = userEvent.setup();
      
      apiRequest.mockImplementation((url, options) => {
        if (url === `/groups/${mockGroup.id}/members/bulk` && options?.method === 'POST') {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              added: 2,
              skipped: 0,
              errors: []
            })
          });
        }
        return apiRequest.getMockImplementation()(url, options);
      });

      render(<GroupMemberManager {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      // Click Add Member
      const addButton = screen.getByText('Add Member');
      await user.click(addButton);
      
      // Select multiple people
      await waitFor(() => {
        expect(screen.getByText('Bob Johnson')).toBeInTheDocument();
      });
      
      const bobCheckbox = screen.getByRole('checkbox', { name: /bob johnson/i });
      const aliceCheckbox = screen.getByRole('checkbox', { name: /alice williams/i });
      
      await user.click(bobCheckbox);
      await user.click(aliceCheckbox);
      
      // Confirm bulk addition
      const confirmButton = screen.getByText('Add Selected');
      await user.click(confirmButton);
      
      // Verify bulk API call
      await waitFor(() => {
        expect(apiRequest).toHaveBeenCalledWith(
          `/groups/${mockGroup.id}/members/bulk`,
          expect.objectContaining({
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ person_ids: [103, 104] })
          })
        );
      });
    });
  });

  describe('Removing Members', () => {
    it('should display remove buttons for each member', async () => {
      render(<GroupMemberManager {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });
      
      // Should have remove buttons for each member
      const removeButtons = screen.getAllByLabelText(/remove.*from group/i);
      expect(removeButtons).toHaveLength(2);
    });

    it('should remove member successfully', async () => {
      const user = userEvent.setup();
      
      apiRequest.mockImplementation((url, options) => {
        if (url === `/groups/${mockGroup.id}/members/101` && options?.method === 'DELETE') {
          return Promise.resolve({ ok: true });
        }
        return apiRequest.getMockImplementation()(url, options);
      });

      // Mock window.confirm
      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);

      render(<GroupMemberManager {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });
      
      // Click remove button for John Doe
      const removeButtons = screen.getAllByLabelText(/remove.*from group/i);
      await user.click(removeButtons[0]);
      
      // Verify confirmation dialog
      expect(confirmSpy).toHaveBeenCalledWith('Remove John Doe from Test Group?');
      
      // Verify API call
      await waitFor(() => {
        expect(apiRequest).toHaveBeenCalledWith(
          `/groups/${mockGroup.id}/members/101`,
          { method: 'DELETE' }
        );
      });
      
      // Verify callback
      expect(defaultProps.onMembershipChange).toHaveBeenCalled();
      
      confirmSpy.mockRestore();
    });

    it('should not remove member if user cancels confirmation', async () => {
      const user = userEvent.setup();
      
      // Mock window.confirm to return false
      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);

      render(<GroupMemberManager {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });
      
      // Click remove button
      const removeButtons = screen.getAllByLabelText(/remove.*from group/i);
      await user.click(removeButtons[0]);
      
      // Should not make API call since user cancelled
      expect(apiRequest).not.toHaveBeenCalledWith(
        expect.stringContaining('/members/'),
        expect.objectContaining({ method: 'DELETE' })
      );
      
      confirmSpy.mockRestore();
    });
  });

  describe('Error Handling', () => {
    it('should display error when loading members fails', async () => {
      apiRequest.mockImplementation((url) => {
        if (url === `/groups/${mockGroup.id}/members`) {
          return Promise.resolve({
            ok: false,
            status: 500,
            json: () => Promise.resolve({ detail: 'Server error' })
          });
        }
        return apiRequest.getMockImplementation()(url);
      });

      render(<GroupMemberManager {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Failed to load group members')).toBeInTheDocument();
      });
    });

    it('should display error when adding member fails', async () => {
      const user = userEvent.setup();
      
      apiRequest.mockImplementation((url, options) => {
        if (url === `/groups/${mockGroup.id}/members` && options?.method === 'POST') {
          return Promise.resolve({
            ok: false,
            status: 400,
            json: () => Promise.resolve({ detail: 'Person already in group' })
          });
        }
        return apiRequest.getMockImplementation()(url, options);
      });

      render(<GroupMemberManager {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      // Try to add member
      const addButton = screen.getByText('Add Member');
      await user.click(addButton);
      
      await waitFor(() => {
        expect(screen.getByText('Bob Johnson')).toBeInTheDocument();
      });
      
      const bobOption = screen.getByText('Bob Johnson');
      await user.click(bobOption);
      
      const confirmButton = screen.getByText('Add Selected');
      await user.click(confirmButton);
      
      // Should display error
      await waitFor(() => {
        expect(screen.getByText('Person already in group')).toBeInTheDocument();
      });
    });

    it('should display error when removing member fails', async () => {
      const user = userEvent.setup();
      
      apiRequest.mockImplementation((url, options) => {
        if (url === `/groups/${mockGroup.id}/members/101` && options?.method === 'DELETE') {
          return Promise.resolve({
            ok: false,
            status: 500,
            json: () => Promise.resolve({ detail: 'Database error' })
          });
        }
        return apiRequest.getMockImplementation()(url, options);
      });

      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);

      render(<GroupMemberManager {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });
      
      // Try to remove member
      const removeButtons = screen.getAllByLabelText(/remove.*from group/i);
      await user.click(removeButtons[0]);
      
      // Should display error
      await waitFor(() => {
        expect(screen.getByText('Failed to remove member')).toBeInTheDocument();
      });
      
      confirmSpy.mockRestore();
    });
  });

  describe('Dialog Management', () => {
    it('should call onClose when dialog is closed', async () => {
      const user = userEvent.setup();
      
      render(<GroupMemberManager {...defaultProps} />);
      
      const closeButton = screen.getByText('Close');
      await user.click(closeButton);
      
      expect(defaultProps.onClose).toHaveBeenCalled();
    });

    it('should call onClose when clicking outside dialog', async () => {
      render(<GroupMemberManager {...defaultProps} />);
      
      // Click on backdrop
      const dialog = screen.getByRole('dialog');
      fireEvent.click(dialog.parentElement);
      
      expect(defaultProps.onClose).toHaveBeenCalled();
    });
  });
});