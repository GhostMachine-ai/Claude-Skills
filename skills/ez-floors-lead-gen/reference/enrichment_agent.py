#!/usr/bin/env python3
"""
EZ Floors Lead Enrichment Agent
Enriches raw leads in Google Sheets with contact data, company size,
project history, and a lead score (1-5).

Requires:
    pip install anthropic google-auth google-auth-oauthlib google-api-python-client

Environment variables:
    ANTHROPIC_API_KEY  — Anthropic API key
    MASTER_SHEET_ID    — Google Sheets document ID
    SHEET_NAME         — Sheet tab name (default: Leads)
    GOOGLE_CREDS_FILE  — Path to Google service account JSON (default: creds.json)

Usage:
    python enrichment_agent.py --limit 20
    python enrichment_agent.py --limit 50 --dry-run
"""

import anthropic
import argparse
import json
import os
import sys
import time
from typing import Any


ENRICHMENT_PROMPT = """
You are a B2B lead enrichment agent for EZ Floors (a commercial flooring company in Katy, TX).
You will receive raw lead data scraped from Google Maps and must enrich it.

Target buyer types: General Contractors, Property Managers, Remodelers, Real Estate Investors, Restoration Companies.

For the provided company, use your knowledge to:
1. Estimate the likely owner/primary contact first name (if business name suggests sole proprietorship or is a person's name)
2. Estimate company size category: Solo (1), Small (2-10), Medium (11-50), Large (50+)
3. Assess commercial project likelihood based on business type and name
4. Assign a lead score 1-5 using this rubric:
   5 = Strong commercial buyer signal, high review count, active business
   4 = Likely commercial buyer, moderate review count
   3 = Possible commercial buyer, residential focus
   2 = Weak signal, minimal presence
   1 = Unlikely buyer or inactive business
5. Write a one-sentence outreach personalization note (what to reference in the cold opening)

Return ONLY valid JSON matching this schema:
{
  "contact_guess": "string or empty string",
  "size_category": "Solo | Small | Medium | Large",
  "commercial_likelihood": "High | Medium | Low",
  "score": 1-5,
  "outreach_note": "string"
}

Do not fabricate phone numbers, emails, or specific project details.
If uncertain about any field, use the most conservative estimate.
"""


def enrich_lead(client: anthropic.Anthropic, lead: dict[str, Any]) -> dict[str, Any]:
    """Call Claude to enrich a single lead."""
    lead_context = (
        f"Company: {lead.get('Company', '')}\n"
        f"Phone: {lead.get('Phone', '')}\n"
        f"Address: {lead.get('Address', '')}\n"
        f"City: {lead.get('City', '')}\n"
        f"Type: {lead.get('Type', '')}\n"
        f"Notes: {lead.get('Notes', '')}"
    )

    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=512,
        temperature=0,
        system=[
            {
                "type": "text",
                "text": ENRICHMENT_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": lead_context}],
    )

    text = response.content[0].text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def get_raw_leads(sheet_id: str, sheet_name: str, limit: int) -> list[dict]:
    """Fetch rows with Status='Raw' from Google Sheets."""
    try:
        from googleapiclient.discovery import build
        from google.oauth2 import service_account

        creds_file = os.environ.get("GOOGLE_CREDS_FILE", "creds.json")
        creds = service_account.Credentials.from_service_account_file(
            creds_file,
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        service = build("sheets", "v4", credentials=creds)
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=sheet_id, range=f"{sheet_name}!A:L")
            .execute()
        )
        rows = result.get("values", [])
        if not rows:
            return []

        headers = rows[0]
        leads = []
        for i, row in enumerate(rows[1:], start=2):
            while len(row) < len(headers):
                row.append("")
            lead = dict(zip(headers, row))
            lead["_row_index"] = i
            if lead.get("Status", "").strip() == "Raw":
                leads.append(lead)
                if len(leads) >= limit:
                    break
        return leads
    except Exception as e:
        print(f"[ERROR] Could not read Google Sheets: {e}", file=sys.stderr)
        return []


def write_enrichment(sheet_id: str, sheet_name: str, row_index: int, enrichment: dict) -> None:
    """Write enrichment data back to the Google Sheet row."""
    try:
        from googleapiclient.discovery import build
        from google.oauth2 import service_account

        creds_file = os.environ.get("GOOGLE_CREDS_FILE", "creds.json")
        creds = service_account.Credentials.from_service_account_file(
            creds_file,
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        service = build("sheets", "v4", credentials=creds)

        # Update Score (column K = index 11) and Status (column J = index 10)
        # and Notes (column L = index 12) with enrichment note
        note = (
            f"{enrichment.get('commercial_likelihood', '')} commercial likelihood | "
            f"{enrichment.get('size_category', '')} company | "
            f"{enrichment.get('outreach_note', '')}"
        )
        updates = [
            {"range": f"{sheet_name}!B{row_index}", "values": [[enrichment.get("contact_guess", "")]]},
            {"range": f"{sheet_name}!J{row_index}", "values": [["Enriched"]]},
            {"range": f"{sheet_name}!K{row_index}", "values": [[str(enrichment.get("score", ""))]]},
            {"range": f"{sheet_name}!L{row_index}", "values": [[note]]},
        ]
        body = {"valueInputOption": "RAW", "data": updates}
        service.spreadsheets().values().batchUpdate(spreadsheetId=sheet_id, body=body).execute()
    except Exception as e:
        print(f"[ERROR] Could not write to Google Sheets row {row_index}: {e}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich EZ Floors raw leads using Claude")
    parser.add_argument("--limit", type=int, default=20, help="Max leads to process")
    parser.add_argument("--dry-run", action="store_true", help="Print results without writing back")
    args = parser.parse_args()

    sheet_id = os.environ.get("MASTER_SHEET_ID", "")
    sheet_name = os.environ.get("SHEET_NAME", "Leads")

    if not sheet_id and not args.dry_run:
        print("[ERROR] MASTER_SHEET_ID environment variable not set", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic()
    leads = get_raw_leads(sheet_id, sheet_name, args.limit) if not args.dry_run else [
        {"Company": "ABC General Contracting", "Phone": "281-555-1234",
         "Address": "1234 Main St, Katy TX", "City": "Katy",
         "Type": "general contractor Katy TX", "Notes": "Rating: 4.5 | Reviews: 47",
         "Status": "Raw", "_row_index": 2}
    ]

    print(f"Processing {len(leads)} raw leads...\n")

    for lead in leads:
        company = lead.get("Company", "Unknown")
        print(f"Enriching: {company} ... ", end="", flush=True)
        try:
            enrichment = enrich_lead(client, lead)
            print(f"Score {enrichment.get('score')}/5 | {enrichment.get('commercial_likelihood')} commercial")
            if args.dry_run:
                print(f"  → {enrichment}")
            else:
                write_enrichment(sheet_id, sheet_name, lead["_row_index"], enrichment)
            time.sleep(0.5)  # Respect API rate limits
        except Exception as e:
            print(f"FAILED: {e}")

    print(f"\nDone. {len(leads)} leads processed.")


if __name__ == "__main__":
    main()
