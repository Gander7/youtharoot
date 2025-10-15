import '@testing-library/jest-dom'
import React from 'react'
import { vi } from 'vitest'

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

// Centralized Material-UI mock components
const createMockComponent = (componentName, specialProps = []) => {
  return ({ children, helperText, label, ...props }) => {
    const testId = componentName.toLowerCase();
    const displayProps = { ...props };
    
    // Add aria-label for TextField components to improve accessibility testing
    if (componentName === 'TextField' && label) {
      displayProps['aria-label'] = label;
    }
    
    const result = React.createElement('div', 
      { 'data-testid': testId, ...displayProps },
      children,
      helperText && React.createElement('div', 
        { 'data-testid': `${testId}-helpertext` }, 
        helperText
      )
    );
    return result;
  };
};

// Mock @mui/material components
vi.mock('@mui/material', () => ({
  Alert: createMockComponent('Alert'),
  AlertTitle: createMockComponent('AlertTitle'),
  Alert: createMockComponent('Alert'),
  AppBar: createMockComponent('AppBar'),
  Autocomplete: createMockComponent('Autocomplete'),
  Avatar: createMockComponent('Avatar'),
  Box: createMockComponent('Box'),
  Button: ({ children, onClick, type, ...props }) => {
    // Use actual button element if it's a submit button to enable form submission
    const Element = type === 'submit' ? 'button' : 'div';
    return React.createElement(Element, {
      'data-testid': 'button',
      onClick,
      type: type === 'submit' ? 'submit' : undefined,
      ...props
    }, children);
  },
  Card: createMockComponent('Card'),
  CardActions: createMockComponent('CardActions'),
  CardContent: createMockComponent('CardContent'),
  CardHeader: createMockComponent('CardHeader'),
  Checkbox: createMockComponent('Checkbox'),
  Chip: ({ label, color, icon, variant, size, ...props }) => React.createElement('div', 
    { 'data-testid': 'chip', color, icon, variant, size, ...props },
    label
  ),
  CircularProgress: createMockComponent('CircularProgress'),
  Container: ({ children, maxWidth, ...props }) => {
    // Filter out Material-UI specific props to avoid DOM warnings
    const { gutterBottom, ...domProps } = props;
    return React.createElement('div', { 'data-testid': 'container', maxwidth: maxWidth, ...domProps }, children);
  },
  Dialog: createMockComponent('Dialog'),
  DialogActions: createMockComponent('DialogActions'),
  DialogContent: createMockComponent('DialogContent'),
  DialogTitle: createMockComponent('DialogTitle'),
  Divider: createMockComponent('Divider'),
  Fab: createMockComponent('Fab'),
  FormControl: createMockComponent('FormControl'),
  FormControlLabel: createMockComponent('FormControlLabel'),
  FormLabel: createMockComponent('FormLabel'),
  Grid: createMockComponent('Grid'),
  IconButton: createMockComponent('IconButton'),
  InputAdornment: createMockComponent('InputAdornment'),
  InputLabel: createMockComponent('InputLabel'),
  LinearProgress: createMockComponent('LinearProgress'),
  List: createMockComponent('List'),
  ListItem: createMockComponent('ListItem'),
  ListItemAvatar: createMockComponent('ListItemAvatar'),
  ListItemIcon: createMockComponent('ListItemIcon'),
  ListItemSecondaryAction: createMockComponent('ListItemSecondaryAction'),
  ListItemText: ({ primary, secondary, ...props }) => 
    React.createElement('div', 
      { 'data-testid': 'listitemtext', ...props },
      primary && React.createElement('div', { 'data-testid': 'listitem-primary' }, primary),
      secondary && React.createElement('div', { 'data-testid': 'listitem-secondary' }, secondary)
    ),
  MenuItem: ({ value, children }) => React.createElement('option', { value }, children),
  Modal: createMockComponent('Modal'),
  Pagination: ({ count, page, onChange, ...props }) => React.createElement('div', 
    { 
      'data-testid': 'pagination', 
      count,
      page,
      ...props 
    },
    `Page ${page} of ${count}`,
    // Add Previous button if not on first page
    page > 1 && React.createElement('button', 
      { 
        onClick: () => onChange && onChange(null, page - 1),
        'data-testid': 'pagination-previous'
      }, 
      'Previous'
    ),
    // Add Next button if not on last page
    page < count && React.createElement('button', 
      { 
        onClick: () => onChange && onChange(null, page + 1),
        'data-testid': 'pagination-next'
      }, 
      'Next'
    )
  ),
  Paper: createMockComponent('Paper'),
  Radio: createMockComponent('Radio'),
  RadioGroup: ({ children, value, onChange, ...props }) => {
    const handleChange = (e) => {
      if (onChange && e.target.value) {
        onChange(e, e.target.value);
      }
    };
    
    return React.createElement('div', 
      { 
        ...props, 
        'data-testid': 'radio-group',
        'data-value': value,
        onChange: handleChange
      }, 
      children
    );
  },
  Select: ({ value, onChange, children, ...props }) => React.createElement('select',
    {
      value: value || '',
      onChange: (e) => onChange && onChange({ target: { value: e.target.value } }),
      'data-testid': 'select',
      ...props
    },
    children
  ),
  Snackbar: createMockComponent('Snackbar'),
  Stack: createMockComponent('Stack'),
  Switch: createMockComponent('Switch'),
  Tabs: ({ children, value, onChange, ...props }) => {
    const handleClick = (e) => {
      // Find which button was clicked and call onChange with its index
      if (e.target.tagName === 'BUTTON' && onChange) {
        const tabsContainer = e.currentTarget;
        const buttons = Array.from(tabsContainer.querySelectorAll('button'));
        const clickedIndex = buttons.indexOf(e.target);
        if (clickedIndex !== -1) {
          onChange(e, clickedIndex);
        }
      }
    };
    
    return React.createElement('div', 
      { 
        ...props, 
        'data-testid': 'tabs',
        onClick: handleClick
      }, 
      children
    );
  },
  Tab: ({ label, children, ...props }) => 
    React.createElement('button', { ...props, role: 'tab' }, label || children),
  TabPanel: ({ children, value, index, ...props }) => 
    React.createElement('div', 
      { 
        ...props, 
        role: 'tabpanel',
        hidden: value !== index
      },
      value === index ? children : null
    ),
  Table: createMockComponent('Table'),
  TableBody: createMockComponent('TableBody'),
  TableCell: createMockComponent('TableCell'),
  TableContainer: createMockComponent('TableContainer'),
  TableHead: createMockComponent('TableHead'),
  TableRow: createMockComponent('TableRow'),
    TextField: ({ label, value, onChange, name, multiline, rows, helperText, ...props }) => {
    const Element = multiline ? 'textarea' : 'input';
    const inputElement = React.createElement(Element, {
      'data-testid': 'textfield',
      'aria-label': label || name,
      value: value || '',
      onChange: onChange || (() => {}),
      name,
      type: multiline ? 'text' : 'text',
      rows: multiline ? rows : undefined,
      ...props
    });
    
    if (helperText) {
      return React.createElement('div', {}, [
        inputElement,
        React.createElement('div', {
          'data-testid': 'textfield-helpertext',
          key: 'helpertext'
        }, helperText)
      ]);
    }
    
    return inputElement;
  },
  ToggleButton: createMockComponent('ToggleButton'),
  ToggleButtonGroup: createMockComponent('ToggleButtonGroup'),
  Toolbar: createMockComponent('Toolbar'),
  Tooltip: createMockComponent('Tooltip'),
  Typography: ({ children, variant, gutterBottom, ...props }) => {
    // Filter out Material-UI specific props to avoid DOM warnings
    return React.createElement('div', { 'data-variant': variant, component: props.component, ...props }, children);
  },
  Checkbox: createMockComponent('Checkbox'),
  FormControlLabel: ({ control, label, ...props }) => 
    React.createElement('div', 
      { 'data-testid': 'formcontrollabel', ...props },
      control,
      React.createElement('span', null, label)
    ),
  FormControl: createMockComponent('FormControl'),
  InputLabel: createMockComponent('InputLabel'),
  Select: ({ value, onChange, children, ...props }) => React.createElement('select',
    {
      value: value || '',
      onChange: (e) => onChange && onChange({ target: { value: e.target.value } }),
      'data-testid': 'select',
      ...props
    },
    children
  ),
  MenuItem: ({ value, children }) => React.createElement('option', { value }, children),
}))

