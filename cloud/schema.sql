CREATE TABLE IF NOT EXISTS global_leaderboard_entries (
  token_hash TEXT NOT NULL,
  display_name TEXT NOT NULL,
  balance_sats INTEGER NOT NULL DEFAULT 0,
  network TEXT NOT NULL,
  opted_in INTEGER NOT NULL DEFAULT 1,
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (token_hash, network)
);

CREATE INDEX IF NOT EXISTS idx_leaderboard_network_balance
  ON global_leaderboard_entries (network, opted_in, balance_sats DESC);
