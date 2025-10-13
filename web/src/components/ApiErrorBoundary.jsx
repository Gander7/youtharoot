import React from 'react';
import ErrorBoundary from './ErrorBoundary.jsx';

/**
 * Specialized error boundary for API-related errors
 * Provides specific messaging and recovery options for network/API failures
 */
class ApiErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      retryCount: 0,
      maxRetries: 3
    };
  }

  componentDidCatch(error, errorInfo) {
    // Check if this is an API-related error
    const isApiError = this.isApiError(error);
    
    if (isApiError) {
      console.group('🌐 API Error Boundary Caught Error');
      console.error('API Error:', error);
      console.error('Retry Count:', this.state.retryCount);
      console.groupEnd();
    }
  }

  isApiError = (error) => {
    // Detect common API error patterns
    const apiErrorPatterns = [
      /fetch/i,
      /network/i,
      /timeout/i,
      /connection/i,
      /authentication required/i,
      /401/,
      /403/,
      /500/,
      /502/,
      /503/,
      /504/
    ];

    const errorMessage = error.message || error.toString();
    return apiErrorPatterns.some(pattern => pattern.test(errorMessage));
  };

  handleRetry = () => {
    const { retryCount, maxRetries } = this.state;
    
    if (retryCount < maxRetries) {
      this.setState({ retryCount: retryCount + 1 });
      // Force re-render to retry the failed operation
      this.forceUpdate();
    }
  };

  render() {
    const { children, fallback } = this.props;
    const { retryCount, maxRetries } = this.state;

    return (
      <ErrorBoundary
        level="component"
        title="Connection Problem"
        message={`We're having trouble connecting to our servers. This might be due to a network issue or temporary server maintenance. ${
          retryCount < maxRetries 
            ? 'Please try again.' 
            : 'If the problem persists, please check your internet connection or try again later.'
        }`}
        showDetails={import.meta.env.DEV}
        onRetry={retryCount < maxRetries ? this.handleRetry : undefined}
      >
        {fallback && this.state.hasError ? fallback : children}
      </ErrorBoundary>
    );
  }
}

export default ApiErrorBoundary;