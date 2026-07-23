function [feat] = ts_extract_features(x, fs)
% TS_EXTRACT_FEATURES  Extract a structured feature set from audio.
%
%   Inputs:
%       x  - column vector of audio samples
%       fs - sample rate (Hz)
%   Output:
%       feat - struct with: duration_sec, rms_energy, zero_crossing_rate,
%              spectral_centroid, spectral_rolloff, dominant_frequency_hz,
%              mfcc (13 coeffs), pitch_hz, speech_ratio
%
%   Returns sane zeros/empty on failure so the Python side never crashes.

    feat = struct();
    feat.duration_sec = 0;
    feat.rms_energy = 0;
    feat.zero_crossing_rate = 0;
    feat.spectral_centroid = 0;
    feat.spectral_rolloff = 0;
    feat.dominant_frequency_hz = 0;
    feat.mfcc = [];
    feat.pitch_hz = [];
    feat.speech_ratio = [];

    try
        x = ts_ascol(x);
        N = numel(x);
        if N < 16 || fs <= 0
            return;
        end

        feat.duration_sec = N / fs;

        % Time-domain features.
        feat.rms_energy = sqrt(mean(x.^2));
        zc = sum(x(1:end-1) .* x(2:end) < 0);
        feat.zero_crossing_rate = zc / max(N - 1, 1);

        % Spectral features (single FFT of the whole signal).
        X = abs(fft(x .* hann(N, 'periodic')));
        X = X(1:floor(N/2)+1);
        f = (0:numel(X)-1)' * (fs / N);
        total = sum(X + eps);
        feat.spectral_centroid = sum(f .* X) / total;
        cumE = cumsum(X) / total;
        rolloffIdx = find(cumE >= 0.85, 1);
        feat.spectral_rolloff = f(max(rolloffIdx, 1));
        [~, maxIdx] = max(X);
        feat.dominant_frequency_hz = f(maxIdx);

        % MFCCs (via a small mel filterbank).
        try
            coeffs = mfcc(double(x), fs, ...
                'NumCoeffs', 13, 'Window', hann(round(0.03*fs), 'periodic'));
            feat.mfcc = mean(coeffs, 1)';
        catch
            feat.mfcc = [];
        end

        % Pitch via autocorrelation (robust, no toolbox required).
        try
            feat.pitch_hz = ts_pitch_acf(x, fs);
        catch
            feat.pitch_hz = [];
        end

        % Speech ratio: fraction of frames above an energy threshold.
        try
            wlen = max(256, round(0.02*fs));
            hop = round(wlen / 2);
            nframes = floor((N - wlen) / hop) + 1;
            e = zeros(nframes, 1);
            for k = 1:nframes
                seg = x((k-1)*hop + (1:wlen));
                e(k) = rms(seg);
            end
            thr = 0.1 * max(e);
            feat.speech_ratio = sum(e > thr) / max(nframes, 1);
        catch
            feat.speech_ratio = [];
        end
    catch ME
        warning('ts_extract_features failed: %s', ME.message);
    end
end

function [p] = ts_pitch_acf(x, fs)
    x = x - mean(x);
    maxLag = min(numel(x)-1, round(fs/50));   % up to 50 Hz
    minLag = max(1, round(fs/500));            % down to 500 Hz
    r = xcorr(x, maxLag, 'unbiased');
    r = r(maxLag+1:end);
    [~, lag] = max(r(minLag:maxLag));
    lag = lag + minLag - 1;
    p = fs / lag;
end
