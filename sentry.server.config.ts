// This file configures the initialization of Sentry on the server.
// The config you add here will be used whenever the server handles a request.
// https://docs.sentry.io/platforms/javascript/guides/nextjs/

import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.SENTRY_DSN || "https://60f78090eb56baab93e466a1c170aa18@o4510642039685120.ingest.us.sentry.io/4510642041651200",
  
  // Enable logging
  enableLogs: true,
  
  // Adjust this value in production, or use tracesSampler for greater control
  tracesSampleRate: 1.0,
  
  // Setting this option to true will print useful information to the console while you're setting up Sentry.
  debug: false,
  
  // Only send errors in production
  enabled: process.env.NODE_ENV === "production",
  
  // Integrations
  integrations: [
    // Send console.log, console.warn, and console.error calls as logs to Sentry
    Sentry.consoleLoggingIntegration({ levels: ["log", "warn", "error"] }),
  ],
  
  // Filter out common errors that aren't actionable
  beforeSend(event, hint) {
    // Don't send errors in development
    if (process.env.NODE_ENV === "development") {
      return null;
    }
    
    return event;
  },
});

