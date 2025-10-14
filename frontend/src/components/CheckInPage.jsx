import React, { useState, useEffect } from 'react';
import CheckIn from './CheckIn.jsx';

const CheckInPage = () => {
  const [eventId, setEventId] = useState(null);
  const [viewOnly, setViewOnly] = useState(false);

  useEffect(() => {
    // Extract eventId and viewOnly from URL parameters client-side
    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get('eventId');
    const isViewOnly = urlParams.get('viewOnly') === 'true';
    
    if (id) {
      setEventId(parseInt(id));
      setViewOnly(isViewOnly);
    } else {
      // If no eventId parameter, redirect to event list or show error
      window.location.href = '/';
    }
  }, []);

  if (!eventId) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <p>Loading...</p>
      </div>
    );
  }

  return <CheckIn eventId={eventId} viewOnly={viewOnly} />;
};

export default CheckInPage;