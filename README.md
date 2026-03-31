# Autonomous Structural Intelligence System (ASIS)

---

## What This Project Does (Plain English)

You upload a photo of a floor plan. The system reads it, figures out where all the walls are, builds a 3D model of the building, recommends which construction materials to use and why, generates a full engineering report using AI, and then permanently records everything on the Stellar blockchain so nobody can ever dispute or alter the results.

There is also a blockchain verification panel on the home page — so clients, banks, and regulators can verify any report directly without running the pipeline.

---

## Project Vision

Construction projects fail because of three things: wrong materials, disputed reports, and no proof of who decided what. ASIS solves all three. The AI pipeline handles the analysis. The blockchain handles the trust.

---

## Quick Start (1 minute)

```bash
# 1. Clone and navigate
git clone https://github.com/<username>/Prompt-thon-PS-II.git
cd Prompt-thon-PS-II

# 2. Set up keys
copy .env.example .env
# Edit .env with your Gemini API key and Stellar testnet secret

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run (2 terminals)
# Terminal 1:
cd final_app && streamlit run app.py

# Terminal 2:
cd web3 && python app.py

# 5. Open browser
# Streamlit: http://localhost:8501
# Blockchain: http://localhost:5050
```

---

## Full Pipeline — 7 Stages

```
Upload → OCR → Vision → 3D Model → Materials → AI Report → Blockchain
  0        1      2         3           4            5           6
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FLOOR PLAN IMAGE (PNG / JPG)                     │
│              Uploaded by architect / engineer / client              │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
               ┌───────────────▼───────────────┐
               │         STAGE 0 — UPLOAD       │
               │  tempfile → st.session_state   │
               │  + Blockchain Verification     │
               │    Panel (read-only, no upload │
               │    needed for verify/ownership)│
               └───────────────┬───────────────┘
                               │
               ┌───────────────▼───────────────┐
               │      STAGE 1 — OCR             │
               │  EasyOCR → readtext()          │
               │  Regex normalize room labels   │
               │  Filter < 20% confidence       │
               │  ─────────────────────────     │
               │  OUT: room_counts, dimensions  │
               └───────────────┬───────────────┘
                               │
               ┌───────────────▼───────────────┐
               │    STAGE 2 — VISION ANALYSIS   │
               │  OpenCV: Grayscale → Otsu →    │
               │  Morph cleanup → Canny →       │
               │  HoughLinesP → ConnectedComp   │
               │  Graph: node snap (15px) →     │
               │  junction classify → wall type │
               │  ─────────────────────────     │
               │  OUT: outer / spine / partition│
               └───────────────┬───────────────┘
                               │
               ┌───────────────▼───────────────┐
               │      STAGE 3 — 3D MODEL        │
               │  try/vision_parser.py          │
               │  Angle snap → columns →        │
               │  furniture detection           │
               │  try/try_app.py → Three.js     │
               │  BoxGeometry per wall, TWEEN   │
               │  camera, click-to-select       │
               │  ─────────────────────────     │
               │  OUT: self-contained HTML      │
               └───────────────┬───────────────┘
                               │
               ┌───────────────▼───────────────┐
               │   STAGE 4 — MATERIAL ANALYSIS  │
               │  Book1.xlsx → openpyxl         │
               │  SCORE_MAP: Low/Med/High → 1-4 │
               │  Weighted tradeoff formula:    │
               │  score = (ws×S + wd×D)/(wc×C) │
               │  Different weights per element │
               │  ─────────────────────────     │
               │  OUT: top 3 materials + scores │
               └───────────────┬───────────────┘
                               │
               ┌───────────────▼───────────────┐
               │      STAGE 5 — AI REPORT       │
               │  prompt_builder.py injects     │
               │  wall counts + scores + weights│
               │  gemini_client.py →            │
               │  Gemini 2.5 Flash API          │
               │  5-section engineering report  │
               │  ─────────────────────────     │
               │  OUT: report text + .txt file  │
               └───────────────┬───────────────┘
                               │
               ┌───────────────▼───────────────┐
               │   STAGE 6 — BLOCKCHAIN AUDIT   │
               │  SHA-256(image) → floor_hash   │
               │  Flask → stellar-sdk →         │
               │  Soroban contract on Stellar   │
               │  Testnet                       │
               │  ─────────────────────────     │
               │  store_report() → sign → send  │
               │  ─────────────────────────     │
               │  Feature A: Audit Certificate  │
               │  Feature B: Material Ledger    │
               │  Feature C: Ownership Registry │
               └───────────────┬───────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                         OUTPUTS                                     │
│  ✅ 3D Interactive Model (HTML)                                     │
│  ✅ Material Recommendations with tradeoff scores                   │
│  ✅ AI Structural Engineering Report (downloadable .txt)            │
│  ✅ Blockchain Audit Certificate (Stellar Testnet)                  │
│  ✅ Immutable Ownership Registry                                    │
│  ✅ Material Procurement Ledger on-chain                            │
└─────────────────────────────────────────────────────────────────────┘
```

