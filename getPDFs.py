from bingsearch import BingWebSearch
import json
import requests
from requests import Response
from bs4 import BeautifulSoup
import PyPDF2
import pdfminer
import pdfplumber
import pymupdf
from urllib.parse import urljoin
import re
from io import BytesIO
from time import time
from pydantic import BaseModel, Field
import logging
import html2text
import dotenv
import os
import asyncio
import aiohttp

## get PDFs from a page.

# use the bing search to get a list of pages matching a search
# use bs4 to look through the page and find any links that would include a PDF
# download the PDFs and open in memory
# convert the pdf to text
# return the contents of the pdf

# Some cases to cover:
# What is the page is a graphical page and has pictures
# What is the pageis almost all text based

# We need to do OAI request for each web page and ask "How does this page relate tot he question?" then we can combine the context of each page to make one big answer.


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


class Inference:

    def __init__(self):
        self.base_url = "http://localhost:1234/v1/chat/completions"
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.question = ""
        self.pagesInMD = []
        self.pageRelevantResponses = []
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def populatePageResponses(self):
        for page in self.pagesInMD:
            response = self.relevantPageResponse(page)
            if response.status_code == 200:
                self.pageRelevantResponses.append(
                    response.json()["choices"][0]["message"]["content"]
                )
            else:
                logger.error(
                    f"Error: Unable to access {page['url']} (status code: {response.status_code})"
                )
                pass

    def finalAnswer(self, searchResults="No results were found in the search"):

        preparedPrompt = f"""

        You are helping a user search the internet and answer a question. Here are the results of their internet search. Only answer the questions based on the search results:

        Search results:

        {self.pageRelevantResponses}

        Based on the search results, what is the answer to the user's question?
        Here's their question: {self.question}
        """

        response = requests.post(
            headers=self.headers,
            url=self.base_url,
            json={
                "messages": [
                    {
                        "role": "system",
                        "content": "You helping to answer a query from a user. You are specifically good with searching the internet for results.",
                        "role": "user",
                        "content": preparedPrompt,
                    }
                ],
                "model": "gpt-4o-mini",
                "temperature": 0.2,
            },
        )
        return response

    def relevantPageResponse(self, pageInMD="No details were available for the page"):

        preparedPrompt = f"""

        You are helping a user search the internet and answer a question. Here's the raw page formatted in markdown. Based on this data, generate a summary of why this question relates to the user's question. If it answers the user's question, provide the answer:

        question: {self.question}

        page content:
        {pageInMD}
        """

        response = requests.post(
            headers=self.headers,
            url=self.base_url,
            json={
                "messages": [
                    {
                        "role": "system",
                        "content": "You helping to answer a query from a user. You are specifically good with searching the internet for results.",
                        "role": "user",
                        "content": preparedPrompt,
                    }
                ],
                "model": "gpt-4o-mini",
                "temperature": 0.2,
            },
        )
        return response


class WebSearch:

    pages: dict

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
        response = mySearch.web_search_basic(query)
        self.pages = response.json()
        self.populatePagesContents()
        pass

    def populatePagesContents(self):
        for page in self.pages["webPages"]["value"]:
            response = self.downloadURL(page["url"])
            if response.status_code == 200:
                self.pagesContentsHTML.append(response)
                self.pagesContentsMD.append(self.convert_html_to_markdown(response))
            else:
                logger.error(
                    f"Error: Unable to access {page['url']} (status code: {response.status_code})"
                )
                pass

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
        response = requests.get(url=url, headers=headers)
        return response

    def find_pdf_links(self, url):
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

    def download_pdf(self, pdf_url):
        # Send a request to the PDF URL
        response = requests.get(pdf_url)

        # Check if the request was successful
        if response.status_code == 200:
            # return the pdf file
            return response.content
        else:
            print(
                f"Error: Unable to download PDF from {pdf_url} (status code: {response.status_code})"
            )

    def convert_html_to_markdown(self, response: Response) -> str:

        html_content = response.text

        # Create an html2text object
        h = html2text.HTML2Text()

        # Ignore converting links (optional)
        h.ignore_links = True

        # Convert the HTML content to Markdown
        markdown_content = h.handle(html_content)

        return markdown_content

    def convert_pdf_to_text(self, pdf_content):
        if self.pdfProvider == "PyPDF2":
            return self.convert_with_pypdf2(pdf_content)
        elif self.pdfProvider == "pdfminer":
            return self.convert_with_pdfminer(pdf_content)
        elif self.pdfProvider == "pdfplumber":
            return self.convert_with_pdfplumber(pdf_content)
        elif self.pdfProvider == "PyMuPDF":
            return self.convert_with_pymupdf(pdf_content)
        else:
            raise ValueError(f"Unknown PDF provider: {self.provider}")

    # Provider implementations
    def convert_with_pypdf2(self, pdf_content):
        pdf_file = BytesIO(pdf_content)
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text

    def convert_with_pdfminer(self, pdf_content):
        from pdfminer.high_level import extract_text

        pdf_file = BytesIO(pdf_content)
        text = extract_text(pdf_file)
        return text

    def convert_with_pdfplumber(self, pdf_content):
        pdf_file = BytesIO(pdf_content)
        text = ""
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text += page.extract_text()
        return text

    def convert_with_pymupdf(self, pdf_content):
        pdf_file = BytesIO(pdf_content)
        doc = pymupdf.open(pdf_file)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text


if __name__ == "__main__":

    webSearch = WebSearch()
    myInference = Inference()
    question = "How do I find Yuffie in Final Fantasy 7 Original?"

    myInference.base_url = "https://api.openai.com/v1/chat/completions"

    webSearch.searchAPI(question)

    myInference.question = question
    myInference.pagesInMD = webSearch.pagesContentsMD

    myInference.populatePageResponses()

    final_answer = myInference.finalAnswer()

    print(final_answer.json()["choices"][0]["message"]["content"])

    # Stopping here for now to get the inference piece put together then turning back around to get the extra PDF info.

    exit()

    pages = webSearch.pages

    # This will be handed to the LLM to decide if it should search or not based on the title.
    pageDetails = webSearch.getPdfChoices(pages)

    # get all the urls from the pages object
    pageURLs = [page["url"] for page in pages["webPages"]["value"]]

    # simulate LLM triggering a search on url
    # this needs to change to selecting by the ID
    # ideally we would then grab all the pdfs and then lopp through those to get the text from each.
    pdfLinks = webSearch.find_pdf_links(pageURLs[0])

    # start a timer to profile the performance of the pdf to text conversion
    start_time = time()

    # set the pdf provider to use
    webSearch.pdfProvider = "pdfminer"

    pdfContents = []

    # convert the pdf to text
    for pdfLink in pdfLinks:
        pdfText = webSearch.download_pdf(pdfLink)
        pdfContents.append(webSearch.convert_pdf_to_text(pdfText))

        # print the first 100 characters of the text
    print(pdfContents)

    print(
        f"Total time taken: {time() - start_time:.2f} seconds using {webSearch.pdfProvider} for {len(pdfLinks)} PDFs"
    )
