function [y] = ts_normalize(x, fs)
% TS_NORMALIZE  Peak-normalise an audio signal to [-0.99, 0.99].
%
%   Inputs:
%       x  - column vector of audio samples
%       fs - sample rate (unused, kept for API symmetry)
%   Output:
%       y  - normalised audio (column vector)
%
%   Uses a soft AGC: peak normalisation with a small floor so near-silent
%   passages are not amplified into noise.

    try
        x = ts_ascol(x);
        peak = max(abs(x));
        target = 0.99;
        floorPeak = 1e-3;
        if peak > floorPeak
            gain = target / peak;
            % Limit gain to avoid blowing up quiet segments.
            gain = min(gain, 20);
            y = x * gain;
        else
            y = x;
        end
        % Safety clamp.
        y = max(min(y, 1), -1);
    catch ME
        warning('ts_normalize failed: %s', ME.message);
        y = ts_ascol(x);
    end
end