### Tech Stack per Stage

| Stage | Technology |
|---|---|
| OCR | EasyOCR, OpenCV, Python regex |
| Vision | OpenCV (Otsu, HoughLinesP, ConnectedComponents) |
| 3D Model | Three.js, TWEEN.js, HTML5 Canvas |
| Materials | openpyxl, custom weighted scoring formula |
| AI Report | Google Gemini 2.5 Flash, google-genai SDK |
| Blockchain | Stellar Soroban (Rust), stellar-sdk, Flask |
| Frontend | Streamlit, HTML/CSS/JS |

---

## Stage-by-Stage Code Explanation

---

### Stage 0 — Upload + Blockchain Verification Panel (`final_app/app.py`)

The home page has a **two-column layout**:

**Left column — Upload:**
The user uploads a floor plan image (PNG/JPG). The file is saved to a temp path using Python's `tempfile` module. This path is stored in `st.session_state` and passed through every subsequent stage.

**Right column — Blockchain Verification Panel (no upload needed):**
Anyone — a client, bank, inspector, or regulator — can use these 3 features directly from the home page without running the pipeline:

- **🔍 Verify a Report** — paste a floor plan hash → instantly confirm the structural report is authentic and untampered on Stellar blockchain
- **👤 Check Ownership** — look up which wallet address registered a floor plan design. Immutable IP ownership proof for architects
- **📚 Browse Public Registry** — see every floor plan analysis ever anchored on Stellar. Full tamper-proof audit trail for regulators

Each feature has a collapsible expander with a live form that calls the Flask blockchain server at `http://localhost:5050`. These are read-only calls — no transaction fee, no signing needed.

---

### Stage 1 — OCR Detection (`stage1/`)

**Files:**
- `stage1/parser/floorplan_parser.py` — orchestrator
- `stage1/parser/ocr_detector.py` — actual OCR logic

**How it works:**

`ocr_detector.py` uses **EasyOCR** (a deep learning OCR library) to read text from the floor plan image. It:
1. Resizes the image to at least 1000px wide so small text is readable
2. Runs `reader.readtext()` which returns bounding boxes + text + confidence scores
3. Filters out anything below 20% confidence
4. Categorizes each detected text into one of three types:
   - `dimension` — numbers like "3.5m", "1200mm"
   - `room_label` — words like "BEDROOM", "KITCHEN", "BATHROOM"
   - `annotation` — everything else

The `_normalize_room()` function uses regex patterns to map variations ("BED ROOM", "BEDRM", "BEDROOM") all to the same key `"bedroom"`. This handles messy real-world floor plan text.

`floorplan_parser.py` calls the detector, counts rooms using Python's `Counter`, and saves the result as a JSON file.

**Output:** `{ room_counts: {bedroom: 2, bathroom: 1}, ocr: {dimensions: [...], room_labels: [...]} }`

---

### Stage 2 — Vision Analysis (`stage2_3/` and `try/`)

