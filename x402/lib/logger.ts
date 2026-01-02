/**
 * Simple structured logging utility
 * In production, consider integrating with a service like Datadog, Sentry, or CloudWatch
 */

type LogLevel = 'info' | 'warn' | 'error'

interface LogContext {
  [key: string]: string | number | boolean | null | undefined
}

function log(level: LogLevel, message: string, context?: LogContext) {
  const timestamp = new Date().toISOString()
  const logEntry = {
    timestamp,
    level,
    message,
    ...context,
  }

  // In production, you might want to send to a logging service
  // For now, just use console with JSON for structured logs
  const logMethod = level === 'error' ? console.error : level === 'warn' ? console.warn : console.log
  logMethod(JSON.stringify(logEntry))
}

export const logger = {
  info: (message: string, context?: LogContext) => log('info', message, context),
  warn: (message: string, context?: LogContext) => log('warn', message, context),
  error: (message: string, context?: LogContext) => log('error', message, context),
}

