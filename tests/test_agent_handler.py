import unittest
from unittest.mock import MagicMock
from borneoai.agent import run_agent_turn

class TestAgentTurn(unittest.TestCase):
    def test_run_agent_turn_parameters(self):
        # Create a mock client
        mock_client = MagicMock()
        
        # Setup mock response from generate_content
        mock_client.generate_content.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "Hello, I am BorneoAI!"}
                        ]
                    }
                }
            ]
        }
        
        # Test calling with all parameters including videos
        result = run_agent_turn(
            client=mock_client,
            prompt="Hello",
            images=["dummy_image.png"],
            videos=["dummy_video.mp4"],
            system_instruction="You are an agent",
            tools_map={},
            tools_declarations=[]
        )
        
        self.assertTrue(result)
        self.assertTrue(mock_client.encode_image.called)
        self.assertTrue(mock_client.encode_video.called)
        self.assertTrue(mock_client.append_message.called)
        self.assertTrue(mock_client.generate_content.called)

if __name__ == "__main__":
    unittest.main()
