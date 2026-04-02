TerraVaultIQ V7 Fresh
=====================

What this build does
- Real Google-based business discovery
- Optional public website enrichment
- Needs Leads scoring
- Hot/Warm/Cold opportunity tiers
- Auto pitch generation
- CSV / Excel / ZIP exports
- Google API key input directly in the app

How to run
1. Install Python 3.11+ if needed.
2. Open a terminal in this folder.
3. Run:
   pip install -r requirements.txt
4. Start the app:
   python -m streamlit run app_gui.py

Recommended first test
- Paste your Google API key into the app
- ZIP: 66048
- Radius: 10
- Search Mode: Marketing Prospect Finder
- Category: roofing
- Google ON
- OSM OFF

Google APIs required
- Geocoding API
- Places API

Safety
- Do not hardcode your API key in the files
- Paste it into the app at runtime
