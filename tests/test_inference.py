import unittest
from unittest.mock import Mock, patch
from searchapp.core.inference.inference import Inference

class TestInference(unittest.TestCase):
    def setUp(self):
        self.inference = Inference()
        self.inference.question = "test question"

    @patch('searchapp.core.inference.inference.requests.post')
    def test_formatQuestion(self, mock_post):
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "formatted question"}}]
        }
        mock_post.return_value = mock_response

        result = self.inference.formatQuestion("How do I make a cake?")
        self.assertEqual(result, "formatted question")

    @patch('searchapp.core.inference.inference.requests.post')
    def test_finalAnswer(self, mock_post):
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "final answer"}}]
        }
        mock_post.return_value = mock_response

        self.inference.pageRelevantResponses = ["response1", "response2"]
        result = self.inference.finalAnswer()
        self.assertEqual(result.json()["choices"][0]["message"]["content"], "final answer")

if __name__ == '__main__':
    unittest.main()