import React, { useEffect, useState } from 'react';
import { useStore } from '@nanostores/react';
import { Box, CircularProgress, Typography } from '@mui/material';
import { authStore, initAuth } from '../stores/auth';

export default function AuthGuard({ children }) {
  const auth = useStore(authStore);
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    // Initialize auth state from localStorage
    initAuth();
    setIsInitialized(true);
  }, []);

  useEffect(() => {
    // Redirect to login if not authenticated and initialization is complete
    if (isInitialized && !auth.isAuthenticated) {
      window.location.href = '/login';
    }
  }, [auth.isAuthenticated, isInitialized]);

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

  // Render children if authenticated
  return <>{children}</>;
}