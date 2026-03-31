# Autonomous Structural Intelligence System — Blockchain Audit Layer

**Personal Project**

---

## Project Title

ASIS Blockchain Audit — Stellar Soroban Smart Contract for Structural Analysis Certification

---

## Project Description

The ASIS Blockchain Audit Layer is the Web3 component of the Autonomous Structural Intelligence System. After the AI pipeline analyzes a floor plan (OCR → Computer Vision → 3D Model → Material Tradeoff → Gemini Report), this layer permanently anchors the results on the Stellar blockchain using a Soroban smart contract.

Every structural analysis becomes a tamper-proof, verifiable, on-chain record. Engineers, clients, and regulators can independently verify that a report was AI-generated, who submitted it, and what materials were recommended — without trusting any central authority.

---

## Project Vision

Construction disputes happen because reports get altered, materials get substituted, and nobody can prove who decided what. ASIS solves this by treating every AI-generated structural analysis as a blockchain record. Once anchored, the report hash, material recommendations, wall counts, and owner wallet are stored immutably on Stellar Soroban. No one can change them. Anyone can verify them.

---

## Key Features

- **Audit Certificate (Feature A)** — Every analysis is anchored on-chain with a SHA-256 floor plan hash. Anyone can call `get_report(hash)` to verify the report is authentic and untampered.

- **Material Procurement Ledger (Feature B)** — Top recommended materials (Fly Ash Brick, TMT Steel, AAC Blocks, Precast Concrete, Hollow Concrete Block) are stored on-chain per structural element. Contractors cannot dispute what materials were specified — it is immutably recorded.

- **Floor Plan Ownership Registry (Feature C)** — The wallet address that submitted the floor plan is recorded on-chain via `get_owner(hash)`. Architects have immutable proof of who registered which design and when.

- **Structural Compliance Flag** — The contract automatically evaluates whether load-bearing walls meet the minimum structural threshold `(outer + spine >= partitions)` and records a compliance boolean on-chain.

- **Full Stellar SDK Integration** — Flask backend calls the deployed Soroban contract using `stellar-sdk` v10 for all read and write operations. Arguments encoded as Soroban XDR using `scval.to_string()`, `scval.to_uint32()`, `scval.to_address()`, `scval.to_map()`.

- **Streamlit Stage 6** — The main ASIS pipeline has a Stage 6 that auto-populates all blockchain fields from the pipeline output and lets users anchor, verify, check ownership, and browse the registry — all from within the Streamlit app.

---

## Deployed Smart Contract Details

| Field | Value |
|---|---|
| **Contract ID** | `CBBWSQMWM7T62IVPZTPPAMHS4N2HZ6AVNFSV2SDW27TTR6AS7FIMDX3J` |
| **Network** | Stellar Testnet |
| **Deploy Transaction** | `2d9e7a8954590d4f05686a4b4a978b3719615a7b5d798487fbe1c83a502fc4b2` |
| **WASM Hash** | `ce30515357b2749f967eba6bc21ef5e9c7fc2fff10294574729d23b4a961f4ab` |
| **Block Explorer** | https://stellar.expert/explorer/testnet/contract/CBBWSQMWM7T62IVPZTPPAMHS4N2HZ6AVNFSV2SDW27TTR6AS7FIMDX3J |
| **Stellar Lab** | https://lab.stellar.org/r/testnet/contract/CBBWSQMWM7T62IVPZTPPAMHS4N2HZ6AVNFSV2SDW27TTR6AS7FIMDX3J |

> Screenshot of block explorer: `public/explorer_screenshot.png`

### Exported Contract Functions

| Function | Type | Description |
|---|---|---|
| `store_report` | Write | Anchors audit cert + materials + ownership on-chain |
| `get_report` | Read | Retrieves full audit certificate by floor hash |
| `get_owner` | Read | Returns wallet address that registered a floor plan |
| `get_all_hashes` | Read | Returns all registered floor plan hashes |
| `report_count` | Read | Returns total number of reports stored on-chain |

---

## UI Screenshots

> See `public/ui_store.png`, `public/ui_verify.png`, `public/ui_ownership.png`, `public/ui_registry.png`

---

## How Blockchain Integrates with the Pipeline

```
Stage 0: Upload Floor Plan
         ↓
Stage 1: OCR — reads room labels and dimensions
         ↓
Stage 2: Vision Analysis — detects walls, classifies load-bearing vs partition
         ↓
Stage 3: 3D Model — Three.js visualization
         ↓
Stage 4: Material Analysis — weighted tradeoff scoring from Book1.xlsx
         ↓
Stage 5: AI Report — Gemini 2.5 Flash generates 5-section engineering report
         ↓
Stage 6: Blockchain Anchor
         SHA-256 hash of floor plan image → unique fingerprint
         Wall counts from Stage 2 + top materials from Stage 4 + summary from Stage 5
         → store_report() called on Soroban contract
         → Transaction signed with Stellar keypair
         → Broadcast to Stellar testnet
         → Immutably stored forever
         ↓
Verify Anytime: get_report(hash) → proves report is authentic
Check Owner:    get_owner(hash)  → proves who submitted the design
Browse Ledger:  get_all_hashes() → full audit trail of all analyses
```

---

## Project Setup Guide

