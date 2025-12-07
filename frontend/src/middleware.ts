import { clerkMiddleware, createRouteMatcher } from '@clerk/astro/server';

const isProtectedRoute = createRouteMatcher([
  '/',
  '/Events(.*)',
  '/People(.*)',
  '/Messaging(.*)',
  '/checkin(.*)',
]);

export const onRequest = clerkMiddleware((auth, context) => {
  const { redirectToSignIn, userId } = auth();

  if (!userId && isProtectedRoute(context.request)) {
    return redirectToSignIn();
  }
});
