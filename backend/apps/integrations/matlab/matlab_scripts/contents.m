% TEACHSENSE MATLAB AUDIO ALGORITHMS
%
% This folder is auto-added to the MATLAB path by MatlabAudioService. To add a
% new algorithm, simply drop a new <name>.m file here that follows the
% ts_<task>(x, fs, ...) calling convention and register a method in
% apps/integrations/matlab/service.py that calls it via _run_script().
%
% Available functions:
%   ts_ascol.m           - robust column-vector coercion (internal helper)
%   ts_denoise.m         - stationary noise reduction (spectral subtraction)
%   ts_normalize.m       - peak normalisation / soft AGC
%   ts_remove_echo.m     - single-channel dereverberation
%   ts_extract_features.m- feature set (RMS, ZCR, spectral, MFCC, pitch, VAD ratio)
%   ts_voice_activity.m  - voice activity detection (segment list)
%   ts_spectrogram.m     - magnitude spectrogram (matrix + axes)
%
% All functions degrade gracefully: on error they issue a warning and return
% the input (or zeros) so the Python pipeline never crashes.
