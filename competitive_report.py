#!/usr/bin/env python
# coding: utf-8

# In[14]:


# Imports

import os
import requests
import json
import datetime
import time
import imgkit
import re
import tempfile
from html2image import Html2Image
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from IPython.display import display, HTML


# In[ ]:


pip install html2image


# In[ ]:


get_ipython().system('pip install requests beautifulsoup4 python-dotenv openai selenium webdriver-manager matplotlib wordcloud nltk pandas schedule')


# In[5]:


# Load environment variables
load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')

# Validate API key
if not api_key:
    print("No API key was found - please head over to the troubleshooting notebook in this folder to identify & fix!")
elif not api_key.startswith("sk-proj-"):
    print("An API key was found, but it doesn't start sk-proj-; please check you're using the right key - see troubleshooting notebook")
elif api_key.strip() != api_key:
    print("An API key was found, but it looks like it might have space or tab characters at the start or end - please remove them - see troubleshooting notebook")
else:
    print("API key found and looks good so far!")


# In[6]:


client = OpenAI(api_key=api_key)

# Second cell: Website scraper class
class EnhancedWebScraper:
    def __init__(self, url, use_selenium=False):
        """Initialize scraper with URL"""
        self.url = url
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
        }

        if use_selenium:
            self._scrape_with_selenium()
        else:
            self._scrape_with_requests()

    def _scrape_with_requests(self):
        """Use requests for static pages"""
        try:
            response = requests.get(self.url, headers=self.headers, timeout=10)
            response.raise_for_status()
            self.body = response.content
            soup = BeautifulSoup(response.content, 'html.parser')
            self._process_soup(soup)
        except Exception as e:
            print(f"Error scraping {self.url}: {e}")
            self.title = "Error"
            self.text = f"Failed to scrape: {str(e)}"
            self.links = []
            self.meta_description = "Not available"

    def _scrape_with_selenium(self):
        """Use Selenium for JavaScript-heavy pages"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'user-agent={self.headers["User-Agent"]}')

        try:
            # Initialize the driver
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

            # Navigate to the URL
            driver.get(self.url)

            # Wait for JavaScript to load
            time.sleep(5)

            # Get the page source after JavaScript has executed
            page_source = driver.page_source

            # Parse with BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            self._process_soup(soup)

            # Extract h1, h2, h3 headers
            self.headers_h1 = [h.text for h in driver.find_elements(By.TAG_NAME, 'h1')]
            self.headers_h2 = [h.text for h in driver.find_elements(By.TAG_NAME, 'h2')]
            self.headers_h3 = [h.text for h in driver.find_elements(By.TAG_NAME, 'h3')]

        except Exception as e:
            print(f"Selenium error for {self.url}: {e}")
            self.title = "Error"
            self.text = f"Failed to scrape with Selenium: {str(e)}"
            self.links = []
            self.meta_description = "Not available"
            self.headers_h1 = []
            self.headers_h2 = []
            self.headers_h3 = []
        finally:
            # Close the browser if it was created
            if 'driver' in locals():
                driver.quit()

    def _process_soup(self, soup):
        """Process the BeautifulSoup object"""
        self.title = soup.title.string if soup.title else "No title found"

        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        self.meta_description = meta_desc.get('content') if meta_desc else "No description found"

        # Remove irrelevant elements
        for irrelevant in soup.find_all(["script", "style", "img", "input", "noscript", "svg"]):
            irrelevant.decompose()

        # Extract main content
        self.text = soup.body.get_text(separator="\n", strip=True) if soup.body else ""

        # Extract links
        links = [link.get('href') for link in soup.find_all('a')]
        self.links = []

        # Process links to get absolute URLs
        for link in links:
            if link and link.strip():
                # Handle relative URLs
                if link.startswith('/'):
                    base_url = '/'.join(self.url.split('/')[:3])  # https://domain.com
                    self.links.append(f"{base_url}{link}")
                elif link.startswith('http'):
                    self.links.append(link)


# In[7]:


class CompetitiveAnalyzer:
    def __init__(self, api_key):
        """Initialize with API key"""
        self.client = OpenAI(api_key=api_key)

    def extract_company_info(self, website_text):
        """Extract comprehensive company information"""
        prompt = f"""
        Analyze the following website content and provide a comprehensive profile of the company.
        Return a detailed JSON object with these fields:
        - company_name: The complete name of the company
        - company_vision: The vision statement or long-term goals
        - industry: Primary and secondary industries the company operates in
        - target_audience: Comprehensive analysis of customer segments and target markets
        - key_products: Detailed list of main products or services with brief descriptions
        - company_profile: company's mission, history, products or services, goals and key information like loacation, leadership, and achievments
        - company_culture: Information about their workplace culture and values
        - market_position: Information about their position in the market
        - business_model: How the company generates revenue
        - unique_selling_points: What makes the company stand out from competitors
        - digital_presence: Quality and extent of online presence
        - customer_experience: UX/UI quality, checkout process, customer support

        Format the value proposition, company mission, and other descriptive fields as complete paragraphs rather than short phrases.

        Website content:
        {website_text[:1000]}
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Using more capable model for better analysis
                messages=[
                    {"role": "system", "content": "You are an expert business analyst who extracts comprehensive information about companies from their website content. Provide detailed, thorough analysis in a structured format."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2  # Lower temperature for more consistent, factual responses
            )

            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error extracting company info: {e}")
            return {
                "company_name": "Error extracting data",
                "error_message": str(e)
            }

    def compare_companies(self, company_data_list):
        """Compare multiple companies based on their extracted data"""

        # Create a prompt with all company data
        company_summaries = []
        for i, company in enumerate(company_data_list):
            company_name = company.get('company_name', f"Company {i+1}")
            summary = f"Company {i+1}: {company_name}\n"

            # Add key information
            for key in ['industry', 'target_audience', 'key_products', 'market_position', 'business_model', 'unique_selling_points']:
                if key in company and company[key]:
                    value = company[key]
                    if isinstance(value, list):
                        value = ", ".join([str(item) for item in value])
                    summary += f"{key}: {value}\n"

            company_summaries.append(summary)

        all_companies = "\n\n".join(company_summaries)

        comparison_prompt = f"""
        Below is information about {len(company_summaries)} e-commerce companies.

        {all_companies}

        Perform a comparative analysis of these companies. Focus on:

        1. Direct comparisons of their market positions
        2. Competitive advantages and disadvantages
        3. Target audience/market overlaps and differences
        4. Business model differences
        5. Product/service offering differences
        6. Pricing strategy comparisons
        7. Digital presence and customer experience differences

        Format your response as a JSON object with the following structure:
        {{
            "comparative_analysis": {{
                "market_position_comparison": "Text comparing all companies' market positions",
                "competitive_advantages": {{
                    "company_name_1": ["advantage 1", "advantage 2"],
                    "company_name_2": ["advantage 1", "advantage 2"]
                }},
                "competitive_disadvantages": {{
                    "company_name_1": ["disadvantage 1", "disadvantage 2"],
                    "company_name_2": ["disadvantage 1", "disadvantage 2"]
                }},
                "target_audience_differences": "Detailed comparison of target markets",
                "business_model_comparison": "Analysis of different revenue models",
                "product_offering_comparison": "How product catalogs compare",
                "pricing_strategy_comparison": "How pricing approaches differ",
                "digital_customer_experience": "UX/CX comparison",
                "key_differentiators": {{
                    "company_name_1": "Main factor that sets this company apart",
                    "company_name_2": "Main factor that sets this company apart"
                }}
            }}
        }}
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert business analyst specialized in comparative market analysis for e-commerce companies."},
                    {"role": "user", "content": comparison_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )

            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error creating comparison: {e}")
            return {
                "comparative_analysis": {
                    "error": f"Failed to generate comparison: {str(e)}"
                }
            }






# In[8]:


def run_competitive_analysis(websites, api_key, save_to_file=True):
    """
    Run comparative analysis on multiple e-commerce websites

    Args:
        websites: List of website URLs to analyze
        api_key: OpenAI API key
        save_to_file: Whether to save results to files
    """
    all_company_data = []
    company_names = []

    print("🔍 Starting comprehensive competitive analysis...\n")

    analyzer = CompetitiveAnalyzer(api_key)
    for i, url in enumerate(websites):
        print(f"📊 Analyzing company {i+1}/{len(websites)}: {url}")

        # Scrape the website
        scraper = EnhancedWebScraper(url)

        # Extract company information
        company_info = analyzer.extract_company_info(scraper.text)
        company_names.append(company_info.get('company_name', f"Company {i+1}"))
        all_company_data.append(company_info)

        print(f"✅ Completed analysis of: {company_info.get('company_name', 'Unknown Company')}")

    print("\n📊 Creating comparative analysis...")
    comparison = analyzer.compare_companies(all_company_data)

    # Create a summary table for display
    comparative_table = create_comparative_table(all_company_data)
    display(HTML(comparative_table))

    # Generate HTML comparison report
    comparison_html = generate_comparison_report(all_company_data, comparison)

    if save_to_file:
        # Save all data to files
        with open("company_analysis_full.json", "w", encoding="utf-8") as f:
            json.dump(all_company_data, f, indent=4, ensure_ascii=False)

        with open("competitive_comparison.json", "w", encoding="utf-8") as f:
            json.dump(comparison, f, indent=4, ensure_ascii=False)

        with open("competitive_analysis_report.html", "w", encoding="utf-8") as f:
            f.write(comparison_html)

         # Save summary table to separate HTML file for easy viewing
        with open("summary_table.html", "w", encoding="utf-8") as f:
            f.write(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Competitive Analysis Summary</title>
                <meta charset="utf-8">
            </head>
            <body>
                {comparative_table}
            </body>
            </html>
            """)

        # Generate image from the HTML table
        try:
            generate_html_table_image(all_company_data, "summary_table.png")
            print("   - summary_table.png (image of the summary table for social media)")
        except Exception as e:
            print(f"Note: Could not generate image of the table: {str(e)}")
            print("   To create an image of the table, please install the required packages:")
            print("   pip install imgkit wkhtmltopdf")

        print("\n📁 Files saved:")
        print("   - company_analysis_full.json (detailed company data)")
        print("   - competitive_comparison.json (comparison analysis)")
        print("   - competitive_analysis_report.html (visual comparison report)")

    return {
        "companies": all_company_data,
        "comparison": comparison
    }


