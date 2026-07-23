function [spec] = ts_spectrogram(x, fs, nfft)
% TS_SPECTROGRAM  Compute a magnitude spectrogram.
%
%   Inputs:
%       x    - column vector of audio samples
%       fs   - sample rate (Hz)
%       nfft - FFT size (e.g. 512)
%   Output:
%       spec - struct with: matrix (bins x frames, double),
%              frequencies_hz (bins x 1), times_sec (1 x frames)
%
%   Returns zeros on failure so the Python layer can degrade gracefully.

    spec = struct();
    spec.matrix = zeros(0, 0);
    spec.frequencies_hz = zeros(0, 1);
    spec.times_sec = zeros(1, 0);
    try
        x = ts_ascol(x);
        if nargin < 3 || isempty(nfft)
            nfft = 512;
        end
        wlen = nfft;
        hop = round(nfft / 4);
        win = hann(wlen, 'periodic');

        N = numel(x);
        nframes = floor((N - wlen) / hop) + 1;
        if nframes < 1
            return;
        end

        bins = floor(nfft / 2) + 1;
        M = zeros(bins, nframes);
        for k = 1:nframes
            seg = x((k-1)*hop + (1:wlen)) .* win;
            sp = abs(fft(seg, nfft));
            M(:, k) = sp(1:bins);
        end

        spec.matrix = M;
        spec.frequencies_hz = (0:bins-1)' * (fs / nfft);
        spec.times_sec = ((0:nframes-1) * hop) / fs;
    catch ME
        warning('ts_spectrogram failed: %s', ME.message);
    end
end
