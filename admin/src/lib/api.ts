import { remoteGet, remoteServicesEnabled } from './remote-services';

export const API_BASE = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8002';

const TOKEN_KEY = 'wv_auth_token';

export interface User {
  id: number;
  username: string;
  role: 'admin' | 'user' | 'pending';
  email?: string;
  is_active?: boolean;
  has_wallet_passphrase?: boolean;
  wallet_count?: number;
  token?: string;
}

export interface WalletSecurityStatus {
  has_wallet_passphrase: boolean;
  unlocked: boolean;
  expires_at: number | null;
  unlock_ttl_seconds?: number;
  legacy_wallet_count: number;
  wallet_count: number;
  admin_cannot_decrypt: boolean;
  mainnet_acknowledged?: boolean;
  mainnet_ack_at?: string | null;
}

export interface AuthConfig {
  open_registration: boolean;
  auto_approve_users: boolean;
  session_idle_seconds?: number;
  session_max_age_days?: number;
  csrf_model?: string;
  auth_primary?: string;
}

export type AssetType = 'btc' | 'xmr';

export interface Wallet {
  id: number;
  user_id: number;
  name: string;
  asset_type: AssetType;
  xpub?: string;
  derivation_path?: string;
  network: string;
  xmr_primary_address?: string | null;
  xmr_restore_height?: number;
  xmr_account_index?: number;
  receive_index?: number;
  last_synced_height?: number;
  encryption_version?: number;
  created_at: string;
}

export interface CreateWalletResponse extends Wallet {
  mnemonic?: string;
}

export interface UtxoRef {
  txid: string;
  vout: number;
}

export interface Utxo {
  txid: string;
  vout: number;
  amount_sats: number;
  address?: string;
  confirmations: number;
  is_spent?: number;
  derivation_index?: number;
  label?: string | null;
  frozen?: number | boolean;
  is_change?: number | boolean;
  privacy_flags?: string | null;
}

export interface WalletTransaction {
  txid: string;
  direction: string;
  amount_sats: number;
  fee_sats?: number;
  block_height?: number;
  timestamp?: string;
  label?: string | null;
}

export interface SendPreview {
  address: string;
  amount_sats: number;
  fee_sats: number;
  fee_rate_sat_vb: number;
  change_sats: number;
  input_count: number;
  estimated_vsize: number;
}

export interface SendResult {
  txid: string;
  fee_sats: number;
  amount_sats: number;
  hex: string;
}

export interface SwapProviderInfo {
  id: string;
  name: string;
  type: string;
  custodial: boolean;
  disclosure: string;
  enabled: boolean;
}

export interface SwapQuote {
  quote_id: string;
  provider: string;
  from_asset: AssetType;
  to_asset: AssetType;
  send_amount_atomic: number;
  receive_amount_atomic: number;
  amount_sats: number;
  rate: number;
  fees: { network: number; provider: number };
  min: number;
  max: number;
  expires_at: string;
  disclosure: string;
  network?: string;
}

export interface SwapExecuteResult {
  swap_id: number;
  status: string;
  from_asset: AssetType;
  to_asset: AssetType;
  send_amount_atomic: number;
  receive_amount_atomic: number;
  deposit_address?: string | null;
  deposit_amount_atomic?: number | null;
  destination_wallet_id: number;
  provider: string;
  expires_at?: string;
  deposit_address_checksum_valid?: boolean | null;
  instructions?: string;
}

export interface SwapRecord {
  id: number;
  user_id: number;
  quote_id: string;
  provider_id: string;
  from_asset: AssetType;
  to_asset: AssetType;
  send_amount_atomic: number;
  receive_amount_atomic: number;
  status: string;
  deposit_address?: string | null;
  deposit_amount_atomic?: number | null;
  destination_wallet_id?: number | null;
  from_txid?: string | null;
  to_txid?: string | null;
  from_network?: string | null;
  to_network?: string | null;
  explorer_links?: { from: string | null; to: string | null };
  created_at: string;
  settled_at?: string | null;
  expires_at?: string | null;
}

export interface StatusResponse {
  user: { id: number; username: string; role: string };
  wallets: Wallet[];
  wallet_count: number;
  network: string;
  tor_enabled: boolean;
  synced: boolean;
  wallet_security?: WalletSecurityStatus;
}