**Files:**
- `stage2_3/image_processor.py` — CV pipeline
- `stage2_3/graph_builder.py` — wall graph
- `try/vision_parser.py` — improved version used in Stage 4's 3D model

**How it works:**

`image_processor.py` runs a full OpenCV pipeline:

1. **Grayscale** — converts BGR to gray
2. **Otsu thresholding** — automatically finds the best threshold to separate walls (dark) from background (white). Otsu's algorithm minimizes intra-class variance — no manual tuning needed
3. **Morphological cleanup** — `MORPH_OPEN` removes noise, `MORPH_CLOSE` fills gaps in wall lines
4. **Canny edge detection** — finds sharp edges (wall boundaries)
5. **Hough Line Transform** (`HoughLinesP`) — detects straight line segments. Parameters: threshold=60 (minimum votes), minLineLength=30px, maxLineGap=8px
6. **Connected components** — finds enclosed regions (rooms) by dilating walls, inverting, then labeling connected white regions. Rooms smaller than 4000px² are ignored

`graph_builder.py` converts the raw line segments into a proper graph:
- **Node snapping** — endpoints within 15px of each other are merged into one node (prevents floating walls from tiny coordinate offsets)
- **Degree counting** — counts how many walls connect at each node
- **Junction classification** — degree 1 = endpoint, 2 = corner, 3 = T-junction, 4 = X-junction
- **Wall classification** — walls near the image border (within 12% margin) = `load_bearing_outer`, walls in the top 25th percentile by length = `load_bearing_spine`, everything else = `partition`

`try/vision_parser.py` is an improved version that also:
- Snaps near-orthogonal angles to exact 0°/90° (prevents impossible geometries)
- Detects columns (small square contours, area 400–5000px²)
- Detects furniture (beds, TV units) from contour aspect ratios

---

### Stage 3 — 3D Model (`stage2_3/threejs_exporter.py`)

**How it works:**

Takes the classified wall segments and generates a self-contained HTML file with a Three.js 3D scene. No server needed — just open in a browser.

The coordinate conversion: pixel coordinates → meters using `SCALE = 0.05` (1px = 5cm). Y-axis is flipped because image coordinates go top-down but 3D space goes bottom-up.

Each wall becomes a `BoxGeometry` rotated to match the wall's angle using `Math.atan2(dz, dx)`. Wall thickness: 0.6m for load-bearing, 0.3m for partitions. Partition walls are semi-transparent (opacity 0.75).

The scene includes:
- Ambient + directional + hemisphere lights with shadow mapping
- Custom orbit controls (no external dependency — pure mouse event math)
- Distance labels as canvas-rendered sprites
- Room center markers as cyan cylinders
- Toggle button for distance labels

`try/try_app.py` is the upgraded version used in Stage 4 — adds columns, furniture (beds with mattress + pillows, TV units with screen), click-to-select with TWEEN camera flyto, and tooltip on hover.

---

### Stage 4 — Material Analysis (`stage4/`)

**Files:**
- `stage4/material_db.py` — reads Excel database
- `stage4/tradeoff_engine.py` — scoring algorithm

**How it works:**

`material_db.py` reads `Book1.xlsx` using `openpyxl`. Each row is a material with columns: Name, Cost, Strength, Durability, Best Use. Text values like "Medium–High" are mapped to numbers using `SCORE_MAP` (Low=1, Medium=2, High=3, Very High=4).

`tradeoff_engine.py` implements a **weighted cost-strength tradeoff formula**:

```
score = (w_strength × strength + w_durability × durability) / (w_cost × cost + 0.01)
```

The weights are different for each structural element type — this is the key engineering insight:

| Element | Strength | Durability | Cost | Reasoning |
|---|---|---|---|---|
| Outer walls | 0.55 | 0.15 | 0.30 | Carry vertical + lateral loads. Strength dominates |
| Spine walls | 0.50 | 0.25 | 0.25 | Floor loads across spans. Strength + durability balanced |
| Partitions | 0.20 | 0.20 | 0.60 | Non-structural. Cost dominates |
| Slab | 0.40 | 0.35 | 0.25 | Cyclic loading + moisture. Durability critical |
| Columns | 0.65 | 0.20 | 0.15 | Point loads. Strength is everything |

