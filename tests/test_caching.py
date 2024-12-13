import unittest
from unittest.mock import Mock, patch
from searchapp.utils.caching import RedisHelper

class TestRedisHelper(unittest.TestCase):
    def setUp(self):
        self.redis_helper = RedisHelper()

    @patch('searchapp.utils.caching.redis.StrictRedis')
    def test_store_and_lookup(self, mock_redis):
        # Mock Redis client
        mock_client = Mock()
        mock_redis.return_value = mock_client

        # Test store
        self.redis_helper.store("test_key", "test_value")
        mock_client.set.assert_called_once_with("test_key", "test_value")

        # Test lookup
        mock_client.get.return_value = "test_value"
        result = self.redis_helper.lookup("test_key")
        self.assertEqual(result, "test_value")
        mock_client.get.assert_called_once_with("test_key")

    @patch('searchapp.utils.caching.redis.StrictRedis')
    def test_exists(self, mock_redis):
        # Mock Redis client
        mock_client = Mock()
        mock_redis.return_value = mock_client

        # Test exists
        mock_client.exists.return_value = True
        result = self.redis_helper.exists("test_key")
        self.assertTrue(result)
        mock_client.exists.assert_called_once_with("test_key")

if __name__ == '__main__':
    unittest.main()