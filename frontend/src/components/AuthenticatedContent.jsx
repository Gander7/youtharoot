import React, { useEffect } from 'react';
import { SignedIn, SignedOut } from '@clerk/clerk-react';
import Navigation from './Navigation.jsx';

function AuthenticatedContent({ children }) {
  return (
    <>
      <SignedIn>
        <Navigation />
        {children}
      </SignedIn>
      <SignedOut>
        <RedirectToSignIn />
      </SignedOut>
    </>
  );
}

function RedirectToSignIn() {
  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.location.href = '/sign-in';
    }
  }, []);
  
  return null;
}

export default AuthenticatedContent;
