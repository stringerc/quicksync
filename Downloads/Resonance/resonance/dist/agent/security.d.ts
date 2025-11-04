/**
 * Security middleware for Resonance Agent
 * Provides API key authentication, rate limiting, and security headers
 */
export interface SecurityConfig {
    apiKey?: string;
    rateLimitWindowMs: number;
    rateLimitMaxRequests: number;
    allowedOrigins: string[];
    enableCORS: boolean;
}
/**
 * Validate API key from request headers
 */
export declare function validateApiKey(req: any, config: SecurityConfig): boolean;
/**
 * Rate limiting middleware
 */
export declare function checkRateLimit(ip: string, config: SecurityConfig): boolean;
/**
 * Get client IP address
 */
export declare function getClientIP(req: any): string;
/**
 * Set security headers
 */
export declare function setSecurityHeaders(res: any, config: SecurityConfig): void;
/**
 * Generate secure API key
 */
export declare function generateApiKey(): string;
/**
 * Clean up expired rate limit entries (call periodically)
 */
export declare function cleanupRateLimit(): void;
//# sourceMappingURL=security.d.ts.map