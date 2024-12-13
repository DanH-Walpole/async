from flask import Flask, render_template, request, jsonify
import asyncio
from searchapp.core.inference.inference import Inference
from searchapp.core.search.web import WebSearch

app = Flask(__name__)

# Home route to render the input form
@app.route('/')
def home():
    return render_template('index.html')

# Route to handle the question
@app.route('/ask', methods=['POST'])
def ask():
    question = request.form['question']
    
    # Asynchronously process the question using your existing classes
    final_answer = asyncio.run(handle_question(question))

    return jsonify({'answer': final_answer})

# Define the async function that runs the logic in your script
async def handle_question(question):
    web_search = WebSearch()
    inference = Inference()
    inference.base_url = "https://api.openai.com/v1/chat/completions"
    inference.setQuestion(question)

    # Conduct web search based on the question
    web_search.searchAPI(inference.formattedQuestion)

    # Set pages from the search results
    inference.pagesInMD = web_search.pagesContentsMD

    # Process the page responses asynchronously
    await inference.populatePageResponsesAsync()

    # Get the final answer after combining responses
    final_answer = inference.finalAnswer()
    
    return final_answer.json()["choices"][0]["message"]["content"]

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=4545)