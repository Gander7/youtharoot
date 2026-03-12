import React from 'react';
import AuthenticatedApp from './AuthenticatedApp.jsx';
import CheckInPage from './CheckInPage.jsx';

export default function CheckInPageWrapper() {
  return (
    <AuthenticatedApp>
      <CheckInPage />
    </AuthenticatedApp>
  );
}
