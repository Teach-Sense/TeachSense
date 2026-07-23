function [segments] = ts_voice_activity(x, fs)
% TS_VOICE_ACTIVITY  Voice activity detection (VAD).
%
%   Inputs:
%       x  - column vector of audio samples
%       fs - sample rate (Hz)
%   Output:
%       segments - Nx2 matrix of [start_sec, end_sec] speech segments
%
%   Method: energy + spectral-flatness thresholding in short frames, with
%   speech gaps shorter than 0.2 s merged. Returns an empty array when no
%   speech is found.

    segments = zeros(0, 2);
    try
        x = ts_ascol(x);
        N = numel(x);
        if N < 16 || fs <= 0
            return;
        end

        wlen = max(256, round(0.02*fs));   % 20 ms
        hop = round(wlen / 2);
        nframes = floor((N - wlen) / hop) + 1;

        energy = zeros(nframes, 1);
        flatness = zeros(nframes, 1);
        for k = 1:nframes
            seg = x((k-1)*hop + (1:wlen)) .* hann(wlen, 'periodic');
            energy(k) = rms(seg);
            sp = abs(fft(seg)).^2 + eps;
            gm = exp(mean(log(sp)));
            am = mean(sp);
            flatness(k) = gm / am;
        end

        eThr = 0.15 * max(energy);
        fThr = 0.5;
        isSpeech = (energy > eThr) & (flatness < fThr);

        % Merge short non-speech gaps (< 0.2 s ~ 10 frames at 20ms).
        maxGap = max(1, round(0.2 * fs / hop));
        merged = isSpeech;
        for k = 2:numel(isSpeech)
            if isSpeech(k) && ~isSpeech(k-1)
                gap = 0;
                j = k - 1;
                while j >= 1 && ~isSpeech(j) && gap < maxGap
                    merged(j) = true;
                    gap = gap + 1;
                    j = j - 1;
                end
            end
        end

        % Build segment list.
        k = 1;
        while k <= nframes
            if merged(k)
                startFrame = k;
                while k <= nframes && merged(k)
                    k = k + 1;
                end
                endFrame = k - 1;
                startSec = (startFrame - 1) * hop / fs;
                endSec = (endFrame * hop + wlen) / fs;
                segments(end+1, :) = [startSec, endSec];
            else
                k = k + 1;
            end
        end
    catch ME
        warning('ts_voice_activity failed: %s', ME.message);
        segments = zeros(0, 2);
    end
end
