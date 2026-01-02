// This file configures the initialization of Sentry on the client.
// The config you add here will be used whenever a users loads a page in their browser.
// https://docs.sentry.io/platforms/javascript/guides/nextjs/

import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  
  // Adjust this value in production, or use tracesSampler for greater control
  tracesSampleRate: 1.0,
  
  // Setting this option to true will print useful information to the console while you're setting up Sentry.
  debug: false,
  
  // Only send errors in production
  enabled: process.env.NODE_ENV === "production",
  
  // Filter out common browser errors that aren't actionable
  beforeSend(event, hint) {
    // Don't send errors in development
    if (process.env.NODE_ENV === "development") {
      return null;
    }
    
    // Filter out known non-critical errors
    const error = hint.originalException;
    if (error && typeof error === "object" && "message" in error) {
      const message = String(error.message);
      // Filter out network errors that are user's connection issues
      if (message.includes("Failed to fetch") || message.includes("NetworkError")) {
        return null;
      }
    }
    
    return event;
  },
  
  replaysOnErrorSampleRate: 1.0,
  replaysSessionSampleRate: 0.1,
});

