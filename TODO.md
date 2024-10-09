# To do

* Add in control for bing API
* Add question formatting step for LLM to make the search more concise and performant
* Add a step for the LLM to review the URLs and Snips of the initial search
    - This should be a loop:
        - Search happens
        - Results are reviewed and evaluted based on the original question
        - Select results if they look high value
        - If no results look high value the loop restarts