// Mock @mui/icons-material components
vi.mock('@mui/icons-material', () => ({
  Add: createMockComponent('Add'),
  AddCircle: createMockComponent('AddCircle'),
  Check: createMockComponent('Check'),
  CheckCircle: createMockComponent('CheckCircle'),
  Clear: createMockComponent('Clear'),
  Delete: createMockComponent('Delete'),
  Edit: createMockComponent('Edit'),
  Email: createMockComponent('Email'),
  Error: createMockComponent('Error'),
  FilterList: createMockComponent('FilterList'),
  Group: createMockComponent('Group'),
  Home: createMockComponent('Home'),
  Info: createMockComponent('Info'),
  Message: createMockComponent('Message'),
  MoreVert: createMockComponent('MoreVert'),
  People: createMockComponent('People'),
  Person: createMockComponent('Person'),
  Phone: createMockComponent('Phone'),
  Refresh: createMockComponent('Refresh'),
  School: createMockComponent('School'),
  Search: createMockComponent('Search'),
  Send: createMockComponent('Send'),
  Warning: createMockComponent('Warning'),
  Work: createMockComponent('Work'),
}))

// Mock @mui/material/styles
vi.mock('@mui/material/styles', () => ({
  ThemeProvider: createMockComponent('ThemeProvider'),
  createTheme: vi.fn(() => ({})),
  useTheme: vi.fn(() => ({})),
}))

// Reset mocks before each test
beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
})