"use strict";
/**
 * Security middleware for Resonance Agent
 * Provides API key authentication, rate limiting, and security headers
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.validateApiKey = validateApiKey;
exports.checkRateLimit = checkRateLimit;
exports.getClientIP = getClientIP;
exports.setSecurityHeaders = setSecurityHeaders;
exports.generateApiKey = generateApiKey;
exports.cleanupRateLimit = cleanupRateLimit;
const crypto = __importStar(require("crypto"));
// In-memory rate limit store (for production, use Redis)
const rateLimitStore = new Map();
const defaultConfig = {
    rateLimitWindowMs: 60000, // 1 minute
    rateLimitMaxRequests: 100, // 100 requests per minute
    allowedOrigins: [],
    enableCORS: false,
};
/**
 * Validate API key from request headers
 */
function validateApiKey(req, config) {
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
    return crypto.timingSafeEqual(Buffer.from(providedKey), Buffer.from(config.apiKey));
}
/**
 * Rate limiting middleware
 */
function checkRateLimit(ip, config) {
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
function getClientIP(req) {
    return (req.headers['x-forwarded-for']?.split(',')[0]?.trim() ||
        req.headers['x-real-ip'] ||
        req.socket?.remoteAddress ||
        'unknown');
}
/**
 * Set security headers
 */
function setSecurityHeaders(res, config) {
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
function generateApiKey() {
    return crypto.randomBytes(32).toString('base64url');
}
/**
 * Clean up expired rate limit entries (call periodically)
 */
function cleanupRateLimit() {
    const now = Date.now();
    for (const [ip, entry] of rateLimitStore.entries()) {
        if (entry.resetAt < now) {
            rateLimitStore.delete(ip);
        }
    }
}
// Cleanup every 5 minutes
setInterval(cleanupRateLimit, 5 * 60 * 1000);
//# sourceMappingURL=security.js.map