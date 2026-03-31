/**
 * OnChainLedger Component
 * Feature B — Material procurement ledger
 * Calls: GET /api/all_hashes, GET /api/report_count
 * Contract functions: get_all_hashes() → Vec<String>, report_count() → u32
 */
import { getAllHashes, getReportCount } from '../App.js';

export class OnChainLedger {
    async loadAll() {
        const [hashes, count] = await Promise.all([getAllHashes(), getReportCount()]);
        return { hashes, count };
    }
}
