import React, { useEffect, useState } from 'react';
import { useStore } from '@nanostores/react';
import { Box, CircularProgress, Typography } from '@mui/material';
import { authStore, initAuth } from '../stores/auth';
import ErrorBoundary from './ErrorBoundary.jsx';

export default function AuthGuard({ children }) {
  const auth = useStore(authStore);
  const [isInitialized, setIsInitialized] = useState(false);
  const [initError, setInitError] = useState(null);

  useEffect(() => {
    // Initialize auth state from localStorage with error handling
    try {
      initAuth();
      setIsInitialized(true);
    } catch (error) {
      console.error('Auth initialization failed:', error);
      setInitError(error);
      setIsInitialized(true); // Still set to true to stop loading
    }
  }, []);

  useEffect(() => {
    // Redirect to login if not authenticated and initialization is complete
    if (isInitialized && !auth.isAuthenticated && !initError) {
      window.location.href = '/login';
    }
  }, [auth.isAuthenticated, isInitialized, initError]);

  // Show loading while initializing
  if (!isInitialized) {
    return (
      <Box 
        display="flex" 
        justifyContent="center" 
        alignItems="center" 
        minHeight="100vh"
        sx={{ backgroundColor: '#1e1e1e' }}
      >
        <Box textAlign="center">
          <CircularProgress size={40} sx={{ mb: 2 }} />
          <Typography color="text.secondary">Loading...</Typography>
        </Box>
      </Box>
    );
  }

  // Show error if initialization failed
  if (initError) {
    return (
      <ErrorBoundary 
        level="page"
        title="Authentication Error"
        message="We're having trouble loading your authentication state. This might be due to corrupted local data."
      >
        <div>Authentication failed</div>
      </ErrorBoundary>
    );
  }

  // Show loading while redirecting to login
  if (!auth.isAuthenticated) {
    return (
      <Box 
        display="flex" 
        justifyContent="center" 
        alignItems="center" 
        minHeight="100vh"
        sx={{ backgroundColor: '#1e1e1e' }}
      >
        <Box textAlign="center">
          <CircularProgress size={40} sx={{ mb: 2 }} />
          <Typography color="text.secondary">Redirecting to login...</Typography>
        </Box>
      </Box>
    );
  }

  // Render children if authenticated, wrapped in error boundary
  return (
    <ErrorBoundary level="page" title="Application Error">
      {children}
    </ErrorBoundary>
  );
}