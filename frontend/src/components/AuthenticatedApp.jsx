import React, { useEffect } from 'react';
import { SignedIn, SignedOut, useUser, useAuth } from '@clerk/clerk-react';
import ErrorBoundary from './ErrorBoundary.jsx';

function AuthenticatedContent({ children }) {
  const { user } = useUser();
  const { getToken } = useAuth();

  // Clone children and inject user and getToken props if it's a React element
  const childrenWithProps = React.Children.map(children, child => {
    if (React.isValidElement(child)) {
      return React.cloneElement(child, { user, getToken });
    }
    return child;
  });

  return <>{childrenWithProps}</>;
}

function AuthenticatedApp({ children }) {
  return (
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
