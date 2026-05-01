---
name: ez-floors-lead-gen
description: Full end-to-end automated B2B lead generation system for EZ Floors (Katy, TX). Use when setting up or running the EZ Floors lead generation machine — imports n8n workflows, configures the Claude Code enrichment agent, and manages outreach sequences targeting GCs, property managers, remodelers, real estate investors, and restoration companies in Houston/Katy. All reference files are in the reference/ directory.
---

# EZ Floors — B2B Lead Generation System

## Overview

This skill orchestrates a zero-capital, fully automated lead generation pipeline for EZ Floors that runs without human dialing. It covers four layers:

1. **Scraper** — nightly Google Maps + directory scraping → Google Sheets master lead tracker
2. **Enrichment** — Claude Code agent scores and enriches each raw lead
3. **Outreach** — n8n automated email + SMS sequences using the EZ Floors B2B cold script
4. **Referral Loop** — post-sale automated follow-up to generate referrals

## Target Buyer Profiles (B2B)

| Type | Pain Point | Hook |
|------|-----------|------|
| General Contractors | Quote turnaround, material availability | "Same-day quote turnaround, direct contact" |
| Property Managers | Tenant-ready turnarounds, callback liability | "Moisture barrier warranty protection" |
| Remodelers | Flooring spec flexibility, stock reliability | "I track your material availability personally" |
| Real Estate Investors | Fast flip timelines, cost per unit | "Volume pricing, no call center" |
| Restoration Companies | Emergency material sourcing | "Same-day availability check" |

## B2B Cold Opening (verbatim — do not alter)

> "Hey [Name], I'm Basel at EZ Floors in Katy. I work with a lot of GCs and remodelers out here — quick question before I take up any more of your time: **what does your current flooring supplier do that slows your jobs down or creates headaches?**"

Wait for the full response. Do not interrupt. Their answer IS the pitch.

## Calibrated Questions Bank

| Trigger Point | Question |
|--------------|----------|
| Discovery | "What does your current flooring supplier do that slows your jobs down?" |
| Value frame | "How important is it that every slab job you spec is covered from the subfloor up?" |
| Moisture barrier | "How important is it that if moisture is found post-install, you're not writing a check?" |
| Underlayment | "How important is it that every floor you install produces zero sound complaints?" |
| Baseboards | "Do you want this to look finished or like a replacement was done?" |
| Close | "If my quote comes in right, is there any reason we wouldn't do the first job together?" |

## Peripheral Commission Stack (15% flat)

| Item | Add-on Range | Commission Lift |
|------|-------------|----------------|
| Moisture Barrier | $120–$250 | $18–$38 |
| Premium Underlayment | $180–$380 | $27–$57 |
| Upgraded Baseboards | $200–$600 | $30–$90 |
| Full Stack (all 3) | $500–$1,230 | $75–$185 |

**Never say:** upgrade / add-on / extra  
**Always say:** "the rest of the system" / "what completes the floor" / "what keeps the warranty valid"

## Reference Files

All automation files are in `reference/`:

| File | Purpose |
|------|---------|
| `SETUP.md` | Credentials + n8n import steps |
| `scraper_workflow.json` | n8n: Google Maps → Google Sheets (nightly) |
| `enrichment_agent.py` | Claude Code: enrich + score raw leads |
| `outreach_sequences.json` | n8n: B2B email + SMS sequence (4 touchpoints) |
| `referral_loop.json` | n8n: Day 1/14/30 post-sale referral automation |

## Setup Sequence

1. Follow `reference/SETUP.md` — replace all credential placeholders
2. Import `scraper_workflow.json` into n8n — activate, verify first run appends rows to Google Sheet
3. Run `python reference/enrichment_agent.py` once manually against 5 test rows — verify scores write back
4. Import `outreach_sequences.json` — configure Gmail + Twilio — trigger with one "Enriched" test row
5. Import `referral_loop.json` — trigger with one "Job Complete" test row — verify Day 1 email sends

## Google Sheet Column Spec

`Company | Contact | Phone | Email | Address | City | Type | Source | Date Added | Status | Score | Notes`

**Status lifecycle:**
`Raw → Enriched → Contacted D0 → Contacted D3 → Contacted D7 → Replied | Sequence Complete → Meeting Booked → Job Complete → Referral Loop Complete`

## B2B Objection Responses (from EZ Floors Peripheral Attachment Script)

**"My clients are price-sensitive."**
> "The way we frame it: 'complete installation' vs. 'bare installation.' Bare is cheaper day one and costs more when something fails. Build two quote tiers — they pick with full information."

**"I already have a flooring supplier."**
> "I respect that. Just give me your next job. I'll quote it same-day, match or beat your number. If it doesn't work, you have a free benchmark. What's coming up next?"

**"How fast can you turn quotes?"**
> "Give me square footage and product spec — I have a number within the hour. Site measure: 24–48 hours. What's your current supplier's turnaround?"
