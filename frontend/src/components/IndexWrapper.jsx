import React from 'react';
import AuthenticatedApp from './AuthenticatedApp.jsx';

function HomeContent() {
  return (
    <main>
      <div style={{ maxWidth: '600px', margin: '0 auto', padding: '2rem', textAlign: 'center' }}>
        <h1>Welcome to Youtharoot</h1>
        <p>Manage your youth group events and people efficiently.</p>

        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', marginTop: '2rem', flexWrap: 'wrap' }}>
          <a href="/Events" style={{ textDecoration: 'none' }}>
            <div style={{ background: '#242424', padding: '2rem', borderRadius: '12px', minWidth: '200px' }}>
              <h3 style={{ margin: '0 0 1rem 0', color: '#90caf9' }}>📅 Events</h3>
              <p style={{ margin: 0, color: '#b0b0b0' }}>View and manage upcoming events</p>
            </div>
          </a>
          <a href="/People" style={{ textDecoration: 'none' }}>
            <div style={{ background: '#242424', padding: '2rem', borderRadius: '12px', minWidth: '200px' }}>
              <h3 style={{ margin: '0 0 1rem 0', color: '#f48fb1' }}>👥 People</h3>
              <p style={{ margin: 0, color: '#b0b0b0' }}>Manage youth and leaders</p>
            </div>
          </a>
        </div>
      </div>
    </main>
  );
}

export default function IndexWrapper() {
  return (
    <AuthenticatedApp>
      <HomeContent />
    </AuthenticatedApp>
  );
}