### Prerequisites
- Python 3.10+
- Rust + Cargo (`rustup-init.exe` from https://rustup.rs)
- Stellar CLI (`cargo install --locked stellar-cli`)
- wasm32v1-none target (`rustup target add wasm32v1-none`)

### 1. Install Python dependencies
```bash
cd web3
pip install flask stellar-sdk
```

### 2. Run the Flask backend
```bash
python app.py
# Runs on http://localhost:5050
```

### 3. Open the standalone dApp
Open http://localhost:5050 in your browser

### 4. Use from Streamlit (Stage 6)
```bash
cd final_app
pip install -r requirements.txt
streamlit run app.py
# Navigate through stages 0-5, then reach Stage 6: Blockchain
# Flask server must be running in a separate terminal
```

### 5. Build the smart contract (already deployed — for reference only)
```bash
cd web3
stellar network add testnet --rpc-url https://soroban-testnet.stellar.org --network-passphrase "Test SDF Network ; September 2015"
stellar keys add deployer --secret-key
stellar contract build
stellar contract deploy --wasm target/wasm32v1-none/release/floorplan_audit.wasm --source snake-charmers --network testnet
```

---

## Repository Structure

```
web3/
├── contracts/
│   └── floorplan-audit/
│       ├── src/
│       │   └── lib.rs          ← Soroban smart contract (Rust)
│       ├── Cargo.toml          ← Contract dependencies (soroban-sdk v22)
│       └── .gitignore
├── src/
│   ├── components/
│   │   ├── StoreReport.js      ← Feature A+B+C: anchor analysis on-chain
│   │   ├── VerifyReport.js     ← Feature A: retrieve audit certificate
│   │   ├── OwnerRegistry.js    ← Feature C: ownership lookup
│   │   └── OnChainLedger.js    ← Feature B: procurement ledger
│   ├── App.js                  ← Main app + all Stellar SDK API calls
│   └── index.js                ← Entry point
├── static/
│   ├── css/
│   │   └── style.css           ← Dark theme UI
│   └── js/
│       └── main.js             ← Frontend JS (tab switching, form handling)
├── templates/
│   └── index.html              ← Flask HTML template (4-tab dApp)
├── public/                     ← Screenshots for README
├── app.py                      ← Flask backend + Stellar SDK integration
├── requirements.txt            ← Python dependencies
├── package.json                ← JS project metadata
├── Cargo.toml                  ← Rust workspace manifest
├── .gitignore                  ← Excludes target/, __pycache__, .env
└── README.md                   ← This file
```

---

## Smart Contract Architecture

The contract (`contracts/floorplan-audit/src/lib.rs`) uses three persistent storage maps:

```rust
// Feature A: Audit Certificate
REPORTS: Map<String, AnalysisReport>   // floor_hash → full report

// Feature C: Ownership Registry  
OWNERS:  Map<String, Address>          // floor_hash → wallet address

// Feature B: Procurement Ledger
HASHES:  Vec<String>                   // ordered list of all hashes
```

The `Materials` struct bundles all 5 material recommendations into one argument to stay within Soroban's 10-parameter limit:

```rust
pub struct Materials {
    pub outer:     String,   // e.g. "Fly Ash Brick"
    pub spine:     String,   // e.g. "Hollow Concrete Block"
    pub partition: String,   // e.g. "AAC Blocks"
    pub slab:      String,   // e.g. "Precast Concrete Panel"
    pub column:    String,   // e.g. "TMT Steel Bars"
}
```

`store_report()` calls `owner.require_auth()` — the transaction must be signed by the owner's wallet. This is what makes ownership provable and non-repudiable.

---

## Stellar SDK Integration (Flask Backend)

`app.py` uses `stellar-sdk` v10 to invoke the contract:

```python
# 1. Load account (gets current sequence number)
account = server.load_account(keypair.public_key)

# 2. Build transaction with contract invocation
tx = TransactionBuilder(...).append_invoke_contract_function_op(
    contract_id=CONTRACT_ID,
    function_name="store_report",
    parameters=[
        scval.to_string(floor_hash),
        scval.to_address(keypair.public_key),
        scval.to_uint32(outer_walls),
        scval.to_uint32(spine_walls),
        scval.to_uint32(partitions),
        scval.to_map({...materials...}),
        scval.to_string(report_summary),
    ]
).build()

# 3. Simulate → get footprint + fee
sim = server.simulate_transaction(tx)

# 4. Prepare → attach footprint
tx = server.prepare_transaction(tx)

# 5. Sign + broadcast
tx.sign(keypair)
response = server.send_transaction(tx)

# 6. Poll for confirmation
status = server.get_transaction(tx_hash)
```

For read-only calls (`get_report`, `get_owner`, `get_all_hashes`, `report_count`), only simulation is run — no fee charged, no signing needed.

---

## Future Scope

- **Multi-sig approval** — require both architect and structural engineer wallet signatures before a report is finalized on-chain
- **NFT compliance badge** — mint a Stellar asset as a tradeable compliance certificate
- **IPFS integration** — store the full AI report PDF on IPFS, anchor the CID on-chain
- **Mainnet deployment** — move from testnet to Stellar mainnet for production use
- **Auto-trigger from pipeline** — automatically call `store_report` after Stage 5 completes without manual copy-paste
- **Report history dashboard** — show all past analyses for a given wallet address
- **Mobile-responsive UI** — optimize the dApp for mobile browsers

---

## About

ASIS is an open-source personal project for autonomous structural analysis and blockchain-based audit trails.