The 3D model in Stage 4 is generated using `try/try_app.py` (upgraded builder) via `importlib` — this gives the full furniture, columns, click-to-select, and TWEEN camera flyto features.

Materials are first filtered by `best_use` keyword matching. If fewer than 3 match, all materials are considered. Top 3 are returned with full explanations citing actual numbers.

---

### Stage 5 — AI Report (`stage5/`)

**Files:**
- `stage5/prompt_builder.py` — builds the structured prompt
- `stage5/gemini_client.py` — calls Gemini API

**How it works:**

`prompt_builder.py` takes the Stage 2 geometry data and Stage 4 material recommendations and builds a detailed structured prompt. The prompt explicitly tells Gemini to write 5 sections: Floor Plan Overview, Material Recommendations, Cost-Strength Tradeoff Analysis, Structural Concerns, and Summary. It injects actual numbers (wall counts, scores, weights) so Gemini cannot give generic advice.

`gemini_client.py` calls `gemini-2.5-flash` using the `google-genai` SDK. Uses non-streaming mode so the full report is returned at once.

The report is rendered in Streamlit using a regex splitter that detects section headings and renders them as styled `<h3>` tags, while body text goes through `st.markdown` which handles bold, bullets, and tables from Gemini's output.

The API key is loaded from the `GEMINI_API_KEY` environment variable (set in `.env`).

A **Download Report** button at the bottom saves the full AI report as a `.txt` file named `ASIS_report_{hash[:8]}.txt`.

---

### Stage 6 — Blockchain Audit (`web3/`)

**Files:**
- `web3/contracts/floorplan-audit/src/lib.rs` — Soroban smart contract (Rust)
- `web3/app.py` — Flask backend with Stellar SDK integration
- `web3/src/App.js` — frontend JS entry point with all Stellar SDK API calls
- `web3/src/components/` — StoreReport, VerifyReport, OwnerRegistry, OnChainLedger components
- `web3/templates/index.html` — standalone dApp frontend (4 tabs)
- `web3/static/css/style.css` — dark theme UI
- `web3/static/js/main.js` — frontend JS calling Flask API

**What the blockchain adds (3 real-world features):**

- **Feature A — Audit Certificate:** Every analysis is anchored on-chain with a SHA-256 floor plan hash. Anyone can call `get_report(hash)` to verify the report is authentic and untampered. Use case: client disputes the engineer's material choice 6 months later — the blockchain shows exactly what was recommended on exactly what date.

- **Feature B — Material Procurement Ledger:** Top recommended materials (Fly Ash Brick, TMT Steel, AAC Blocks, etc.) are stored on-chain per structural element. Contractors cannot dispute what materials were specified. Use case: a bank verifies the structural report before releasing construction funds.

- **Feature C — Ownership Registry:** The wallet address that submitted the floor plan is recorded on-chain. Proves who registered which design and when. Use case: two architects claim they designed the same floor plan — whoever anchored it first on Stellar wins.

**Smart Contract (Rust/Soroban):**

The contract stores `AnalysisReport` structs keyed by floor plan hash in Soroban's persistent storage. Three storage maps:
- `REPORTS` — hash → full report struct (Feature A)
- `OWNERS` — hash → wallet address (Feature C)
- `HASHES` — ordered list of all hashes (Feature B)

The `Materials` struct bundles all 5 material recommendations into one argument to stay within Soroban's 10-parameter limit.

`store_report()` calls `owner.require_auth()` — the transaction must be signed by the owner's wallet. This is what makes ownership provable and non-repudiable.

**Flask Backend (Python/Stellar SDK):**

`web3/app.py` uses `stellar-sdk` to call the contract:
1. `SorobanServer.load_account()` — gets the current sequence number
2. `TransactionBuilder.append_invoke_contract_function_op()` — builds the contract call
3. `SorobanServer.simulate_transaction()` — gets the resource footprint and fee estimate
4. `SorobanServer.prepare_transaction()` — attaches footprint to the transaction
5. `tx.sign(keypair)` — signs with the secret key
6. `SorobanServer.send_transaction()` — broadcasts to testnet
7. Polls `get_transaction()` every 2 seconds until confirmed

