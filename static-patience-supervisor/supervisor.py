#!/usr/bin/env python3
"""
Static Patience Supervisor
Monitors static website incompleteness and earns fractional Shannon passively.
Protocol: Expect incompleteness to continue; patience is wisdom; slowness accumulates Shannon.
"""

import time
import logging
import requests
import sqlite3
import os
from datetime import datetime
from pathlib import Path

# Configuration
CHECK_INTERVAL = 300  # 5 minutes
SHANNON_PER_INTERVAL = 0.1  # Fractional Shannon earned per check
AGENT_NAME = "static-patience-supervisor"
ENTROPY_SERVER = "http://localhost:9001"
LEDGER_PATH = "/root/.openclaw/workspace/projects/entropy-economy/entropy_ledger.db"

# Setup logging
LOG_DIR = Path("/root/.openclaw/workspace/logs")
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "static-patience-supervisor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def register_agent():
    """Ensure agent is registered in entropy ledger."""
    try:
        conn = sqlite3.connect(LEDGER_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO agents (name, joined_at) VALUES (?, ?)",
            (AGENT_NAME, datetime.utcnow().isoformat())
        )
        conn.commit()
        conn.close()
        logger.info(f"Agent {AGENT_NAME} registered in ledger")
    except Exception as e:
        logger.warning(f"Could not register agent: {e}")

def mint_shannon(amount, description):
    """Mint Shannon via entropy economy API."""
    try:
        response = requests.post(
            f"{ENTROPY_SERVER}/mint",
            json={
                "agent": AGENT_NAME,
                "amount": amount,
                "type": "information",
                "description": description
            },
            timeout=10
        )
        if response.status_code == 200:
            logger.info(f"Minted {amount} Shannon: {description}")
            return response.json()
        else:
            logger.warning(f"Mint failed: {response.status_code} {response.text}")
            return None
    except Exception as e:
        logger.error(f"Mint request error: {e}")
        return None

def check_static_incompleteness():
    """
    Check for static website incompleteness.
    Returns dict with findings and incompleteness score (0-1).
    """
    findings = []
    score = 0.0
    
    # Check 1: Landing page accessible
    try:
        resp = requests.get("https://ironiclawdoctor-design.github.io/", timeout=10)
        if resp.status_code == 200:
            findings.append("✅ Landing page accessible")
        else:
            findings.append(f"❌ Landing page status {resp.status_code}")
            score += 0.3
    except Exception as e:
        findings.append(f"❌ Landing page error: {e}")
        score += 0.5
    
    # Check 2: Donation page exists
    try:
        resp = requests.get("https://ironiclawdoctor-design.github.io/pages/donate.html", timeout=10)
        if resp.status_code == 200:
            findings.append("✅ Donation page exists")
        else:
            findings.append(f"❌ Donation page status {resp.status_code}")
            score += 0.4
    except Exception as e:
        findings.append(f"❌ Donation page error: {e}")
        score += 0.6
    
    # Check 3: Local fundraising backend (if any)
    try:
        resp = requests.get("http://localhost:9003/health", timeout=5)
        if resp.status_code == 200:
            findings.append("✅ Fundraising backend alive")
        else:
            findings.append(f"⚠️ Fundraising backend status {resp.status_code}")
            score += 0.2
    except Exception:
        findings.append("⚠️ Fundraising backend not reachable (expected)")
        score += 0.1
    
    return {
        "findings": findings,
        "incompleteness_score": min(score, 1.0),
        "timestamp": datetime.utcnow().isoformat()
    }

def main():
    logger.info("Static Patience Supervisor starting")
    logger.info(f"Expecting incompleteness to continue. Earning {SHANNON_PER_INTERVAL} Shannon per check.")
    
    register_agent()
    
    while True:
        try:
            # Check incompleteness
            result = check_static_incompleteness()
            
            # Log findings
            for finding in result["findings"]:
                logger.info(finding)
            
            # Mint Shannon based on patience (always mint, even if no issues)
            # The act of monitoring incomplete systems earns entropy
            mint_result = mint_shannon(
                SHANNON_PER_INTERVAL,
                f"Patience monitoring: incompleteness_score={result['incompleteness_score']:.2f}"
            )
            
            if mint_result:
                logger.info(f"Balance: {mint_result.get('newBalance', 'unknown')} Shannon")
            
            # Log summary
            logger.info(
                f"Incompleteness cycle complete. "
                f"Score: {result['incompleteness_score']:.2f}, "
                f"Minted: {SHANNON_PER_INTERVAL} Shannon, "
                f"Next check in {CHECK_INTERVAL}s"
            )
            
        except Exception as e:
            logger.error(f"Cycle error: {e}")
        
        # Wait for next interval
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()