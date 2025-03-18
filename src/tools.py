from __future__ import annotations

import os
from typing import Dict, List

from apify import Actor
from apify_client import ApifyClient
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from openai import OpenAI
import re


# Initialize clients globally
APIFY_TOKEN = os.getenv('APIFY_TOKEN')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')

if not APIFY_TOKEN:
    raise ValueError('APIFY_TOKEN is missing!')

if not OPENAI_KEY:
    raise ValueError('OPENAI_API_KEY is missing!')

apify_client = ApifyClient(APIFY_TOKEN)
openai_client = OpenAI(api_key=OPENAI_KEY)


# ----------------------------- Tool 1: Google Search Tool -----------------------------

# src/tools.py

from apify import Actor
from apify_client import ApifyClient
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import os

# Google Search Scraper Tool (example)
class WebsiteScraperInput(BaseModel):
    url: str = Field(..., description="Official website URL of the company.")

class WebsiteScraperTool(BaseTool):
    name: str = 'Company Website Extractor'
    description: str = 'Extracts company focus, products, funding, executives, and contact info from official website.'
    args_schema: type[BaseModel] = WebsiteScraperInput

    def _run(self, url: str) -> dict:
        if not url:
            return {"error": "No URL provided"}

        run_input = {"startUrls": [{"url": url}], "maxPagesPerCrawl": 5}
        run = apify_client.actor("apify/website-content-crawler").call(run_input=run_input)
        pages = run.get('output', {}).get('pages', [])

        if not pages:
            return {"error": "No pages scraped."}

        all_text = " ".join([p.get('text', '') for p in pages])
        return {"website_data": all_text}

# ----------------------------- Tool 2: LinkedIn Scraper Tool -----------------------------

class LinkedInScraperInput(BaseModel):
    url: str = Field(..., description="LinkedIn company profile URL")

class LinkedInScraperTool(BaseTool):
    name: str = 'LinkedIn Company Profile Scraper'
    description: str = 'Scrapes company profile and employee data from LinkedIn.'
    args_schema: type[BaseModel] = LinkedInScraperInput

    def _run(self, url: str) -> dict:
        if not url:
            return {"error": "No LinkedIn URL provided"}

        run_input = {"url": url}
        run = apify_client.actor("pratikdani/linkedin-company-profile-scraper").call(run_input=run_input)
        items = run.get('output', [])
        if not items:
            return {"error": "No data from LinkedIn."}

        return items[0]

# ----------------------------- Tool 3: Crunchbase Scraper Tool -----------------------------

class CrunchbaseScraperInput(BaseModel):
    url: str = Field(..., description="Crunchbase organization profile URL")

class CrunchbaseScraperTool(BaseTool):
    name: str = 'Crunchbase Company Scraper'
    description: str = 'Scrapes funding history and company data from Crunchbase profile.'
    args_schema: type[BaseModel] = CrunchbaseScraperInput

    def _run(self, url: str) -> dict:
        if not url:
            return {"error": "No Crunchbase URL provided"}

        run_input = {"url": url}
        run = apify_client.actor("pratikdani/crunchbase-companies-scraper").call(run_input=run_input)
        items = run.get('output', [])
        if not items:
            return {"error": "No data from Crunchbase."}

        funding_rounds = items[0].get("funding_rounds_list", [])
        # Process funding history
        timeline = []
        for round_info in funding_rounds:
            try:
                timeline.append({
                    "date": round_info.get("announced_on"),
                    "amount_usd": round_info.get("money_raised", {}).get("value_usd", 0),
                    "investors": [i.get("names") for i in round_info.get("lead_investors", [])]
                })
            except Exception:
                continue

        return {
            "company_profile": items[0],
            "funding_timeline": sorted(timeline, key=lambda x: x['date'])
        }
