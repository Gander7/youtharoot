import React, { useState } from 'react';
import { useStore } from '@nanostores/react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  Container,
  Paper,
} from '@mui/material';
import { login, authLoading, authError, authStore } from '../stores/auth';

export default function LoginForm() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const loading = useStore(authLoading);
  const error = useStore(authError);
  const auth = useStore(authStore);

  // Redirect if already authenticated
  React.useEffect(() => {
    if (auth.isAuthenticated) {
      window.location.href = '/';
    }
  }, [auth.isAuthenticated]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!username || !password) {
      return;
    }

    const success = await login(username, password);
    if (success) {
      // Redirect to home page
      window.location.href = '/';
    }
  };

  return (
    <Container maxWidth="sm">
      <Paper elevation={6} sx={{ 
        p: 4, 
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(10px)',
        borderRadius: 2
      }}>
        <Box display="flex" flexDirection="column" alignItems="center">
          <Typography variant="h4" component="h1" gutterBottom sx={{ color: '#333', fontWeight: 'bold' }}>
            Youth Attendance
          </Typography>
          
          <Typography variant="h6" component="h2" gutterBottom sx={{ color: '#666', mb: 3 }}>
            Sign In
          </Typography>

          <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1, width: '100%' }}>
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            <TextField
              fullWidth
              label="Username"
              variant="outlined"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={loading}
              required
              sx={{ mb: 2 }}
            />

            <TextField
              fullWidth
              label="Password"
              type="password"
              variant="outlined"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              required
              sx={{ mb: 3 }}
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              disabled={loading || !username || !password}
              sx={{ 
                mb: 2,
                py: 1.5,
                background: 'linear-gradient(45deg, #667eea 30%, #764ba2 90%)',
                '&:hover': {
                  background: 'linear-gradient(45deg, #5a6fd8 30%, #6a4190 90%)',
                }
              }}
            >
              {loading ? <CircularProgress size={24} color="inherit" /> : 'Sign In'}
            </Button>
          </Box>

          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <Typography variant="body2" sx={{ color: '#666', mb: 1 }}>
              Demo Credentials:
            </Typography>
            <Typography variant="body2" sx={{ color: '#666' }}>
              Admin: <strong>admin</strong> / <strong>admin123</strong>
            </Typography>
            <Typography variant="body2" sx={{ color: '#666' }}>
              User: <strong>user</strong> / <strong>user123</strong>
            </Typography>
          </Box>
        </Box>
      </Paper>
    </Container>
  );
}