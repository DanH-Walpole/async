import json
import logging
import requests
from bs4 import BeautifulSoup
import html2text
from urllib.parse import urljoin
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import time
from typing import List, Optional, Set
from .bing import BingWebSearch

logger = logging.getLogger(__name__)

class WebSearch:
    def __init__(self):
        self.query = ""
        self.provider = "bing"
        self.pdfProvider = "PyPDF2"
        self.pages = None
        self.pagesContentsHTML = []
        self.pagesContentsMD = []
        self.response = None

    def searchAPI(self, query):
        mySearch = BingWebSearch()

        response = mySearch.web_search_basic(query, results_count=5)
        if response.status_code != 200:
            logger.error(
                f"Error: Unable to access Bing Search API (status code: {response.status_code})"
            )
            return
        try:
            self.pages = response.json()
            logger.debug(f"Bing API Response: {json.dumps(self.pages, indent=2)}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            self.pages = {}

        start_time = time()
        if self.pages:
            self.populatePagesContentsMulti()
            logger.debug(
                f"Populated pages contents in {time() - start_time:.2f} seconds"
            )
        else:
            logger.error("No search results found.")

    def populatePagesContentsMulti(self):
        if not self.pages:
            logger.error("No search results found.")
            return

        if "webPages" not in self.pages:
            logger.error(f"'webPages' key not found in the API response: {self.pages}")
            return

        if "value" not in self.pages["webPages"]:
            logger.error(
                f"'value' key not found under 'webPages': {self.pages['webPages']}"
            )
            return

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []

            for page in self.pages["webPages"]["value"]:
                # Download the page HTML and convert to markdown concurrently
                future = executor.submit(self.processPageMulti, page)
                futures.append(future)

            # Wait for all futures to complete
            for future in as_completed(futures):
                try:
                    page_markdown = future.result()
                    self.pagesContentsMD.append(page_markdown)
                except Exception as e:
                    logger.error(f"Error processing page: {e}")

    def processPageMulti(self, page):
        response = self.downloadURL(page["url"])
        if response and response.status_code == 200:
            self.pagesContentsHTML.append(response)
            return self.convert_html_to_markdown(pageHTML=response, pageURL=page["url"])
        else:
            logger.error(f"Error: Unable to access {page['url']}")
            return None

    def populatePagesContents(self):
        for page in self.pages["webPages"]["value"]:
            response = self.downloadURL(page["url"])
            if response and response.status_code == 200:
                self.pagesContentsHTML.append(response)
                self.pagesContentsMD.append(
                    self.convert_html_to_markdown(
                        pageHTML=response, pageURL=page["url"]
                    )
                )
            if response:
                logger.error(
                    f"Error: Unable to access {page['url']} status code: {response.status_code}"
                )
            else:
                logger.error(f"Error: Unable to access {page['url']}")

    def getPdfChoices(self, responseObject) -> str:
        returnString = ""

        for pageDetails in responseObject["webPages"]["value"]:
            pageTitle = pageDetails["name"]
            pageID = pageDetails["id"]
            pageURL = pageDetails["url"]
            pageSnippet = pageDetails["snippet"]
            returnString += f"{pageID}\n{pageTitle}\n{pageURL}\n{pageSnippet}\n\n"

        return returnString

    def downloadURL(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        try:
            response = requests.get(url=url, headers=headers, timeout=5)
        except requests.Timeout:
            logger.error(f"Timeout error while accessing {url}")
            return None
        except requests.RequestException as e:
            logger.error(f"Error while accessing {url}: {e}")
            return None

        return response

    def find_pdf_links(self, url) -> Set[str]:
        # Send a request to the URL
        response = self.downloadURL(url)

        pdf_links = set()  # Use a set instead of a dictionary

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the HTML content with BeautifulSoup
            soup = BeautifulSoup(response.text, "html.parser")

            # Find all 'a' tags (links) in the webpage
            links = soup.find_all("a", href=True)

            # Filter and add links that point to PDFs to the set
            for link in links:
                href = link["href"].strip()  # Clean up any extra whitespace
                if href.lower().endswith(".pdf"):
                    # Handle relative URLs and get absolute ones
                    pdf_url = urljoin(url, href)

                    # Clean up link text by collapsing multiple spaces
                    link_text = re.sub(r"\s+", " ", link.text.strip()) or "Unnamed link"

                    # Add the cleaned PDF URL to the set
                    pdf_links.add(pdf_url)

            # Output the found PDF links
            if pdf_links:
                logger.info(f"Found {len(pdf_links)} unique PDF link(s):")
                for pdf_url in pdf_links:
                    logger.debug(f" - {pdf_url}")
            else:
                logger.warning("No PDF links found.")
        else:
            logger.error(
                f"Error: Unable to access {url} (status code: {response.status_code})"
            )

        return pdf_links

    def convert_html_to_markdown(self, pageHTML: requests.Response, pageURL: str) -> str:
        start_time = time()

        html_content = pageHTML.text

        # Create an html2text object
        h = html2text.HTML2Text()

        # Ignore converting links (optional)
        h.ignore_links = True
        h.ignore_images = True
        h.ignore_mailto_links = True
        h.skip_internal_links = True

        # Convert the HTML content to Markdown
        markdown_content = f"source: {pageURL} \n{h.handle(html_content)}"

        logger.debug(f"Converted HTML to Markdown in {time() - start_time:.2f} seconds")

        return markdown_content