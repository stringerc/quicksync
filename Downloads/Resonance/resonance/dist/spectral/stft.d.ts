/**
 * Short-Time Fourier Transform (STFT)
 * Windowed spectral analysis on event timestamps
 */
export interface Spectrogram {
    magnitudes: number[][];
    timeWindows: number;
    frequencyBins: number;
}
/**
 * Compute STFT on time series
 * @param samples Time series data
 * @param win Window size (number of samples per window)
 * @param hop Hop size (number of samples to advance between windows)
 * @returns Spectrogram with magnitudes
 */
export declare function stft(samples: number[], win: number, hop: number): Spectrogram;
/**
 * Find dominant frequencies from spectrogram
 * @param spectrogram STFT result
 * @param topK Number of top frequencies to return
 * @returns Array of [binIndex, magnitude] pairs
 */
export declare function findPeaks(spectrogram: Spectrogram, topK?: number): number[][];
//# sourceMappingURL=stft.d.ts.map