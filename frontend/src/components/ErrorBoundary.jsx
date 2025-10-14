import React from 'react';
import {
  Box,
  Typography,
  Button,
  Alert,
  AlertTitle,
  Paper,
  Stack,
  Chip
} from '@mui/material';
import {
  ErrorOutline as ErrorIcon,
  Refresh as RefreshIcon,
  Home as HomeIcon,
  BugReport as BugIcon
} from '@mui/icons-material';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error: error,
      errorId: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    };
  }

  componentDidCatch(error, errorInfo) {
    // Log error details for debugging
    console.group('🚨 React Error Boundary Caught Error');
    console.error('Error:', error);
    console.error('Error Info:', errorInfo);
    console.error('Component Stack:', errorInfo.componentStack);
    console.groupEnd();

    // Update state with error details
    this.setState({
      error: error,
      errorInfo: errorInfo
    });

    // In production, you might want to send this to an error reporting service
    if (!import.meta.env.DEV) {
      this.reportError(error, errorInfo);
    }
  }

  reportError = (error, errorInfo) => {
    // TODO: Integrate with error reporting service (Sentry, LogRocket, etc.)
    const errorReport = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      userAgent: navigator.userAgent,
      errorId: this.state.errorId
    };

    // For now, just log to console in production
    console.error('Error Report:', errorReport);
  };

  handleRetry = () => {
    // Reset error state to re-render the component
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null
    });
  };

  handleGoHome = () => {
    // Navigate to home page
    window.location.href = '/';
  };

  handleReload = () => {
    // Reload the entire page
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      const { error, errorInfo, errorId } = this.state;
      const { level = 'page', title, message, showDetails = import.meta.env.DEV } = this.props;

      return (
        <Box
          sx={{
            minHeight: level === 'page' ? '100vh' : 'auto',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            p: 3,
            bgcolor: 'background.default'
          }}
        >
          <Paper
            elevation={3}
            sx={{
              p: 4,
              maxWidth: 600,
              width: '100%',
              textAlign: 'center'
            }}
          >
            <Stack spacing={3} alignItems="center">
              {/* Error Icon */}
              <ErrorIcon
                sx={{
                  fontSize: 64,
                  color: 'error.main',
                  opacity: 0.8
                }}
              />

              {/* Error Title */}
              <Typography variant="h4" component="h1" color="error.main" fontWeight="bold">
                {title || 'Oops! Something went wrong'}
              </Typography>

              {/* Error Message */}
              <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                {message || 'We encountered an unexpected error. Our team has been notified and is working on a fix.'}
              </Typography>

              {/* Error ID for support */}
              {errorId && (
                <Chip
                  icon={<BugIcon />}
                  label={`Error ID: ${errorId}`}
                  variant="outlined"
                  size="small"
                  sx={{ fontSize: '0.75rem' }}
                />
              )}

              {/* Action Buttons */}
              <Stack direction="row" spacing={2} sx={{ mt: 3 }}>
                <Button
                  variant="contained"
                  startIcon={<RefreshIcon />}
                  onClick={this.handleRetry}
                  size="large"
                >
                  Try Again
                </Button>

                {level === 'page' && (
                  <Button
                    variant="outlined"
                    startIcon={<HomeIcon />}
                    onClick={this.handleGoHome}
                    size="large"
                  >
                    Go Home
                  </Button>
                )}

                <Button
                  variant="text"
                  onClick={this.handleReload}
                  size="large"
                >
                  Reload Page
                </Button>
              </Stack>

              {/* Development Error Details */}
              {showDetails && error && (
                <Alert severity="error" sx={{ mt: 3, textAlign: 'left', width: '100%' }}>
                  <AlertTitle>Development Error Details</AlertTitle>
                  <Typography variant="body2" component="pre" sx={{ 
                    overflow: 'auto', 
                    fontSize: '0.75rem',
                    mb: 1
                  }}>
                    {error.message}
                  </Typography>
                  {error.stack && (
                    <details>
                      <summary style={{ cursor: 'pointer', marginBottom: '8px' }}>
                        <strong>Stack Trace</strong>
                      </summary>
                      <Typography variant="body2" component="pre" sx={{ 
                        overflow: 'auto', 
                        fontSize: '0.7rem',
                        whiteSpace: 'pre-wrap'
                      }}>
                        {error.stack}
                      </Typography>
                    </details>
                  )}
                  {errorInfo?.componentStack && (
                    <details>
                      <summary style={{ cursor: 'pointer', marginBottom: '8px' }}>
                        <strong>Component Stack</strong>
                      </summary>
                      <Typography variant="body2" component="pre" sx={{ 
                        overflow: 'auto', 
                        fontSize: '0.7rem',
                        whiteSpace: 'pre-wrap'
                      }}>
                        {errorInfo.componentStack}
                      </Typography>
                    </details>
                  )}
                </Alert>
              )}
            </Stack>
          </Paper>
        </Box>
      );
    }

    // No error, render children normally
    return this.props.children;
  }
}

export default ErrorBoundary;