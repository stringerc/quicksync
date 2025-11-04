/**
 * Short-Time Fourier Transform (STFT)
 * Windowed spectral analysis on event timestamps
 */

export interface Spectrogram {
  magnitudes: number[][];  // Magnitude for each time window and frequency bin
  timeWindows: number;      // Number of time windows
  frequencyBins: number;    // Number of frequency bins
}

/**
 * Compute STFT on time series
 * @param samples Time series data
 * @param win Window size (number of samples per window)
 * @param hop Hop size (number of samples to advance between windows)
 * @returns Spectrogram with magnitudes
 */
export function stft(samples: number[], win: number, hop: number): Spectrogram {
  const mags: number[][] = [];
  
  for (let i = 0; i + win <= samples.length; i += hop) {
    const frame = samples.slice(i, i + win);
    mags.push(naiveDFTMag(frame, 16)); // 16 frequency bins
  }
  
  return {
    magnitudes: mags,
    timeWindows: mags.length,
    frequencyBins: mags[0]?.length || 0,
  };
}

/**
 * Naive DFT magnitude computation
 * @param x Time-domain samples
 * @param bins Number of frequency bins
 * @returns Magnitude spectrum
 */
function naiveDFTMag(x: number[], bins: number): number[] {
  const out: number[] = [];
  
  for (let k = 0; k < bins; k++) {
    let re = 0;
    let im = 0;
    
    for (let n = 0; n < x.length; n++) {
      const ang = (-2 * Math.PI * k * n) / x.length;
      re += x[n] * Math.cos(ang);
      im += x[n] * Math.sin(ang);
    }
    
    out.push(Math.hypot(re, im));
  }
  
  return out;
}

/**
 * Find dominant frequencies from spectrogram
 * @param spectrogram STFT result
 * @param topK Number of top frequencies to return
 * @returns Array of [binIndex, magnitude] pairs
 */
export function findPeaks(spectrogram: Spectrogram, topK = 3): number[][] {
  if (spectrogram.timeWindows === 0) return [];
  
  // Average across time windows
  const avgMag: number[] = new Array(spectrogram.frequencyBins).fill(0);
  
  for (const frame of spectrogram.magnitudes) {
    for (let k = 0; k < frame.length; k++) {
      avgMag[k] += frame[k];
    }
  }
  
  for (let k = 0; k < avgMag.length; k++) {
    avgMag[k] /= spectrogram.timeWindows;
  }
  
  // Find top K peaks
  const indexed = avgMag.map((mag, idx) => [idx, mag]);
  indexed.sort((a, b) => b[1] - a[1]);
  
  return indexed.slice(0, topK);
}

