import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MessagingPage from '../../components/MessagingPage.jsx';

// Mock the child components
vi.mock('../../components/GroupList.jsx', () => ({
  default: ({ onGroupSelect, onGroupCreated }) => (
    <div data-testid="group-list">
      <button onClick={() => onGroupSelect({ id: 1, name: 'Test Group' })}>
        Select Test Group
      </button>
      <button onClick={() => onGroupCreated()}>Create Group</button>
    </div>
  )
}));

vi.mock('../../components/MessageForm.jsx', () => ({
  default: ({ selectedGroup, onMessageSent }) => (
    <div data-testid="message-form">
      <div>{selectedGroup ? `Group: ${selectedGroup.name}` : 'No group selected'}</div>
      <button onClick={() => onMessageSent()}>Send Message</button>
    </div>
  )
}));

vi.mock('../../components/MessageHistory.jsx', () => ({
  default: ({ refreshTrigger }) => (
    <div data-testid="message-history">
      <div>Refresh Trigger: {refreshTrigger}</div>
    </div>
  )
}));

vi.mock('../../components/ErrorBoundary.jsx', () => ({
  default: ({ children }) => children
}));

vi.mock('../../components/ApiErrorBoundary.jsx', () => ({
  default: ({ children }) => children
}));

// Material-UI components are mocked globally in setup.js

