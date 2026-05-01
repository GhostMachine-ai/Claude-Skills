# EZ Floors Lead Gen System — Setup Guide

## Prerequisites

- n8n community edition (self-hosted or n8n.cloud free tier)
- Google Cloud project with Places API enabled
- Google Sheets API credential configured in n8n
- Gmail credential configured in n8n (OAuth2)
- Twilio account (trial is sufficient for SMS)
- Python 3.10+ with `anthropic` package installed

## Credential Placeholders to Replace

Search all JSON files for these strings and replace with your actual values:

| Placeholder | Where to get it |
|------------|----------------|
| `YOUR_GOOGLE_MAPS_API_KEY` | Google Cloud Console → APIs & Services → Credentials |
| `YOUR_SHEETS_CREDENTIAL_ID` | n8n → Settings → Credentials → Google Sheets OAuth2 |
| `YOUR_GMAIL_CREDENTIAL_ID` | n8n → Settings → Credentials → Gmail OAuth2 |
| `YOUR_TWILIO_CREDENTIAL_ID` | n8n → Settings → Credentials → Twilio API |
| `YOUR_TWILIO_FROM_NUMBER` | Twilio Console → Phone Numbers (format: +12815551234) |
| `YOUR_MASTER_SHEET_ID` | Google Sheets URL: docs.google.com/spreadsheets/d/`THIS_PART`/edit |
| `YOUR_SHEET_NAME` | Tab name in your Google Sheet (e.g. "Leads") |
| `YOUR_CALENDLY_LINK` | Your Calendly public link |
| `ANTHROPIC_API_KEY` | Set as environment variable — do not hardcode |

## Google Sheet Setup

Create a Google Sheet with exactly these column headers in row 1 (order matters):

```
Company | Contact | Phone | Email | Address | City | Type | Source | Date Added | Status | Score | Notes
```

## n8n Import Steps

1. Open n8n → Workflows → Import from File
2. Import `scraper_workflow.json` — activate workflow
3. Import `outreach_sequences.json` — do NOT activate until credentials are configured
4. Import `referral_loop.json` — do NOT activate until credentials are configured
5. Replace all credential IDs in each workflow's node settings
6. Test manually:
   - Scraper: click "Execute Workflow" → verify rows appear in Google Sheet
   - Outreach: add a test row with Status="Enriched" → trigger manually
   - Referral: add a test row with Status="Job Complete" → trigger manually

## Enrichment Agent Setup

```bash
pip install anthropic
export ANTHROPIC_API_KEY=your_key_here
export MASTER_SHEET_ID=your_sheet_id_here
python enrichment_agent.py --limit 10
```

Run daily via cron or n8n Execute Command node:
```
0 3 * * * cd /path/to/reference && python enrichment_agent.py --limit 50
```

## Search Strings (Google Maps Places API)

The scraper uses these 6 queries by default. Add or remove in `scraper_workflow.json` Code node:

1. `general contractor Katy TX`
2. `property management company Houston TX`
3. `remodeling contractor Houston TX`
4. `real estate investor Houston TX`
5. `restoration company Houston TX`
6. `commercial contractor Houston TX`

## Lead Scoring Rubric (used by enrichment_agent.py)

| Score | Criteria |
|-------|----------|
| 5 | 50+ Google reviews, active Houzz/BuildZoom profile, commercial projects visible |
| 4 | 20–49 reviews, business active, no project history found |
| 3 | 10–19 reviews, residential focus, could do commercial |
| 2 | 5–9 reviews, minimal online presence |
| 1 | Under 5 reviews or business appears inactive |