export interface Balance {
  confirmed_sats: number;
  unconfirmed_sats: number;
  total_sats: number;
}

export interface SyncStatus {
  wallet_id: number;
  synced: boolean;
  progress: number;
  block_height: number;
  message?: string;
}

export interface WalletStats {
  balance_history: { date: string; sats: number }[];
  tx_count: number;
  total_received_sats: number;
  total_sent_sats: number;
  fees_paid_sats: number;
  utxo_count: number;
  privacy_score: number;
}

export type PrivacyRecommendationSeverity = 'info' | 'warning' | 'critical';

export interface PrivacyRecommendation {
  id: string;
  severity: PrivacyRecommendationSeverity;
  title: string;
  detail: string;
}

export interface PrivacySummary {
  privacy_score: number;
  private_utxos: number;
  non_private_utxos: number;
  entities: string[];
  exchange_exposure?: number;
  flag_counts?: Record<string, number>;
  recommendations?: PrivacyRecommendation[];
  message?: string;
}

export interface WalletLabel {
  wallet_id: number;
  target_type: string;
  target_id: string;
  label: string;
  entity?: string | null;
}

export interface AuditEntry {
  id: number;
  user_id?: number;
  username?: string;
  action: string;
  details?: string;
  ip?: string;
  timestamp: string;
}

export interface LeaderboardEntry {
  rank: number;
  display_name: string;
  balance_sats: number;
  updated_at?: string;
}

export interface LeaderboardResponse {
  network: string;
  entries: LeaderboardEntry[];
}

export interface LeaderboardMe {
  network: string;
  opted_in: boolean;
  display_name: string | null;
  balance_sats: number;
  rank: number | null;
}

export interface SystemInfo {
  settings: Record<string, string>;
  node_height: number;
  peer_count: number;
  version: string;
  message?: string;
}

export interface NetworkStatus {
  tor_enabled: boolean;
  tor_managed: boolean;
  tor_proxy: string | null;
  tor_bootstrap_complete: boolean;
  network_wizard_complete: boolean;
  backend: string;
  light_client: boolean;
}

export function getToken(): string | null {
  if (typeof sessionStorage === 'undefined') return null;
  return sessionStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  sessionStorage.removeItem(TOKEN_KEY);
}

function authHeaders(): HeadersInit {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
      ...options.headers
    }
  });

  const rotated = res.headers.get('X-Session-Token');
  if (rotated) setToken(rotated);

  if (res.status === 401) {
    clearToken();
    if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
      window.location.href = '/login';
    }
    throw new Error('Not authenticated');
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    const detail = typeof body.detail === 'string' ? body.detail : 'Request failed';
    throw new Error(detail);
  }

  return res.json();
}

