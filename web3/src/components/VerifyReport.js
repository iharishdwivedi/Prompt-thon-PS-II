/**
 * VerifyReport Component
 * Feature A — Retrieve audit certificate from blockchain
 * Calls: GET /api/get_report/:hash
 * Contract function: get_report(floor_hash) → Option<AnalysisReport>
 */
import { verifyReport } from '../App.js';

export class VerifyReport {
    async verify(floorHash) {
        return verifyReport(floorHash);
    }
}
