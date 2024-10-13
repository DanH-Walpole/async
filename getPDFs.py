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
from concurrent.futures import ThreadPoolExecutor, as_completed

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

    question: str
    formattedQuestion: str
    base_url: str = "http://localhost:1234/v1/chat/completions"

    def __init__(self):
        # self.base_url = "http://localhost:1234/v1/chat/completions"
        self.api_key = os.getenv("OPENAI_API_KEY")
        # self.question = ""
        self.pagesInMD = []
        self.pageRelevantResponses = []
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        self.tokensUsedInput = 0  # Track tokens within the class
        self.semaphore = asyncio.Semaphore(10)
        self.lock = asyncio.Lock()  # Lock for thread safety

    def setQuestion(self, question: str) -> None:
        self.question = question
        self.formattedQuestion = self.formatQuestion(self.question)
        logger.debug(f"Formatted question: {self.formattedQuestion}")

    def populatePageResponses(self) -> None:
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

        if len(self.pageRelevantResponses) == 0:
            logger.error("No relevant pages found.")

        logger.debug(f"Search results: {len(self.pageRelevantResponses)}")
        logger.debug(f"Search results: {self.pageRelevantResponses}")

        preparedPrompt = f"""

        You are helping a user search the internet and answer a question. Here are the results of their internet search. Only answer the questions based on the search results. Mention the website if the answer came from a website.:

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

        You are helping a user search the internet and answer a question. Here's the raw page formatted in markdown. Based on this data, generate a summary of why this question relates to the user's question. If it answers the user's question, provide the answer and also mention the website it came from:

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

    def formatQuestion(self, question=""):

        preparedPrompt = f"""

        You are helping a user search the internet and answer a question. Here's the question from the user. Based on the question, can you reformat the question into a good query for a search engine? For example, if the user's question is "I am having trouble with my computer overheating. What should I do?" you could reformat it as "How to prevent computer overheating". Respond only with the reformatted question:

        user's question: {question}

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

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        return response

    async def populatePageResponsesAsync(self):
        # List of async tasks for each page in Markdown format
        tasks = [self.relevantPageResponseAsync(page) for page in self.pagesInMD]

        # Run all tasks asynchronously and gather results
        results = await asyncio.gather(*tasks)

        for result in results:
            if result and result.status == 200:
                try:
                    # Read the response content as text
                    raw_content = await result.text()
                    logger.debug(f"Raw response content: {raw_content}")

                    # Attempt to parse it as JSON
                    json_resp = await result.json()
                    self.pageRelevantResponses.append(
                        json_resp["choices"][0]["message"]["content"]
                    )
                except aiohttp.ClientConnectionError:
                    logger.error("Error parsing JSON: Connection closed")
                except Exception as e:
                    logger.error(f"Error parsing JSON: {e}")
            else:
                logger.error(
                    f"Error: Unable to process one of the pages (status code: {result.status if result else 'None'})"
                )

    async def relevantPageResponseAsync(
        self, pageInMD="No details were available for the page"
    ):
        preparedPrompt = f"""
        You are helping a user search the internet and answer a question. Here's the raw page formatted in markdown. Based on this data, generate a summary of why this question relates to the user's question. If it answers the user's question, provide the answer:

        question: {self.question}

        page content:
        {pageInMD}
        """

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.base_url,
                    headers=self.headers,
                    json={
                        "messages": [
                            {
                                "role": "system",
                                "content": "You helping to answer a query from a user. You are specifically good with searching the internet for results.",
                                "role": "user",
                                "content": preparedPrompt,
                            }
                        ],
                        "model": "gpt-4o-mini",  # need to fix this to a parameter
                        "temperature": 0.2,
                    },
                    timeout=aiohttp.ClientTimeout(total=60),  # 30 seconds timeout
                ) as response:
                    logger.info(f"Response status: {response.status}")
                    logger.debug(f"Response content: {await response.text()}")

                    return response
            except aiohttp.ClientConnectionError as e:
                logger.error(f"Connection error while processing page: {e}")
                return None
            except asyncio.TimeoutError:
                logger.error(f"Request timed out for the page.")
                return None


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
        if response.status_code != 200:
            logger.error(
                f"Error: Unable to access Bing Search API (status code: {response.status_code})"
            )
            return
        self.pages = response.json()
        start_time = time()
        if self.pages:
            self.populatePagesContentsMulti()
            logger.debug(
                f"Populated pages contents in {time() - start_time:.2f} seconds"
            )
        else:
            logger.error("No search results found.")
        pass

    def populatePagesContentsMulti(self):

        if not self.pages["webPages"]["value"]:
            logger.error("No search results found.")
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
        try:
            response = requests.get(url=url, headers=headers, timeout=5)
        except requests.Timeout:
            logger.error(f"Timeout error while accessing {url}")
            return None
        except requests.RequestException as e:
            logger.error(f"Error while accessing {url}: {e}")
            return None

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

    def convert_html_to_markdown(self, pageHTML: Response, pageURL: str) -> str:

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


class DocumentHandler:

    def __init__(self):
        pass

    def convertPDFToText(self, inputPDF):
        for page in inputPDF:
            text = page.get_text()


class InputController:

    def run(self):
        asyncio.run(self.main())

    async def main(self):
        while True:
            start_time = time()

            webSearch = WebSearch()
            myInference = Inference()
            myInference.base_url = "https://api.openai.com/v1/chat/completions"
            # myInference.base_url = "http://192.168.1.181:1234/v1/chat/completions"
            # question = "What are the opinions between amazon s3 and backblaze b2 on reddit?"
            question = input("Enter a question: ")

            if question:
                myInference.setQuestion(question)

            webSearch.searchAPI(myInference.formattedQuestion)

            myInference.question = question
            myInference.pagesInMD = webSearch.pagesContentsMD

            start_time_inference = time()
            await myInference.populatePageResponsesAsync()

            final_answer = myInference.finalAnswer()
            end_time_inference = time()

            end_time = time()
            total_time = end_time - start_time

            # Print the final answer and the time taken
            print(
                f"""
                Total time taken: {total_time:.2f} seconds\n
                Time taken for inference: {end_time_inference - start_time_inference:.2f} seconds\n\n
                Final Answer: {final_answer.json()["choices"][0]["message"]["content"]}
                """
            )


if __name__ == "__main__":

    InputController().run()

    exit()

    async def main():

        while True:
            start_time = time()

            webSearch = WebSearch()
            myInference = Inference()
            myInference.base_url = "https://api.openai.com/v1/chat/completions"
            # myInference.base_url = "http://192.168.1.181:1234/v1/chat/completions"
            # question = "What are the opinions between amazon s3 and backblaze b2 on reddit?"
            question = input("Enter a question: ")

            if question:
                myInference.setQuestion(question)

            webSearch.searchAPI(myInference.formattedQuestion)

            myInference.question = question
            myInference.pagesInMD = webSearch.pagesContentsMD

            start_time_inference = time()
            await myInference.populatePageResponsesAsync()

            final_answer = myInference.finalAnswer()
            end_time_inference = time()

            end_time = time()
            total_time = end_time - start_time

            # Print the final answer and the time taken
            print(
                f"""
                Total time taken: {total_time:.2f} seconds\n
                Time taken for inference: {end_time_inference - start_time_inference:.2f} seconds\n\n
                Final Answer: {final_answer.json()["choices"][0]["message"]["content"]}
                """
            )

    asyncio.run(main())

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
