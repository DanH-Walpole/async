import json
import logging
import os
import asyncio
import aiohttp
import requests
from typing import List, Optional

logger = logging.getLogger(__name__)

class Inference:
    def __init__(self):
        self.base_url = "http://localhost:1234/v1/chat/completions"
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.pagesInMD = []
        self.pageRelevantResponses = []
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        self.tokensUsedInput = 0  # Track tokens within the class
        self.semaphore = asyncio.Semaphore(10)
        self.lock = asyncio.Lock()  # Lock for thread safety
        self.question: Optional[str] = None
        self.formattedQuestion: Optional[str] = None

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

    def finalAnswer(self, searchResults="No results were found in the search"):
        if len(self.pageRelevantResponses) == 0:
            logger.error("No relevant pages found.")

        logger.debug(f"Search results: {len(self.pageRelevantResponses)}")
        logger.debug(f"Search results: {self.pageRelevantResponses}")

        preparedPrompt = f"""
        You are helping a user search the internet and answer a question. Here are the results of their internet search. Only answer the questions based on the search results. Mention the website if the answer came from a website. Format the answer in markdown:

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
        You are helping a user search the internet and answer a question. Here's the question from the user. Based on the question, can you reformat the question into a good query for a search engine? For example, if the user's question is "I am having trouble with my computer overheating. What should I do?" you could reformat it as "How to prevent computer overheating". Respond only with the reformatted question. Do not use the site keyword in the query:

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