import React from 'react';
import AuthenticatedApp from './AuthenticatedApp.jsx';
import PersonList from './PersonList.jsx';

export default function PersonListWrapper() {
  return (
    <AuthenticatedApp>
      <PersonList />
    </AuthenticatedApp>
  );
}