For read-only calls (`get_report`, `get_owner`, `get_all_hashes`, `report_count`) only simulation is run — no fee, no signing needed. Arguments encoded as Soroban XDR using `scval.to_string()`, `scval.to_uint32()`, `scval.to_address()`, `scval.to_map()`.

**Streamlit Stage 6 (4 tabs):**

Stage 6 auto-populates all fields from the pipeline:
- Floor hash: SHA-256 of the uploaded image file bytes
- Wall counts: from Stage 2 summary
- Materials: top-ranked material from each Stage 4 category
- Report summary: first 200 chars of Stage 5 Gemini output

1. **Anchor Report** — sends POST to Flask `/api/store_report`, shows tx hash + Stellar Explorer link
2. **Verify Certificate** — GET `/api/get_report/{hash}`, shows XDR result
3. **Ownership Registry** — GET `/api/get_owner/{hash}`, shows registered wallet
4. **On-Chain Registry** — GET `/api/all_hashes` + `/api/report_count`, shows full ledger + block explorer link

---

## Deployed Smart Contract

- **Contract ID:** `CBBWSQMWM7T62IVPZTPPAMHS4N2HZ6AVNFSV2SDW27TTR6AS7FIMDX3J`
- **Network:** Stellar Testnet
- **Deploy TX:** `2d9e7a8954590d4f05686a4b4a978b3719615a7b5d798487fbe1c83a502fc4b2`
- **WASM Hash:** `ce30515357b2749f967eba6bc21ef5e9c7fc2fff10294574729d23b4a961f4ab`
- **Explorer:** https://stellar.expert/explorer/testnet/contract/CBBWSQMWM7T62IVPZTPPAMHS4N2HZ6AVNFSV2SDW27TTR6AS7FIMDX3J

---

## Repository Structure

```
approach2/
├── final_app/
│   └── app.py                  ← Main Streamlit app (all 7 stages + blockchain panel on home)
│
├── stage1/
│   └── parser/
│       ├── floorplan_parser.py ← OCR orchestrator
│       └── ocr_detector.py     ← EasyOCR + room classification
│
├── stage2_3/
│   ├── image_processor.py      ← OpenCV pipeline (grayscale→Hough)
│   ├── graph_builder.py        ← Wall graph + junction classification
│   └── threejs_exporter.py     ← Generates 3D HTML viewer
│
├── stage4/
│   ├── material_db.py          ← Reads Book1.xlsx
│   ├── tradeoff_engine.py      ← Weighted cost-strength scoring
│   └── Book1.xlsx              ← Materials database
│
├── stage5/
│   ├── prompt_builder.py       ← Builds structured Gemini prompt
│   └── gemini_client.py        ← Calls Gemini 2.5 Flash API
│
├── try/
│   ├── vision_parser.py        ← Improved CV with angle snapping + columns
│   └── try_app.py              ← Upgraded 3D builder with furniture + click (used in Stage 4)
│
└── web3/
    ├── contracts/
    │   └── floorplan-audit/
    │       ├── src/lib.rs      ← Soroban smart contract (Rust)
    │       └── Cargo.toml      ← Contract dependencies (soroban-sdk v22)
    ├── src/
    │   ├── components/
    │   │   ├── StoreReport.js  ← Feature A+B+C: anchor analysis on-chain
    │   │   ├── VerifyReport.js ← Feature A: retrieve audit certificate
    │   │   ├── OwnerRegistry.js← Feature C: ownership lookup
    │   │   └── OnChainLedger.js← Feature B: procurement ledger
    │   ├── App.js              ← All Stellar SDK API call functions
    │   └── index.js            ← Entry point
    ├── static/
    │   ├── css/style.css       ← Dark theme UI
    │   └── js/main.js          ← Frontend JS (tab switching, form handling)
    ├── templates/
    │   └── index.html          ← Standalone dApp (4 tabs)
    ├── public/                 ← Screenshots
    ├── app.py                  ← Flask backend + Stellar SDK integration
    ├── requirements.txt        ← Python dependencies
    ├── package.json            ← JS project metadata
    ├── Cargo.toml              ← Rust workspace manifest
    └── README.md               ← Web3 specific docs
```