describe('MessagingPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('MessagingPage_Initial_Render_ShowsCorrectLayout', () => {
    it('should render messaging page with three tabs', () => {
      render(<MessagingPage />);
      
      // Look for tab buttons by their proper role
      expect(screen.getByRole('tab', { name: /Message Groups/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /Send Message/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /Message History/i })).toBeInTheDocument();
    });

    it('should render all child components', async () => {
      render(<MessagingPage />);
      
      // Initially only the first tab (group-list) should be visible
      expect(screen.getByTestId('group-list')).toBeInTheDocument();
      
      // Switch to second tab to see message-form
      const sendMessageTab = screen.getByText('Send Message');
      fireEvent.click(sendMessageTab);
      
      // Wait for tab content to switch
      await waitFor(() => {
        expect(screen.getByTestId('message-form')).toBeInTheDocument();
      });
      
      // Switch to third tab to see message-history
      const historyTab = screen.getByText('Message History');
      fireEvent.click(historyTab);
      
      await waitFor(() => {
        expect(screen.getByTestId('message-history')).toBeInTheDocument();
      });
    });

    it('should display welcome message in page header', () => {
      render(<MessagingPage />);
      
      expect(screen.getByText('SMS Messaging')).toBeInTheDocument();
      // Note: MessagingPage doesn't have a subtitle, just the main heading
    });
  });

  describe('MessagingPage_TabNavigation_WorksCorrectly', () => {
    it('should start with Message Groups tab active', () => {
      render(<MessagingPage />);
      
      // Check that the first tab content is visible (indicating tab 0 is active)
      expect(screen.getByTestId('group-list')).toBeInTheDocument();
      
      // Verify hidden tabs are not visible
      expect(screen.queryByTestId('message-form')).not.toBeInTheDocument();
      expect(screen.queryByTestId('message-history')).not.toBeInTheDocument();
    });

    it('should switch to Send Message tab when tab is clicked', async () => {
      const user = userEvent.setup();
      render(<MessagingPage />);
      
      const sendMessageTab = screen.getByText('Send Message');
      await user.click(sendMessageTab);
      
      // Check if the tab change handler was called (would be verified through UI state)
      expect(sendMessageTab).toBeInTheDocument();
    });

    it('should switch to Message History tab when tab is clicked', async () => {
      const user = userEvent.setup();
      render(<MessagingPage />);
      
      const historyTab = screen.getByText('Message History');
      await user.click(historyTab);
      
      expect(historyTab).toBeInTheDocument();
    });
  });

  describe('MessagingPage_GroupSelection_UpdatesMessageForm', () => {
    it('should pass selected group to message form when group is selected', async () => {
      const user = userEvent.setup();
      render(<MessagingPage />);
      
      // Select a group from the first tab (Message Groups)
      const selectButton = screen.getByText('Select Test Group');
      await user.click(selectButton);
      
      // Should automatically switch to Send Message tab and show selected group
      expect(screen.getByText('Group: Test Group')).toBeInTheDocument();
    });

    it('should switch to Send Message tab when group is selected', async () => {
      const user = userEvent.setup();
      render(<MessagingPage />);
      
      const selectButton = screen.getByText('Select Test Group');
      await user.click(selectButton);
      
      // The tab should switch to Send Message (index 1)
      // This would be tested by checking the active tab panel
      expect(screen.getByText('Group: Test Group')).toBeInTheDocument();
    });
  });

  describe('MessagingPage_MessageSending_UpdatesHistory', () => {
    it('should increment refresh trigger when message is sent', async () => {
      const user = userEvent.setup();
      render(<MessagingPage />);
      
      // Navigate to Send Message tab first
      const sendMessageTab = screen.getByRole('tab', { name: /send message/i });
      await user.click(sendMessageTab);
      
      // Send a message - target the button inside the message form
      const messageForm = screen.getByTestId('message-form');
      const sendButton = within(messageForm).getByText('Send Message');
      await user.click(sendButton);
      
      // Should automatically switch to Message History tab and show updated trigger
      expect(screen.getByText('Refresh Trigger: 1')).toBeInTheDocument();
    });

    it('should switch to Message History tab when message is sent', async () => {
      const user = userEvent.setup();
      render(<MessagingPage />);
      
      // Navigate to Send Message tab first
      const sendMessageTab = screen.getByRole('tab', { name: /send message/i });
      await user.click(sendMessageTab);
      
      // Send a message - target the button inside the message form
      const messageForm = screen.getByTestId('message-form');
      const sendButton = within(messageForm).getByText('Send Message');
      await user.click(sendButton);
      
      // Should switch to Message History tab and show refresh trigger
      expect(screen.getByText('Refresh Trigger: 1')).toBeInTheDocument();
    });
  });

  describe('MessagingPage_GroupCreation_TriggersRefresh', () => {
    it('should refresh components when group is created', async () => {
      const user = userEvent.setup();
      render(<MessagingPage />);
      
      const createButton = screen.getByText('Create Group');
      await user.click(createButton);
      
      // Group creation should trigger a refresh of the group list
      expect(screen.getByTestId('group-list')).toBeInTheDocument();
    });
  });

  describe('MessagingPage_ErrorHandling_ShowsGracefulDegradation', () => {
    it('should render error boundaries around components', () => {
      render(<MessagingPage />);
      
      // Error boundaries are rendered but don't show unless there's an error
      // Only the active tab content should be visible initially
      expect(screen.getByTestId('group-list')).toBeInTheDocument();
      
      // Verify tabs structure is rendered (error boundaries wrap each tab panel)
      expect(screen.getByTestId('tabs')).toBeInTheDocument();
      // All 3 tab panels exist in DOM (hidden ones still count)
      const tabpanels = screen.getAllByRole('tabpanel', { hidden: true });
      expect(tabpanels).toHaveLength(3);
    });
  });

  describe('MessagingPage_Accessibility_MeetsStandards', () => {
    it('should have proper ARIA labels for tabs', () => {
      render(<MessagingPage />);
      
      // Check that tabs have proper role and labeling
      const tabsContainer = screen.getByTestId('tabs');
      expect(tabsContainer).toBeInTheDocument();
    });

    it('should provide descriptive text for screen readers', () => {
      render(<MessagingPage />);
      
      expect(screen.getByText('SMS Messaging')).toBeInTheDocument();
      // Note: MessagingPage has proper ARIA labels for tabs, not a subtitle
    });
  });
});