# In[9]:


def html_to_image_simple(html_content, output_filename="summary_table.png"):
    """
    A simpler function to convert HTML to an image using just one method
    for easier debugging
    """
    # Create a temporary HTML file
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as temp_file:
        temp_file.write(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Table Image</title>
            <style>
                body {{
                    margin: 0;
                    padding: 20px;
                    background-color: white;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """)
        temp_html_path = temp_file.name

    try:
        # Try using imgkit first
        try:
            options = {
                'width': 1200,
                'quality': 100,
                'enable-local-file-access': None,
                'encoding': 'UTF-8',
            }
            imgkit.from_file(temp_html_path, output_filename, options=options)
            print(f"✅ Successfully created image using imgkit: {output_filename}")
            return True
        except ImportError:
            print("imgkit not found, trying alternative method...")

        # If imgkit fails, try using Selenium
        try:

            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--window-size=1200,2000")
            chrome_options.add_argument("--hide-scrollbars")

            driver = webdriver.Chrome(options=chrome_options)
            file_url = f"file:///{os.path.abspath(temp_html_path)}"
            driver.get(file_url)
            time.sleep(2)

            # Adjust the height to match content
            height = driver.execute_script("return document.body.scrollHeight")
            driver.set_window_size(1200, height)

            # Take a screenshot
            driver.save_screenshot(output_filename)
            driver.quit()
            print(f"✅ Successfully created image using Selenium: {output_filename}")
            return True
        except Exception as e:
            print(f"Selenium method failed: {str(e)}")

        # Last resort: html2image
        try:
            hti = Html2Image()
            hti.screenshot(html_file=temp_html_path, save_as=output_filename)
            print(f"✅ Successfully created image using html2image: {output_filename}")
            return True
        except Exception as e:
            print(f"html2image method failed: {str(e)}")

        raise Exception("All image conversion methods failed")

    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_html_path)
        except:
            pass


# In[10]:


def generate_html_table_image(companies_data, output_file="summary_table.png"):
    """
    Generate an image of a comparative table for the given companies data

    Args:
        companies_data: List of company data dictionaries
        output_file: Path where to save the image file
    """
    # Create the HTML table
    html_table = create_comparative_table(companies_data)

    # Convert to image
    try:
        html_to_image_simple(html_table, output_file)
        print(f"Table image saved to: {output_file}")
        return True
    except Exception as e:
        print(f"Error generating image: {str(e)}")
        print("\nPlease install the required dependencies:")
        print("Option 1 (recommended): pip install imgkit")
        print("  and install wkhtmltopdf from: https://wkhtmltopdf.org/downloads.html")
        print("Option 2: pip install selenium webdriver-manager")
        print("Option 3: pip install html2image")
        return False


# In[11]:


def create_comparative_table(companies_data):
    """Create an HTML table comparing key aspects of companies"""

    # Define the aspects to compare
    comparison_aspects = [
        "industry", 
        "target_audience", 
        "business_model", 
        "market_position",
        "unique_selling_points"
    ]

    # Start building the HTML table
    html = """
    <style>
        .comp-table {
            width: 100%;
            border-collapse: collapse;
            font-family: Arial, sans-serif;
            font-size: 14px;
            margin: 20px 0;
        }
        .comp-table th {
            background-color: #304878;
            color: white;
            text-align: left;
            padding: 12px 15px;
            font-weight: bold;
        }
        .comp-table td {
            padding: 10px 15px;
            border-bottom: 1px solid #ddd;
            max-width: 300px;
            vertical-align: top;
        }
        .comp-table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .aspect-name {
            font-weight: bold;
            color: #555;
        }
    </style>
    <table class="comp-table">
        <tr>
            <th>Comparison Aspect</th>
    """

    # Add company names as column headers
    for company in companies_data:
        company_name = company.get('company_name', 'Unknown Company')
        html += f"<th>{company_name}</th>"

    html += "</tr>"

    # Add rows for each comparison aspect
    for aspect in comparison_aspects:
        html += f"""
        <tr>
            <td class="aspect-name">{aspect.replace('_', ' ').title()}</td>
        """

        for company in companies_data:
            aspect_value = company.get(aspect, "Information not available")

            # Handle different data types
            if isinstance(aspect_value, list):
                if all(isinstance(item, dict) for item in aspect_value):
                    # List of dictionaries - extract key info
                    items = []
                    for item in aspect_value[:3]:  # Limit to first 3 for brevity
                        if 'name' in item:
                            items.append(item['name'])
                        elif 'title' in item:
                            items.append(item['title'])
                        else:
                            items.append(str(list(item.values())[0]) if item else "")
                    display_value = "<br>".join(items)
                    if len(aspect_value) > 3:
                        display_value += f"<br>...and {len(aspect_value)-3} more"
                else:
                    # Simple list - join with breaks
                    display_value = "<br>".join([str(item) for item in aspect_value[:3]])
                    if len(aspect_value) > 3:
                        display_value += f"<br>...and {len(aspect_value)-3} more"
            elif isinstance(aspect_value, str):
                # String - truncate if too long
                if len(aspect_value) > 200:
                    display_value = aspect_value[:197] + "..."
                else:
                    display_value = aspect_value
            else:
                display_value = str(aspect_value)

            html += f"<td>{display_value}</td>"

        html += "</tr>"

    html += "</table>"
    return html


# In[12]:


def generate_comparison_report(companies_data, comparison):
    """Generate detailed HTML comparison report"""

    company_names = [company.get('company_name', 'Unknown Company') for company in companies_data]

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>E-commerce Competitive Analysis Report</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            .header {
                background: #304878;
                color: white;
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 30px;
            }
            h1 {
                margin: 0;
                font-size: 28px;
            }
            h2 {
                color: #304878;
                border-bottom: 2px solid #304878;
                padding-bottom: 5px;
                margin-top: 30px;
            }
            h3 {
                color: #555;
                margin-top: 25px;
            }
            .company-card {
                background: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 15px;
                margin-bottom: 20px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .company-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }
            .company-name {
                font-size: 18px;
                font-weight: bold;
                color: #304878;
                margin: 0;
            }
            .industry-tag {
                background: #e8f0ff;
                color: #304878;
                padding: 3px 8px;
                border-radius: 12px;
                font-size: 12px;
            }
            .section {
                margin-bottom: 20px;
            }
            .section-title {
                font-weight: bold;
                margin-bottom: 5px;
                color: #555;
            }
            .advantage {
                color: #2e7d32;
            }
            .disadvantage {
                color: #c62828;
            }
            .comparison-table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            .comparison-table th {
                background-color: #304878;
                color: white;
                text-align: left;
                padding: 10px;
            }
            .comparison-table td {
                padding: 10px;
                border-bottom: 1px solid #ddd;
            }
            .comparison-table tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            .key-diff {
                font-weight: bold;
                color: #304878;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>E-commerce Competitive Analysis Report</h1>
            <p>Comparative analysis of """ + ", ".join(company_names) + """</p>
        </div>

        <h2>Executive Summary</h2>
    """

    # Add market position comparison
    comparative_analysis = comparison.get('comparative_analysis', {})
    html += f"""
        <div class="section">
            <div class="section-title">MARKET POSITIONING OVERVIEW</div>
            <p>{comparative_analysis.get('market_position_comparison', 'No comparison available')}</p>
        </div>
    """

    # Add company cards section
    html += """
        <h2>Company Profiles</h2>
        <div class="company-cards">
    """

    # Add a card for each company
    for company in companies_data:
        company_name = company.get('company_name', 'Unknown Company')
        industry = company.get('industry', 'Industry not specified')
        if isinstance(industry, list) and industry:
            industry = industry[0]

        html += f"""
        <div class="company-card">
            <div class="company-header">
                <h3 class="company-name">{company_name}</h3>
                <span class="industry-tag">{industry}</span>
            </div>

            <div class="section">
                <div class="section-title">COMPANY PROFILE</div>
                <p>{company.get('company_profile', 'No profile available')}</p>
            </div>

            <div class="section">
                <div class="section-title">TARGET AUDIENCE</div>
                <p>{company.get('target_audience', 'No target audience specified')}</p>
            </div>

            <div class="section">
                <div class="section-title">UNIQUE SELLING POINTS</div>
                <p>{company.get('unique_selling_points', 'No USPs specified')}</p>
            </div>
        </div>
        """

    # Add comparative advantages and disadvantages
    html += """
        </div>

        <h2>Competitive Strengths & Weaknesses</h2>
        <table class="comparison-table">
            <tr>
                <th>Company</th>
                <th>Competitive Advantages</th>
                <th>Competitive Disadvantages</th>
            </tr>
    """

    advantages = comparative_analysis.get('competitive_advantages', {})
    disadvantages = comparative_analysis.get('competitive_disadvantages', {})

    for company_name in company_names:
        company_advantages = advantages.get(company_name, [])
        company_disadvantages = disadvantages.get(company_name, [])

        if isinstance(company_advantages, str):
            company_advantages = [company_advantages]
        if isinstance(company_disadvantages, str):
            company_disadvantages = [company_disadvantages]

        html += f"""
        <tr>
            <td><strong>{company_name}</strong></td>
            <td class="advantage">{'<br>'.join([f'• {adv}' for adv in company_advantages]) if company_advantages else 'None identified'}</td>
            <td class="disadvantage">{'<br>'.join([f'• {dis}' for dis in company_disadvantages]) if company_disadvantages else 'None identified'}</td>
        </tr>
        """

    html += """
        </table>

        <h2>Detailed Comparative Analysis</h2>
    """

    # Add business model comparison
    html += f"""
        <h3>Business Model Comparison</h3>
        <p>{comparative_analysis.get('business_model_comparison', 'No comparison available')}</p>

        <h3>Product & Service Offerings</h3>
        <p>{comparative_analysis.get('product_offering_comparison', 'No comparison available')}</p>

        <h3>Target Audience Differences</h3>
        <p>{comparative_analysis.get('target_audience_differences', 'No comparison available')}</p>

        <h3>Pricing Strategy Comparison</h3>
        <p>{comparative_analysis.get('pricing_strategy_comparison', 'No comparison available')}</p>

        <h3>Digital & Customer Experience</h3>
        <p>{comparative_analysis.get('digital_customer_experience', 'No comparison available')}</p>
    """

    # Add key differentiators section
    key_differentiators = comparative_analysis.get('key_differentiators', {})
    html += """
        <h3>Key Differentiators</h3>
        <table class="comparison-table">
            <tr>
                <th>Company</th>
                <th>Primary Differentiator</th>
            </tr>
    """

    for company_name in company_names:
        differentiator = key_differentiators.get(company_name, 'None identified')
        html += f"""
        <tr>
            <td><strong>{company_name}</strong></td>
            <td class="key-diff">{differentiator}</td>
        </tr>
        """

    html += """
        </table>

        <div style="margin-top: 40px; color: #777; font-size: 12px; text-align: center; border-top: 1px solid #ddd; padding-top: 20px;">
            This analysis is based on publicly available information and may not reflect complete company data.
        </div>
    </body>
    </html>
    """

    return html


# In[13]:


if __name__ == "__main__":
    # Replace with your OpenAI API key

    # List of e-commerce websites to compare
    websites = [
        "https://www.amazon.com",
        "https://www.walmart.com",
        "https://www.shopify.com"
    ]

    # Run the analysis
    results = run_competitive_analysis(websites, api_key)


# In[ ]:


pip install wkhtmltopdf


# In[ ]:




