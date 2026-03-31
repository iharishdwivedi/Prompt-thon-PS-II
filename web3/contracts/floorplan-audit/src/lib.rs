#![no_std]
use soroban_sdk::{
    contract, contractimpl, contracttype,
    symbol_short, Address, Env, String, Vec, Map,
};

// ── Data Types ───────────────────────────────────────────────

/// Feature B: Material Procurement Ledger — top material per element
#[contracttype]
#[derive(Clone)]
pub struct Materials {
    pub outer: String,
    pub spine: String,
    pub partition: String,
    pub slab: String,
    pub column: String,
}

/// Feature A + B + C: Audit Certificate + Material Ledger + Ownership Registry
#[contracttype]
#[derive(Clone)]
pub struct AnalysisReport {
    pub floor_hash:     String,   // SHA256 of floor plan image
    pub owner:          Address,  // Feature C: ownership registry
    pub timestamp:      u64,
    pub outer_walls:    u32,
    pub spine_walls:    u32,
    pub partitions:     u32,
    pub materials:      Materials, // Feature B: procurement ledger
    pub report_summary: String,   // Feature A: AI report summary
    pub compliance:     bool,
}

#[contract]
pub struct FloorplanAuditContract;

#[contractimpl]
impl FloorplanAuditContract {

    /// Feature A + B + C — Store analysis result on-chain
    pub fn store_report(
        env: Env,
        floor_hash: String,
        owner: Address,
        outer_walls: u32,
        spine_walls: u32,
        partitions: u32,
        materials: Materials,
        report_summary: String,
    ) -> bool {
        owner.require_auth();

        let compliance = (outer_walls + spine_walls) >= partitions;
        let timestamp  = env.ledger().timestamp();

        let report = AnalysisReport {
            floor_hash: floor_hash.clone(),
            owner: owner.clone(),
            timestamp,
            outer_walls,
            spine_walls,
            partitions,
            materials,
            report_summary,
            compliance,
        };

        // Store report keyed by floor_hash
        let mut reports: Map<String, AnalysisReport> = env
            .storage().persistent()
            .get(&symbol_short!("REPORTS"))
            .unwrap_or(Map::new(&env));
        reports.set(floor_hash.clone(), report);
        env.storage().persistent().set(&symbol_short!("REPORTS"), &reports);

        // Feature C: ownership registry
        let mut owners: Map<String, Address> = env
            .storage().persistent()
            .get(&symbol_short!("OWNERS"))
            .unwrap_or(Map::new(&env));
        owners.set(floor_hash.clone(), owner);
        env.storage().persistent().set(&symbol_short!("OWNERS"), &owners);

        // Track all hashes
        let mut hashes: Vec<String> = env
            .storage().persistent()
            .get(&symbol_short!("HASHES"))
            .unwrap_or(Vec::new(&env));
        hashes.push_back(floor_hash);
        env.storage().persistent().set(&symbol_short!("HASHES"), &hashes);

        compliance
    }

    /// Feature A — Retrieve audit certificate by floor hash
    pub fn get_report(env: Env, floor_hash: String) -> Option<AnalysisReport> {
        let reports: Map<String, AnalysisReport> = env
            .storage().persistent()
            .get(&symbol_short!("REPORTS"))
            .unwrap_or(Map::new(&env));
        reports.get(floor_hash)
    }

    /// Feature C — Check who owns a floor plan hash
    pub fn get_owner(env: Env, floor_hash: String) -> Option<Address> {
        let owners: Map<String, Address> = env
            .storage().persistent()
            .get(&symbol_short!("OWNERS"))
            .unwrap_or(Map::new(&env));
        owners.get(floor_hash)
    }

    /// Get all stored floor plan hashes
    pub fn get_all_hashes(env: Env) -> Vec<String> {
        env.storage().persistent()
            .get(&symbol_short!("HASHES"))
            .unwrap_or(Vec::new(&env))
    }

    /// Get total number of reports stored
    pub fn report_count(env: Env) -> u32 {
        let hashes: Vec<String> = env
            .storage().persistent()
            .get(&symbol_short!("HASHES"))
            .unwrap_or(Vec::new(&env));
        hashes.len()
    }
}
