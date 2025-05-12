Competitive Website Analyzer with GPT-4o

This project is an **AI-powered web scraper and business intelligence tool** that performs **deep competitive analysis** of any websites. It extracts detailed company profiles from website content using `requests`, `Selenium`, `BeautifulSoup`, and OpenAI's `GPT-4o`, then produces structured JSON and HTML comparison reports.

Features

Smart Web Scraping: 
  - Static scraping with `requests`

  - JavaScript-rendered scraping with `Selenium` for dynamic sites

LLM-powered Analysis:

  - GPT-4o extracts structured company data (vision, products, audience, model, etc.)

Side-by-Side Comparison:

  - Market position
    
  - Business models
    
  - Product/service offerings
    
  - Pricing, UX, and customer experience
    
Outputs:

  - Full JSON data of individual companies
    
  - Comparative analysis in JSON
    
  - Rich HTML report
    
  - Summary table image

Setup

```bash

git clone https://github.com/yourusername/competitive-analyzer

cd competitive-analyzer

pip install -r requirements.txt


Requirements

openai


beautifulsoup4


requests


selenium


webdriver-manager


html2image or imgkit + wkhtmltopdf for image generation


🔑 Usage

Replace api_key in the script or pass it securely.

websites to compare and analyze = [

    "https://www.amazon.com",

    "https://www.walmart.com",

    "https://www.shopify.com"

]

results = run_competitive_analysis(websites, api_key="your_openai_api_key")


<img width="600" alt="summary_table" src="https://github.com/user-attachments/assets/ab114bd0-d2d1-4403-9265-4b4652b6e37e" />

📂 Output Files

company_analysis_full.json – full structured profiles


competitive_comparison.json – GPT-4o analysis results


competitive_analysis_report.html – rich HTML report


summary_table.html – quick-glance table


summary_table.png – image of summary table

Powered By

OpenAI GPT-4o


BeautifulSoup


Selenium


imgkit

Got any question? Contact me: chyootch@gmail.com
