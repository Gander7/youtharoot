import React, { useEffect } from 'react';
import { ClerkProvider, SignedIn, SignedOut, useUser, useAuth } from '@clerk/clerk-react';
import Navigation from './Navigation.jsx';
import ErrorBoundary from './ErrorBoundary.jsx';

const publishableKey = import.meta.env.PUBLIC_CLERK_PUBLISHABLE_KEY;

if (!publishableKey) {
  throw new Error('Missing Clerk Publishable Key');
}

function AuthenticatedContent({ children }) {
  const { user, isLoaded } = useUser();
  const { getToken } = useAuth();
  
  // Debug logging
  useEffect(() => {
    console.log('🔵 AuthenticatedContent:', { 
      isLoaded, 
      hasUser: !!user, 
      userId: user?.id,
      getTokenType: typeof getToken 
    });
  }, [user, isLoaded, getToken]);
  
  // Clone children and inject user and getToken props if it's a React element
  const childrenWithProps = React.Children.map(children, child => {
    if (React.isValidElement(child)) {
      return React.cloneElement(child, { user, getToken });
    }
    return child;
  });

  return (
    <>
      <Navigation />
      {childrenWithProps}
    </>
  );
}

function AuthenticatedApp({ children }) {
  return (
    <ClerkProvider publishableKey={publishableKey}>
      <ErrorBoundary level="page" title="Application Error">
        <SignedIn>
          <AuthenticatedContent>
            {children}
          </AuthenticatedContent>
        </SignedIn>
        <SignedOut>
          <RedirectToSignIn />
        </SignedOut>
      </ErrorBoundary>
    </ClerkProvider>
  );
}

function RedirectToSignIn() {
  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.location.href = '/sign-in';
    }
  }, []);
  
  return <div>Redirecting to sign in...</div>;
}

export default AuthenticatedApp;
