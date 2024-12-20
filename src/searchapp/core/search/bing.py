import json
import logging
import dotenv
import requests
from requests import HTTPError
from time import sleep

logger = logging.getLogger(__name__)

class BingWebSearch:

    def __init__(self) -> None:
        env = dotenv.dotenv_values()
        self.SUBSCRIPTION_KEY_ENV_VAR_NAME = "BING_SEARCH_V7_WEB_SEARCH_SUBSCRIPTION_KEY"
        self.subscription_key = env.get(self.SUBSCRIPTION_KEY_ENV_VAR_NAME)

    def web_search_basic(
        self, query, auth_header_name="Ocp-Apim-Subscription-Key", mkt="en-us", results_count=5
    ):
        """Bing Web Search Basic REST call

        This sample makes a call to the Bing Web Search API with a text query and returns relevant pages
        Documentation: https://docs.microsoft.com/en-us/bing/search-apis/bing-web-search/overview

        May throw HTTPError in case of invalid parameters or a server error.

        Args:
            subscription_key (str): Azure subscription key of Bing Web Search service
            auth_header_name (str): Name of the authorization header
            query (str): Query to search for
            mkt (str): Market to search in
        """
        # safety catch
        sleep(1)

        # Construct a request
        endpoint = "https://api.bing.microsoft.com/v7.0/search"
        params = {
            "q": query, 
            "mkt": mkt,
            "count": results_count,
            }
        headers = {auth_header_name: self.subscription_key}

        # Call the API
        try:
            response = requests.get(endpoint, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response
        except HTTPError as ex:
            logger.error(f"HTTPError: {ex}")
            print(ex)
            print("++The above exception was thrown and handled succesfully++")
            return response