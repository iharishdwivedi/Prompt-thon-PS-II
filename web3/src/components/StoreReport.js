/**
 * StoreReport Component
 * Feature A + B + C — Anchor analysis on Stellar blockchain
 *
 * Calls: POST /api/store_report
 * Contract function: store_report(floor_hash, owner, outer_walls,
 *                    spine_walls, partitions, materials, report_summary)
 */

import { anchorReport, generateHash } from '../App.js';

export class StoreReport {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
    }

    async hashImage(file) {
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = async (e) => {
                const b64  = e.target.result.split(',')[1] || e.target.result;
                const data = await generateHash(b64);
                resolve(data.floor_hash);
            };
            reader.readAsDataURL(file);
        });
    }

    async submit(formData) {
        return anchorReport(formData);
    }
}
