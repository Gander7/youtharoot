import React from 'react';
import { ClerkProvider } from '@clerk/clerk-react';

const publishableKey = import.meta.env.PUBLIC_CLERK_PUBLISHABLE_KEY;

if (!publishableKey) {
  throw new Error('Missing Clerk Publishable Key');
}

function ClerkProviderWrapper({ children }) {
  return (
    <ClerkProvider publishableKey={publishableKey}>
      {children}
    </ClerkProvider>
  );
}

export default ClerkProviderWrapper;
