"use strict";
/**
 * Resonance Runtime
 * Complete package exports
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
var __exportStar = (this && this.__exportStar) || function(m, exports) {
    for (var p in m) if (p !== "default" && !Object.prototype.hasOwnProperty.call(exports, p)) __createBinding(exports, m, p);
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.LatencyHistogram = exports.ResonanceCalculus = void 0;
// Core
__exportStar(require("./resonance-core"), exports);
var calculus_1 = require("./resonance-core/calculus");
Object.defineProperty(exports, "ResonanceCalculus", { enumerable: true, get: function () { return calculus_1.ResonanceCalculus; } });
// Spectral
__exportStar(require("./spectral"), exports);
// Math
__exportStar(require("./resonance-math"), exports);
// SDK
__exportStar(require("./sdk/node"), exports);
// Observability
var histogram_1 = require("./observability/histogram");
Object.defineProperty(exports, "LatencyHistogram", { enumerable: true, get: function () { return histogram_1.LatencyHistogram; } });
//# sourceMappingURL=index.js.map