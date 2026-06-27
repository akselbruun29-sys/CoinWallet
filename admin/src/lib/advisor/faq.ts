import type { FaqItem } from './types';

/** Static Bitcoin FAQ — no LLM, no market advice. */
export const BITCOIN_FAQ: FaqItem[] = [
	{
		id: 'what_is_bitcoin',
		question: 'What is Bitcoin?',
		answer:
			'Bitcoin is a decentralized digital currency secured by proof-of-work. You hold keys that control UTXOs on the blockchain — not a balance in a bank account.'
	},
	{
		id: 'what_are_utxos',
		question: 'What are UTXOs?',
		answer:
			'Unspent transaction outputs (UTXOs) are the coins your wallet can spend. Each receive creates one or more UTXOs. Coin Control lets you freeze or label individual outputs.'
	},
	{
		id: 'confirmations',
		question: 'Why wait for confirmations?',
		answer:
			'Confirmations measure how deep a transaction is in the blockchain. More confirmations reduce reorg risk. Many wallets wait for 1+ confirmation before treating funds as spendable.'
	},
	{
		id: 'fees',
		question: 'How do transaction fees work?',
		answer:
			'Miners prioritize transactions by fee rate (satoshis per virtual byte). Larger transactions (more inputs) cost more. You pay the difference between inputs and outputs.'
	},
	{
		id: 'passphrase_vs_seed',
		question: 'Passphrase vs recovery phrase?',
		answer:
			'Your 12/24-word recovery phrase restores the wallet. The wallet passphrase encrypts stored keys on this device — it is not the same as your login password or seed words.'
	},
	{
		id: 'address_reuse',
		question: 'Why avoid address reuse?',
		answer:
			'Reusing receive addresses links payments on-chain and hurts privacy. CoinWallet generates fresh addresses; the Privacy page flags reused addresses.'
	},
	{
		id: 'not_trading',
		question: 'Does CoinWallet trade for me?',
		answer:
			'No. CoinWallet is a non-custodial wallet. It does not run trading bots, signals, or automated swaps. You confirm every send manually.'
	},
	{
		id: 'testnet',
		question: 'What is testnet?',
		answer:
			'Testnet is a separate Bitcoin network for development. Coins are free from faucets and worthless. Use it to learn before moving to mainnet.'
	}
];