export const api = {
  login: async (username: string, password: string) => {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(typeof body.detail === 'string' ? body.detail : 'Login failed');
    }

    const user = (await res.json()) as User & { token: string };
    if (user.token) setToken(user.token);
    return user;
  },
  logout: async () => {
    try {
      await request<{ status: string }>('/api/security/wallet/lock', {
        method: 'POST',
        body: '{}'
      }).catch(() => {});
      await request<{ status: string }>('/api/auth/logout', {
        method: 'POST',
        body: '{}'
      });
    } finally {
      clearToken();
    }
  },
  authConfig: () => request<AuthConfig>('/api/auth/config'),
  register: (username: string, password: string, email?: string) =>
    request<{ id: number; username: string; role: string }>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password, email })
    }),
  changePassword: (current_password: string, new_password: string) =>
    request<{ status: string }>('/api/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({ current_password, new_password })
    }),
  me: () => request<User>('/api/auth/me'),
  walletSecurity: () => request<WalletSecurityStatus>('/api/security/wallet'),
  setupWalletPassphrase: (passphrase: string) =>
    request<WalletSecurityStatus>('/api/security/wallet/passphrase/setup', {
      method: 'POST',
      body: JSON.stringify({ passphrase })
    }),
  unlockWallet: (passphrase: string) =>
    request<WalletSecurityStatus>('/api/security/wallet/unlock', {
      method: 'POST',
      body: JSON.stringify({ passphrase })
    }),
  lockWallet: () =>
    request<WalletSecurityStatus>('/api/security/wallet/lock', {
      method: 'POST',
      body: '{}'
    }),
  migrateLegacyWallets: (passphrase: string) =>
    request<WalletSecurityStatus & { migrated_wallets?: number }>(
      '/api/security/wallet/migrate',
      { method: 'POST', body: JSON.stringify({ passphrase }) }
    ),
  changeWalletPassphrase: (current_passphrase: string, new_passphrase: string) =>
    request<WalletSecurityStatus>('/api/security/wallet/passphrase/change', {
      method: 'POST',
      body: JSON.stringify({ current_passphrase, new_passphrase })
    }),
  acknowledgeMainnetRisks: () =>
    request<WalletSecurityStatus>('/api/security/wallet/mainnet/acknowledge', {
      method: 'POST',
      body: JSON.stringify({ acknowledged: true })
    }),
  status: () => request<StatusResponse>('/api/status'),
  settings: () => request<Record<string, string>>('/api/settings'),
  logs: (tail = 200, level?: string, search?: string) => {
    const params = new URLSearchParams({ tail: String(tail) });
    if (level) params.set('level', level);
    if (search) params.set('search', search);
    return request<{ lines: string[]; path: string }>(`/api/logs?${params}`);
  },
  wallets: (asset_type?: AssetType) =>
    request<Wallet[]>(
      asset_type ? `/api/wallets?asset_type=${encodeURIComponent(asset_type)}` : '/api/wallets'
    ),
  createWallet: (name: string, options?: { network?: string; asset_type?: AssetType }) =>
    request<CreateWalletResponse>('/api/wallets', {
      method: 'POST',
      body: JSON.stringify({
        name,
        network: options?.network,
        asset_type: options?.asset_type ?? 'btc'
      })
    }),
  importWallet: (
    name: string,
    mnemonic: string,
    options?: { network?: string; asset_type?: AssetType }
  ) =>
    request<Wallet>('/api/wallets/import', {
      method: 'POST',
      body: JSON.stringify({
        name,
        mnemonic,
        network: options?.network,
        asset_type: options?.asset_type ?? 'btc'
      })
    }),
  syncWallet: (id: number) =>
    request<SyncStatus>(`/api/wallets/${id}/sync`, { method: 'POST', body: '{}' }),
  walletBalance: (id: number) => request<Balance>(`/api/wallets/${id}/balance`),
  walletSync: (id: number) => request<SyncStatus>(`/api/wallets/${id}/sync-status`),
  walletUtxos: (id: number) => request<Utxo[]>(`/api/wallets/${id}/utxos`),
  updateUtxo: (id: number, txid: string, vout: number, patch: { frozen?: boolean; label?: string }) =>
    request<Utxo>(`/api/wallets/${id}/utxos/${txid}/${vout}`, {
      method: 'PATCH',
      body: JSON.stringify(patch)
    }),
  walletTransactions: (id: number) =>
    request<WalletTransaction[]>(`/api/wallets/${id}/transactions`),
  walletReceive: (id: number, options?: { subaddress?: boolean }) =>
    request<{
      address: string;
      network: string;
      index?: number;
      address_type?: string;
      asset_type?: string;
    }>(
      `/api/wallets/${id}/receive-address${
        options?.subaddress === false ? '?subaddress=false' : ''
      }`
    ),
  walletStats: (id: number) => request<WalletStats>(`/api/wallets/${id}/stats`),
  walletPrivacy: (id: number) => request<PrivacySummary>(`/api/wallets/${id}/privacy`),
  sendPreview: (
    id: number,
    address: string,
    amount_sats: number,
    fee_rate_sat_vb?: number,
    utxos?: UtxoRef[]
  ) =>
    request<SendPreview>(`/api/wallets/${id}/send/preview`, {
      method: 'POST',
      body: JSON.stringify({ address, amount_sats, fee_rate_sat_vb, utxos })
    }),
  sendFunds: (
    id: number,
    address: string,
    amount_sats: number,
    fee_rate_sat_vb?: number,
    utxos?: UtxoRef[]
  ) =>
    request<SendResult>(`/api/wallets/${id}/send`, {
      method: 'POST',
      body: JSON.stringify({ address, amount_sats, fee_rate_sat_vb, utxos })
    }),
  exportWallet: (id: number) =>
    request<{ id: number; name: string; network: string; xpub?: string; derivation_path?: string }>(
      `/api/wallets/${id}/export`
    ),
  deleteWallet: (id: number) =>
    request<{ status: string; wallet_id: number }>(`/api/wallets/${id}`, { method: 'DELETE' }),
  walletLabels: (id: number, target_type?: string) => {
    const q = target_type ? `?target_type=${encodeURIComponent(target_type)}` : '';
    return request<WalletLabel[]>(`/api/wallets/${id}/labels${q}`);
  },
  setWalletLabel: (
    id: number,
    target_type: string,
    target_id: string,
    label: string,
    entity?: string
  ) =>
    request<WalletLabel>(`/api/wallets/${id}/labels/${target_type}/${encodeURIComponent(target_id)}`, {
      method: 'PUT',
      body: JSON.stringify({ label, entity })
    }),
  swapProviders: () =>
    request<{ providers: SwapProviderInfo[] }>('/api/swap/providers'),
  swapQuote: (from_asset: AssetType, to_asset: AssetType, amount_sats: number, provider?: string) => {
    const params = new URLSearchParams({
      from: from_asset,
      to: to_asset,
      amount_sats: String(amount_sats)
    });
    if (provider) params.set('provider', provider);
    return request<SwapQuote>(`/api/swap/quote?${params}`);
  },
  swapExecute: (quote_id: string, destination_wallet_id: number) =>
    request<SwapExecuteResult>('/api/swap/execute', {
      method: 'POST',
      body: JSON.stringify({ quote_id, destination_wallet_id })
    }),
  swapHistory: (limit = 50) =>
    request<{ swaps: SwapRecord[] }>(`/api/swap/history?limit=${limit}`),
  swapStatus: (swap_id: number) => request<SwapRecord>(`/api/swap/${swap_id}`),
  swapAttachTxids: (swap_id: number, txids: { from_txid?: string; to_txid?: string }) =>
    request<SwapRecord>(`/api/swap/${swap_id}/txids`, {
      method: 'PATCH',
      body: JSON.stringify(txids)
    }),
  adminUsers: () => request<User[]>('/api/admin/users'),
  adminCreateUser: (username: string, password: string, role = 'user') =>
    request<User>('/api/admin/users', {
      method: 'POST',
      body: JSON.stringify({ username, password, role })
    }),
  adminUpdateUser: (id: number, data: { role?: string; is_active?: boolean }) =>
    request<User>(`/api/admin/users/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data)
    }),
  adminAuditLog: (limit = 50) => request<AuditEntry[]>(`/api/admin/audit-log?limit=${limit}`),
  adminSystem: () => request<SystemInfo>('/api/admin/system'),
  adminUpdateSettings: (data: {
    network?: string;
    backend_type?: string;
    backend_uri?: string;
    tor_enabled?: boolean;
    coordinator_uri?: string;
    allow_mainnet?: boolean;
    mainnet_enable_acknowledged?: boolean;
    xmr_wallet_rpc_uri?: string;
    wallet_unlock_ttl?: number;
  }) =>
    request<Record<string, string>>('/api/admin/settings', {
      method: 'PATCH',
      body: JSON.stringify(data)
    }),
  leaderboard: (network = 'testnet', limit = 100) =>
    remoteServicesEnabled()
      ? remoteGet<LeaderboardResponse>(
          `/api/leaderboard?network=${encodeURIComponent(network)}&limit=${limit}`
        )
      : request<LeaderboardResponse>(
          `/api/leaderboard?network=${encodeURIComponent(network)}&limit=${limit}`
        ),
  leaderboardMe: (network = 'testnet') =>
    request<LeaderboardMe>(`/api/leaderboard/me?network=${encodeURIComponent(network)}`),
  leaderboardOptIn: (display_name: string, opted_in: boolean) =>
    request<LeaderboardMe>('/api/leaderboard/opt-in', {
      method: 'POST',
      body: JSON.stringify({ display_name, opted_in })
    }),
  networkStatus: () => request<NetworkStatus>('/api/network/status'),
  completeNetworkSetup: (skip_tor = false) =>
    request<{ network_wizard_complete: boolean; tor_enabled: boolean }>(
      '/api/network/complete-setup',
      {
        method: 'POST',
        body: JSON.stringify({ skip_tor })
      }
    )
};
