// Open Booth — Configuration
// Copy this file to config.js and update the values for your deployment.
//
//   cp config.example.js config.js
//
// config.js is loaded by recorder.html and monitor.html.
// It is gitignored — your settings won't be committed.

const OB_CONFIG = {

  // ── REQUIRED ──────────────────────────────────────────────────────
  // Set these to your server's URL after deploying (see docs/VPS_SETUP.md).
  // Leave as null to run in local-only mode (IndexedDB cache, no server upload).

  UPLOAD_ENDPOINT:   null,   // e.g. 'https://your-domain.com/upload'
  SESSION_STATE_URL: null,   // e.g. 'https://your-domain.com/session-state'

  // ── OPTIONAL ──────────────────────────────────────────────────────
  // Defaults are fine for most setups. Uncomment to override.

  // SERVER_CHUNK_MS:   10000,   // Server upload cadence (ms)
  // IDB_CHUNK_MS:      30000,   // Local cache cadence (ms)
  // SERVER_VIDEO_KBPS: 800,     // Server stream bitrate (kbps)
  // LOCAL_VIDEO_KBPS:  4000,    // Local cache bitrate (kbps)
  // POLL_INTERVAL_MS:  5000,    // Monitor poll interval (ms)
  // STALE_THRESHOLD_S: 30,      // Monitor: warn if no chunk in N seconds
  // DEAD_THRESHOLD_S:  90,      // Monitor: error if no chunk in N seconds
  // COMMAND_POLL_MS:   2000,    // Host command polling interval (ms)
};
