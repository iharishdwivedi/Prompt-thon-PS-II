/**
 * ASIS — Autonomous Structural Intelligence System
 * Stellar Blockchain Integration — Main App
 *
 * This file is the frontend entry point for the Web3 dApp.
 * It wires together all components and handles routing between tabs.
 *
 * Integration flow:
 *   User fills form → JS calls Flask API (/api/store_report)
 *   Flask uses stellar-sdk to invoke Soroban contract on Stellar testnet
 *   Contract stores report immutably on-chain
 *   User can verify/query via /api/get_report, /api/get_owner, /api/all_hashes
 */

import { StoreReport }    from './components/StoreReport.js';
import { VerifyReport }   from './components/VerifyReport.js';
import { OwnerRegistry }  from './components/OwnerRegistry.js';
import { OnChainLedger }  from './components/OnChainLedger.js';

// ── Contract Config ───────────────────────────────────────────
export const CONTRACT_ID = 'CBBWSQMWM7T62IVPZTPPAMHS4N2HZ6AVNFSV2SDW27TTR6AS7FIMDX3J';
export const NETWORK     = 'testnet';
export const EXPLORER    = `https://stellar.expert/explorer/testnet/contract/${CONTRACT_ID}`;
export const FLASK_API   = 'http://localhost:5050';

// ── Stellar SDK Integration ───────────────────────────────────
// All blockchain calls go through Flask backend (app.py)
// which uses stellar-sdk to:
//   1. Load account sequence number
//   2. Build TransactionBuilder with invoke_contract_function_op
//   3. Simulate transaction (get footprint + fee)
//   4. Prepare transaction (attach footprint)
//   5. Sign with keypair
//   6. Send to Stellar testnet RPC
//   7. Poll for confirmation

export async function anchorReport(payload) {
    const res  = await fetch(`${FLASK_API}/api/store_report`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(payload),
    });
    return res.json();
}

export async function verifyReport(floorHash) {
    const res = await fetch(`${FLASK_API}/api/get_report/${floorHash}`);
    return res.json();
}

export async function getOwner(floorHash) {
    const res = await fetch(`${FLASK_API}/api/get_owner/${floorHash}`);
    return res.json();
}

export async function getAllHashes() {
    const res = await fetch(`${FLASK_API}/api/all_hashes`);
    return res.json();
}

export async function getReportCount() {
    const res = await fetch(`${FLASK_API}/api/report_count`);
    return res.json();
}

export async function generateHash(imageBase64) {
    const res  = await fetch(`${FLASK_API}/api/hash`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ image_data: imageBase64 }),
    });
    return res.json();
}
