function [y] = ts_denoise(x, fs)
% TS_DENOISE  Reduce stationary background noise in a lecture recording.
%
%   Inputs:
%       x  - column vector of audio samples (double, [-1,1])
%       fs - sample rate (Hz)
%   Output:
%       y  - denoised audio (column vector)
%
%   Method: spectral subtraction via a Wiener-style filter estimated from a
%   short noise-only prefix (assumed first 0.5 s of room tone). Falls back to
%   a gentle high-pass if the signal is too short.

    try
        x = ts_ascol(x);
        N = numel(x);

        % High-pass to kill low-frequency HVAC / rumble.
        if fs > 0
            [b, a] = butter(4, max(20, fs*0.01) / (fs/2), 'high');
            x = filtfilt(b, a, x);
        end

        % Estimate noise profile from the first 0.5 s (or 10% if shorter).
        noiseLen = min(N, max(round(0.5*fs), round(0.1*N)));
        if noiseLen > 16
            noise = x(1:noiseLen);
            noisePsd = mean(abs(fft(noise, 1024)).^2, 1);
            win = hann(1024, 'periodic');
            nframes = floor((N - 1024) / 512) + 1;
            out = zeros(N, 1);
            normWin = sum(win);
            for k = 1:nframes
                seg = x((k-1)*512 + (1:1024)) .* win;
                X = fft(seg);
                S = abs(X).^2;
                % Wiener filter using estimated noise PSD.
                G = max(0, 1 - (noisePsd ./ (S + eps)));
                Y = X .* G;
                rec = real(ifft(Y));
                start = (k-1)*512 + 1;
                out(start:start+1023) = out(start:start+1023) + rec .* win;
            end
            % Normalise overlap-add window.
            out = out / max(normWin, eps);
            y = out(1:N);
        else
            y = x;
        end
        y = y / max(max(abs(y)), 1);
    catch ME
        warning('ts_denoise failed: %s', ME.message);
        y = ts_ascol(x);
    end
end
