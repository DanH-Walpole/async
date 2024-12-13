import asyncio
import logging
from time import time
from typing import Optional

from searchapp.core.inference.inference import Inference
from searchapp.core.search.web import WebSearch
from searchapp.utils.caching import RedisHelper

logger = logging.getLogger(__name__)

class InputController:
    def __init__(self):
        self.redis = RedisHelper()
        self.question: Optional[str] = None

    def memoization(self) -> Optional[str]:
        """
        Use Redis to cache cold questions.
        """
        try:
            # Try to look up the question in Redis
            returnObject = self.redis.lookup(key=self.question)
            if returnObject:
                return returnObject  # Return the cached result from Redis
            else:
                return None

        except Exception as e:
            logger.error(f"Error with memoization: {e}")
            return None  # Ensure None is returned in case of an exception

    def run(self, question: str = None):
        try:
            self.question = question
        except Exception as e:
            logger.error(f"Error with initializing question: {e}")
            return

        if self.question:
            # Check the Redis cache before running the inference
            cached_result = self.memoization()
            if cached_result:
                logger.info(f"Returning cached result for '{question}' from Redis")
                return cached_result  # Return cached result from Redis
            else:
                # If no cache, run the main method and store the result in Redis
                result = asyncio.run(self.main(question))
                self.redis.store(key=self.question, value=result)
                return result

    async def main(self, question: str = None) -> str:
        start_time = time()

        webSearch = WebSearch()
        myInference = Inference()
        myInference.base_url = "https://api.openai.com/v1/chat/completions"

        if question:
            myInference.setQuestion(question)

        # Perform the web search and inference
        webSearch.searchAPI(myInference.formattedQuestion)
        myInference.question = question
        myInference.pagesInMD = webSearch.pagesContentsMD

        start_time_inference = time()
        await myInference.populatePageResponsesAsync()

        final_answer = myInference.finalAnswer()
        end_time_inference = time()

        total_time = time() - start_time

        logger.info(f"""
            Total time taken: {total_time:.2f} seconds
            Time taken for inference: {end_time_inference - start_time_inference:.2f} seconds

            Final Answer: {final_answer.json()["choices"][0]["message"]["content"]}
            """)

        # Return the final answer from the API response
        return final_answer.json()["choices"][0]["message"]["content"]