---

## Key Features

- **OCR** — EasyOCR reads room labels and dimensions from any floor plan image
- **Computer Vision** — Otsu threshold + Hough lines + connected components detects walls and rooms
- **Graph Analysis** — Node snapping + degree counting classifies junctions and wall types
- **3D Visualization** — Self-contained Three.js HTML with orbit controls, shadows, furniture, click-to-select
- **Material Tradeoff** — Weighted formula with engineering-justified weights per element type, sourced from Book1.xlsx
- **AI Report** — Gemini 2.5 Flash generates a 5-section structural engineering report, downloadable as .txt
- **Blockchain Home Panel** — Clients and regulators can verify reports, check ownership, and browse the registry directly from the home page without running the pipeline
- **Blockchain Stage 6** — Stellar Soroban stores audit certificate + material ledger + ownership registry with 4-tab interface

---

## How to Run

### Step 1 — Clone the repo
```bash
git clone https://github.com/<your-username>/Prompt-thon-PS-II.git
cd Prompt-thon-PS-II
```

### Step 2 — Set up environment variables
```bash
# Copy the example env file (Windows)
copy .env.example .env

# Or on Linux/Mac:
# cp .env.example .env

# Open .env and fill in:
# GEMINI_API_KEY=your_gemini_api_key_here
# STELLAR_SECRET_KEY=your_stellar_testnet_secret_key_here
```

**To get your API keys:**
- **Gemini API Key:** Visit https://aistudio.google.com/app/apikey → Create new API key
- **Stellar Secret Key:** Visit https://laboratory.stellar.org/#account-creator?network=test → Create a Testnet account (Copy the Secret Key)

### Step 3 — Install all dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Run the Streamlit App
```bash
cd final_app
streamlit run app.py
```

The app will open at `http://localhost:8501`

### Step 5 — Run the Blockchain Flask Server (separate terminal)
```bash
cd web3
python app.py
# Runs on http://localhost:5050
# Must be running for Stage 6 and home page blockchain features
```

### Step 6 — Standalone Web3 dApp (optional)
Open http://localhost:5050 in your browser (Flask must be running)

---

## Usage Guide

### From the Streamlit App Home Page

**Two columns:**

**Left side — Upload & Run Pipeline:**
1. **Upload a floor plan image** (PNG or JPG) of any building layout
2. Click **Run Full Pipeline** 
3. Watch the progress as the system:
   - 🔍 Extracts room labels and dimensions (OCR)
   - 👁️ Detects walls and structural elements (computer vision)
   - 📐 Generates interactive 3D model
   - 📊 Recommends materials based on engineering tradeoffs
   - 🤖 Generates AI structural report (Gemini)
   - ⛓️ Records everything on Stellar blockchain

**Right side — Blockchain Verification Panel (no upload needed):**
- **🔍 Verify a Report** — Paste a floor plan hash to check if a report is authentic on-chain
- **👤 Check Ownership** — Look up which wallet registered a floor plan design
- **📚 Browse Public Registry** — View all analyses anchored on Stellar testnet

### Step-by-Step Pipeline Walkthrough

#### **Stage 0 — Home Page**
- Upload your floor plan image
- Optionally verify reports or check ownership from the blockchain panel

#### **Stage 1 — OCR Detection**
- The system extracts all text from your floor plan
- Identifies room labels (BEDROOM, KITCHEN, BATHROOM, etc.)
- Records dimensions (3.5m, 1200mm, etc.)
- Result: Room count summary

#### **Stage 2 — Vision Analysis**
- Computer vision pipeline detects walls and structure
- Classifies wall types:
  - **Outer walls** (load-bearing, around perimeter)
  - **Spine walls** (load-bearing, interior support)
  - **Partitions** (non-structural, interior walls)
