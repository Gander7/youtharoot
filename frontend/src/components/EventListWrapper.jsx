import React from 'react';
import AuthenticatedApp from './AuthenticatedApp.jsx';
import EventList from './EventList.jsx';

export default function EventListWrapper() {
  return (
    <AuthenticatedApp>
      <EventList />
    </AuthenticatedApp>
  );
}
