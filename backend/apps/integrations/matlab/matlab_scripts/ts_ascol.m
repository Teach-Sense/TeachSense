function [y] = ts_ascol(x)
% TS_ASCOL  Coerce input into a column vector of doubles.
%   Used by all TeachSense MATLAB scripts for robust input normalisation,
%   regardless of whether Python passed a row/column/list.

    if isnumeric(x)
        y = double(x(:));
    elseif islogical(x)
        y = double(x(:));
    else
        try
            y = double(x(:));
        catch
            y = zeros(0, 1);
        end
    end
end