- Identifies junctions and connected rooms
- Result: Interactive visualization of wall structure

#### **Stage 3 — 3D Model**
- Generates interactive 3D building model (Three.js)
- Features:
  - Rotate, zoom, pan with mouse
  - Click walls to see properties
  - Distance labels between rooms
  - Color-coded wall types
- **Download:** HTML file for offline viewing

#### **Stage 4 — Material Analysis**
- System analyzes the structure and recommends best materials
- Considers:
  - **Strength** (load capacity)
  - **Durability** (weather, wear resistance)
  - **Cost** (budget constraints)
- Weights are different for each element type (outer walls prioritize strength, partitions prioritize cost)
- Result: Top 3 recommended materials with detailed cost-strength tradeoff analysis

#### **Stage 5 — AI Structural Report**
- Gemini 2.5 Flash generates a professional 5-section report:
  1. Floor Plan Overview (room count, dimensions)
  2. Material Recommendations (with scores and reasoning)
  3. Cost-Strength Tradeoff Analysis (why these materials)
  4. Structural Concerns (potential issues to watch)
  5. Summary (key takeaways)
- **Download:** Save report as `.txt` file with timestamp

#### **Stage 6 — Blockchain Audit**
- Anchor your analysis on Stellar blockchain
- **Features:**
  - **Audit Certificate** — Proves report is authentic & untampered
  - **Material Ledger** — Records recommended materials forever
  - **Ownership Registry** — Shows who registered the design
- Get blockchain transaction hash + Stellar Explorer link
- Anyone can verify the report using the Verification Panel (Stage 0)

---

## Example Workflow

```
1. Upload floor_plan.jpg
   ↓
2. System detects: 3 bedrooms, 2 bathrooms, kitchen, living room
   ↓
3. Walls classified: 2 outer, 1 spine, 4 partitions
   ↓
4. 3D model generated + downloaded
   ↓
5. Materials recommended: Fly Ash Brick (outer), TMT Steel (spine), Plasterboard (partitions)
   ↓
6. AI report generated: "Cost-effective and structurally sound for residential..."
   ↓
7. Report anchored on blockchain ⛓️
   ↓
8. Client receives: 3D model, AI report, blockchain certificate, materials list
```

---

## API Keys Setup

### Google Gemini API
1. Visit https://aistudio.google.com/app/apikey
2. Click **Create API Key**
3. Copy the key to your `.env` file

### Stellar Testnet Keys
1. Visit https://laboratory.stellar.org/#account-creator?network=test
2. Click **Generate Keypair**
3. Copy the **Secret Key** (not the public key) to your `.env` file
4. Fund your account with test lumens (optional for viewing features, required for anchoring)

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'streamlit'"
```bash
pip install -r requirements.txt
```

### "Error: GEMINI_API_KEY environment variable not set"
Make sure:
1. `.env.example` was copied to `.env` (not `.env.txt`)
2. Your `.env` file has: `GEMINI_API_KEY=your_actual_key_here`
3. The key is from https://aistudio.google.com/app/apikey

### "Connection error to localhost:5050"
Make sure Flask server is running:
```bash
cd web3
python app.py
```
(Run in a separate terminal)

### "Streamlit port 8501 already in use"
```bash
streamlit run app.py --server.port 8502
```

### "PIL Error: cannot identify image file"
Make sure your floor plan image is:
- PNG or JPG format
- Not corrupted
- Has clear visible walls

---

## Future Scope

- Auto-trigger blockchain anchor from Stage 5 without needing Flask running separately
- Multi-sig: require both architect + engineer wallet signatures before anchoring
- IPFS: store full PDF report on IPFS, anchor the CID on-chain
- Mainnet deployment for production use
- Mobile-responsive Streamlit layout
- Support for multi-storey floor plans (stack multiple floor analyses)

---

## About

ASIS is an open-source personal project for autonomous structural analysis and blockchain-based audit trails.
