import React from 'react';
import AuthenticatedApp from './AuthenticatedApp.jsx';
import MessagingPage from './MessagingPage.jsx';

// This wrapper combines AuthenticatedApp and MessagingPage in a single React tree
export default function MessagingPageWrapper() {
  return (
    <AuthenticatedApp>
      <MessagingPage />
    </AuthenticatedApp>
  );
}
