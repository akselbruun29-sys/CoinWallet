export const PUBLIC_API_URL = (
  import.meta.env.VITE_REMOTE_SERVICES_URL ??
  import.meta.env.VITE_PUBLIC_API_URL ??
  ''
).replace(/\/$/, '');

export type LeaderboardEntry = {
  rank: number;
  display_name: string;
  balance_sats: number;
};

export type LeaderboardResponse = {
  network: string;
  entries: LeaderboardEntry[];
};

export async function fetchLeaderboard(
  network: string,
  limit = 100
): Promise<LeaderboardResponse> {
  const base =
    PUBLIC_API_URL ||
    (typeof window !== 'undefined' ? window.location.origin : 'http://127.0.0.1:8002');
  const res = await fetch(
    `${base}/api/leaderboard?network=${encodeURIComponent(network)}&limit=${limit}`
  );
  if (!res.ok) {
    throw new Error('Could not load leaderboard');
  }
  return res.json();
}

export function formatBtc(sats: number): string {
  const btc = sats / 100_000_000;
  if (btc >= 1) return `${btc.toFixed(4)} BTC`;
  if (btc >= 0.001) return `${btc.toFixed(6)} BTC`;
  return `${sats.toLocaleString()} sats`;
}
