import unittest
from unittest.mock import Mock, patch
from searchapp.core.search.web import WebSearch

class TestWebSearch(unittest.TestCase):
    def setUp(self):
        self.web_search = WebSearch()

    @patch('searchapp.core.search.web.BingWebSearch')
    def test_searchAPI_success(self, mock_bing):
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "webPages": {
                "value": [
                    {"url": "http://example.com", "name": "Example", "snippet": "Test"}
                ]
            }
        }
        mock_bing.return_value.web_search_basic.return_value = mock_response

        self.web_search.searchAPI("test query")
        self.assertIsNotNone(self.web_search.pages)
        self.assertEqual(len(self.web_search.pages["webPages"]["value"]), 1)

    @patch('searchapp.core.search.web.BingWebSearch')
    def test_searchAPI_failure(self, mock_bing):
        # Mock failed API response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_bing.return_value.web_search_basic.return_value = mock_response

        self.web_search.searchAPI("test query")
        self.assertIsNone(self.web_search.pages)

    def test_find_pdf_links(self):
        # Test with a mock HTML response containing PDF links
        mock_html = """
        <html>
            <body>
                <a href="test1.pdf">PDF 1</a>
                <a href="test2.pdf">PDF 2</a>
                <a href="not-a-pdf.txt">Not a PDF</a>
            </body>
        </html>
        """
        with patch.object(WebSearch, 'downloadURL') as mock_download:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = mock_html
            mock_download.return_value = mock_response

            pdf_links = self.web_search.find_pdf_links("http://example.com")
            self.assertEqual(len(pdf_links), 2)
            self.assertTrue(all(link.endswith('.pdf') for link in pdf_links))

if __name__ == '__main__':
    unittest.main()