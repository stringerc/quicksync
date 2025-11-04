/**
 * Security middleware for Resonance Agent
 * Provides API key authentication, rate limiting, and security headers
 */

import * as crypto from 'crypto';

export interface SecurityConfig {
  apiKey?: string;
  rateLimitWindowMs: number;
  rateLimitMaxRequests: number;
  allowedOrigins: string[];
  enableCORS: boolean;
}

interface RateLimitEntry {
  count: number;
  resetAt: number;
}

// In-memory rate limit store (for production, use Redis)
const rateLimitStore = new Map<string, RateLimitEntry>();

const defaultConfig: SecurityConfig = {
  rateLimitWindowMs: 60000, // 1 minute
  rateLimitMaxRequests: 100, // 100 requests per minute
  allowedOrigins: [],
  enableCORS: false,
};

/**
 * Validate API key from request headers
 */
export function validateApiKey(req: any, config: SecurityConfig): boolean {
  if (!config.apiKey) {
    // No API key configured = allow all (development mode)
    return true;
  }

  const authHeader = req.headers['authorization'] || req.headers['x-api-key'];
  if (!authHeader) {
    return false;
  }

  // Support both "Bearer <key>" and direct key
  const providedKey = authHeader.startsWith('Bearer ')
    ? authHeader.substring(7)
    : authHeader;

  // Use constant-time comparison to prevent timing attacks
  return crypto.timingSafeEqual(
    Buffer.from(providedKey),
    Buffer.from(config.apiKey)
  );
}

/**
 * Rate limiting middleware
 */
export function checkRateLimit(ip: string, config: SecurityConfig): boolean {
  const now = Date.now();
  const entry = rateLimitStore.get(ip);

  if (!entry || entry.resetAt < now) {
    // New entry or expired window
    rateLimitStore.set(ip, {
      count: 1,
      resetAt: now + config.rateLimitWindowMs,
    });
    return true;
  }

  if (entry.count >= config.rateLimitMaxRequests) {
    return false; // Rate limit exceeded
  }

  entry.count++;
  return true;
}

/**
 * Get client IP address
 */
export function getClientIP(req: any): string {
  return (
    req.headers['x-forwarded-for']?.split(',')[0]?.trim() ||
    req.headers['x-real-ip'] ||
    req.socket?.remoteAddress ||
    'unknown'
  );
}

/**
 * Set security headers
 */
export function setSecurityHeaders(res: any, config: SecurityConfig): void {
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-XSS-Protection', '1; mode=block');
  res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');

  if (config.enableCORS && config.allowedOrigins.length > 0) {
    const origin = res.req?.headers?.origin;
    if (origin && config.allowedOrigins.includes(origin)) {
      res.setHeader('Access-Control-Allow-Origin', origin);
      res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
      res.setHeader('Access-Control-Allow-Headers', 'Authorization, X-API-Key');
      res.setHeader('Access-Control-Max-Age', '86400');
    }
  }
}

/**
 * Generate secure API key
 */
export function generateApiKey(): string {
  return crypto.randomBytes(32).toString('base64url');
}

/**
 * Clean up expired rate limit entries (call periodically)
 */
export function cleanupRateLimit(): void {
  const now = Date.now();
  for (const [ip, entry] of rateLimitStore.entries()) {
    if (entry.resetAt < now) {
      rateLimitStore.delete(ip);
    }
  }
}

// Cleanup every 5 minutes
setInterval(cleanupRateLimit, 5 * 60 * 1000);

