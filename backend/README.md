# TeachSense Backend

Django REST + Channels backend for the TeachSense classroom-intelligence platform.

## Optional MATLAB Integration

TeachSense supports **optional** MATLAB-based advanced audio processing
(denoising, normalization, echo removal, feature extraction, voice activity
detection, spectrograms). MATLAB is **disabled by default** and is never
imported unless explicitly enabled, so the backend runs everywhere without a
MATLAB license.

### How it works

- Controlled by the `ENABLE_MATLAB` environment variable (default `False`).
- When disabled (or when the `matlabengine` package / MATLAB is not installed),
  the pipeline transparently falls back to the existing pure-Python processing.
- When enabled, a singleton MATLAB engine is started once per process, reused
  for all calls, auto-reconnects if it closes, and every call is timeout- and
  retry-protected.

### Enabling MATLAB

1. Install a licensed MATLAB on the host.
2. Install the MATLAB Engine API for Python in the same Python environment:
   ```bash
   # from the MATLAB root:
   cd "$(matlab -batch 'disp(matlabroot)')/extern/engines/python"
   python setup.py install
   ```
   (dependency is intentionally commented out in `requirements.txt`.)
3. Set the environment variables:
   ```env
   ENABLE_MATLAB=True
   MATLAB_START_TIMEOUT=60      # seconds to wait for MATLAB to start
   MATLAB_CALL_TIMEOUT=120      # per-call timeout for MATLAB computations
   MATLAB_RETRIES=2             # automatic retries on transient failures
   ```

### Extending

Add new `.m` algorithms to `apps/integrations/matlab/matlab_scripts/` and call
them from `apps/integrations/matlab/service.py` via `_run_script(...)`. No core
changes required.

See `docs/integration/OVERVIEW.md` for the full environment configuration.
