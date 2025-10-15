import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Tab, 
  Tabs, 
  Container, 
  Typography, 
  Paper,
  Alert
} from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import ErrorBoundary from './ErrorBoundary';
import GroupList from './GroupList';
import MessageForm from './MessageForm';
import MessageHistory from './MessageHistory';
import ApiErrorBoundary from './ApiErrorBoundary';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#90caf9',
    },
    secondary: {
      main: '#f48fb1',
    },
    background: {
      default: '#181818',
      paper: '#242424',
    },
    text: {
      primary: '#f5f5f5',
      secondary: '#e0e0e0',
    },
  },
});

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`messaging-tabpanel-${index}`}
      aria-labelledby={`messaging-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function MessagingPage() {
  const [tabValue, setTabValue] = useState(0);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleGroupSelect = (group) => {
    setSelectedGroup(group);
    setTabValue(1); // Switch to Send Message tab
  };

  const handleMessageSent = () => {
    setRefreshTrigger(prev => prev + 1);
    setTabValue(2); // Switch to Message History tab
  };

  const handleGroupCreated = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <ThemeProvider theme={darkTheme}>
      <ErrorBoundary>
        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            SMS Messaging
          </Typography>
          
          <Paper sx={{ width: '100%' }}>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs 
                value={tabValue} 
                onChange={handleTabChange} 
                aria-label="messaging tabs"
              >
                <Tab label="Message Groups" />
                <Tab label="Send Message" />
                <Tab label="Message History" />
              </Tabs>
            </Box>
            
            <TabPanel value={tabValue} index={0}>
              <ApiErrorBoundary>
                <GroupList 
                  onGroupSelect={handleGroupSelect}
                  onGroupCreated={handleGroupCreated}
                  refreshTrigger={refreshTrigger}
                />
              </ApiErrorBoundary>
            </TabPanel>
            
            <TabPanel value={tabValue} index={1}>
              <ApiErrorBoundary>
                <MessageForm 
                  selectedGroup={selectedGroup}
                  onMessageSent={handleMessageSent}
                  refreshTrigger={refreshTrigger}
                />
              </ApiErrorBoundary>
            </TabPanel>
            
            <TabPanel value={tabValue} index={2}>
              <ApiErrorBoundary>
                <MessageHistory 
                  refreshTrigger={refreshTrigger}
                />
              </ApiErrorBoundary>
            </TabPanel>
          </Paper>
        </Container>
      </ErrorBoundary>
    </ThemeProvider>
  );
}

export default MessagingPage;