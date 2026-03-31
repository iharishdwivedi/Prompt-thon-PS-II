from flask import Flask, render_template, request, jsonify
import hashlib
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from stellar_sdk import (
    Keypair, Network, TransactionBuilder, scval
)
from stellar_sdk import SorobanServer
from stellar_sdk.exceptions import PrepareTransactionException

app = Flask(__name__)

# ── Config ────────────────────────────────────────────────────
RPC_URL     = "https://soroban-testnet.stellar.org"
NETWORK     = Network.TESTNET_NETWORK_PASSPHRASE
CONTRACT_ID = "CBBWSQMWM7T62IVPZTPPAMHS4N2HZ6AVNFSV2SDW27TTR6AS7FIMDX3J"
SECRET_KEY  = os.getenv("STELLAR_SECRET_KEY", "")
keypair     = Keypair.from_secret(SECRET_KEY)


def _invoke_contract(function_name, args, readonly=False):
    """
    Core Stellar SDK integration function.
    Builds, simulates, signs and submits a Soroban contract invocation.
    For readonly calls (get_*), only simulates — no fee charged.
    """
    server  = SorobanServer(RPC_URL)
    account = server.load_account(keypair.public_key)

    tx = (
        TransactionBuilder(
            source_account=account,
            network_passphrase=NETWORK,
            base_fee=100,
        )
        .append_invoke_contract_function_op(
            contract_id=CONTRACT_ID,
            function_name=function_name,
            parameters=args,
        )
        .set_timeout(30)
        .build()
    )

    # Simulate to get footprint + fee
    sim = server.simulate_transaction(tx)
    if hasattr(sim, "error") and sim.error:
        raise Exception(f"Simulation error: {sim.error}")

    if readonly:
        # For read-only calls just return the simulation result
        if sim.results and len(sim.results) > 0:
            return {"result_xdr": sim.results[0].xdr, "readonly": True}
        return {"result_xdr": None, "readonly": True}

    # Prepare (attach footprint + resource fee)
    tx = server.prepare_transaction(tx)
    tx.sign(keypair)

    response = server.send_transaction(tx)
    tx_hash  = response.hash

    # Poll for confirmation
    import time
    for _ in range(20):
        time.sleep(2)
        status = server.get_transaction(tx_hash)
        if status.status == "SUCCESS":
            return {"tx_hash": tx_hash, "status": "SUCCESS"}
        if status.status == "FAILED":
            raise Exception(f"Transaction failed: {tx_hash}")

    return {"tx_hash": tx_hash, "status": "PENDING"}


# ── Routes ────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", contract_id=CONTRACT_ID,
                           public_key=keypair.public_key)


@app.route("/api/hash", methods=["POST"])
def compute_hash():
    """Generate SHA-256 fingerprint of the floor plan image — used as on-chain key"""
    data      = request.get_json()
    image_b64 = data.get("image_data", "")
    floor_hash = hashlib.sha256(image_b64.encode()).hexdigest()[:32]
    return jsonify({"floor_hash": floor_hash})


@app.route("/api/store_report", methods=["POST"])
def store_report():
    """
    Feature A + B + C — Anchor analysis on Stellar blockchain.
    Calls store_report() on the Soroban contract with:
      - floor_hash   : SHA-256 of the floor plan image (Feature C: ownership key)
      - owner        : wallet address (Feature C: ownership registry)
      - wall counts  : outer, spine, partition (Feature A: audit data)
      - materials    : top recommended material per element (Feature B: procurement ledger)
      - report_summary: first 200 chars of Gemini AI report (Feature A: audit cert)
    """
    try:
        d = request.get_json()

        floor_hash = d["floor_hash"]
        outer      = int(d.get("outer_walls", 0))
        spine      = int(d.get("spine_walls", 0))
        parts      = int(d.get("partitions", 0))
        summary    = d.get("report_summary", "")[:200]

        # Build Materials struct as a Soroban map
        materials_map = scval.to_map({
            scval.to_symbol("outer"):     scval.to_string(d.get("top_material_outer", "N/A")),
            scval.to_symbol("spine"):     scval.to_string(d.get("top_material_spine", "N/A")),
            scval.to_symbol("partition"): scval.to_string(d.get("top_material_part",  "N/A")),
            scval.to_symbol("slab"):      scval.to_string(d.get("top_material_slab",  "N/A")),
            scval.to_symbol("column"):    scval.to_string(d.get("top_material_col",   "N/A")),
        })

        args = [
            scval.to_string(floor_hash),
            scval.to_address(keypair.public_key),
            scval.to_uint32(outer),
            scval.to_uint32(spine),
            scval.to_uint32(parts),
            materials_map,
            scval.to_string(summary),
        ]

        result = _invoke_contract("store_report", args, readonly=False)
        compliance = (outer + spine) >= parts

        return jsonify({
            "success":    True,
            "floor_hash": floor_hash,
            "tx_hash":    result.get("tx_hash", ""),
            "status":     result.get("status", ""),
            "compliance": compliance,
            "message":    "Report anchored on Stellar blockchain ✓"
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/get_report/<floor_hash>", methods=["GET"])
def get_report(floor_hash):
    """Feature A — Retrieve audit certificate from blockchain by floor hash"""
    try:
        args   = [scval.to_string(floor_hash)]
        result = _invoke_contract("get_report", args, readonly=True)
        return jsonify({"success": True, "result_xdr": result.get("result_xdr")})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/get_owner/<floor_hash>", methods=["GET"])
def get_owner(floor_hash):
    """Feature C — Floor plan ownership registry lookup"""
    try:
        args   = [scval.to_string(floor_hash)]
        result = _invoke_contract("get_owner", args, readonly=True)
        return jsonify({"success": True, "result_xdr": result.get("result_xdr")})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/all_hashes", methods=["GET"])
def all_hashes():
    """Get all registered floor plan hashes from on-chain storage"""
    try:
        result = _invoke_contract("get_all_hashes", [], readonly=True)
        return jsonify({"success": True, "result_xdr": result.get("result_xdr")})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/report_count", methods=["GET"])
def report_count():
    """Get total number of reports stored on chain"""
    try:
        result = _invoke_contract("report_count", [], readonly=True)
        return jsonify({"success": True, "result_xdr": result.get("result_xdr")})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5050)
