function [y] = ts_remove_echo(x, fs)
% TS_REMOVE_ECHO  Simple de-reverberation / echo suppression.
%
%   Inputs:
%       x  - column vector of audio samples
%       fs - sample rate (Hz)
%   Output:
%       y  - echo-reduced audio (column vector)
%
%   Method: short single-channel blind dereverberation via a spectral
%   decay (T60) attenuation in the STFT domain. Conservative defaults keep
%   speech natural while damping late reverberation.

    try
        x = ts_ascol(x);
        N = numel(x);
        if N < 1024
            y = x;
            return;
        end

        wlen = 1024;
        hop = wlen / 4;
        win = hann(wlen, 'periodic');

        % Estimate reverberation time from energy decay (simplified).
        env = abs(x);
        % Smoothed energy decay after the loudest frame.
        [~, idx] = max(env);
        tail = env(idx:end);
        if numel(tail) > 10
            decay = polyfit((1:numel(tail))', 20*log10(tail + eps), 1);
            rt60 = -60 / decay(1) / fs;   % seconds
            rt60 = max(0.05, min(rt60, 1.5));
        else
            rt60 = 0.3;
        end

        nframes = floor((N - wlen) / hop) + 1;
        out = zeros(N, 1);
        normWin = sum(win.^2);

        for k = 1:nframes
            seg = x((k-1)*hop + (1:wlen)) .* win;
            X = fft(seg);
            mag = abs(X);
            % Attenuate sustained energy to suppress reverberant tail.
            G = exp(-((0:(wlen/2))' * (1/fs)) / max(rt60/3, eps));
            G = [G; G(end:-1:2)];
            Y = X .* G;
            rec = real(ifft(Y));
            start = (k-1)*hop + 1;
            out(start:start+wlen-1) = out(start:start+wlen-1) + rec .* win;
        end
        out = out / max(normWin, eps);
        y = out(1:N);
        y = y / max(max(abs(y)), 1);
    catch ME
        warning('ts_remove_echo failed: %s', ME.message);
        y = ts_ascol(x);
    end
end
