"""
Unit tests for ai_tools.py

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Copyright (C) 2024 AI Coder Assistant Contributors
"""

import unittest
import tempfile
import os
import sys
import json
from unittest.mock import Mock, patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.backend.services.ai_tools import (
    generate_report_and_training_data,
    batch_process_suggestions,
    _process_suggestion_batch,
    get_ai_explanation,
    _generate_ollama_explanation,
    _generate_own_model_explanation,
    _generate_fallback_explanation,
    browse_web_tool,
    transcribe_youtube_tool,
    AITools
)


class TestAITools(unittest.TestCase):
    """Test AITools class functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ai_tools = AITools()
    
    def test_ai_tools_initialization(self):
        """Test AITools initialization."""
        self.assertIsNotNone(self.ai_tools)
    
    def test_generate_report_and_training_data_empty(self):
        """Test report generation with empty suggestions."""
        mock_model = Mock()
        mock_tokenizer = Mock()
        
        report, training_data = generate_report_and_training_data(
            [], "ollama", mock_model, mock_tokenizer
        )
        
        self.assertIsInstance(report, str)
        self.assertIsInstance(training_data, str)
        self.assertIn("No issues found", report)
    
    def test_generate_report_and_training_data_with_suggestions(self):
        """Test report generation with suggestions."""
        suggestions = [
            {
                'file_path': '/test/file1.py',
                'line_number': 10,
                'description': 'Test issue 1',
                'code_snippet': 'x = 1',
                'suggested_improvement': 'x = 1  # Add comment',
                'language': 'python',
                'issue_type': 'performance_issue',
                'severity': 'medium'
            },
            {
                'file_path': '/test/file2.py',
                'line_number': 20,
                'description': 'Test issue 2',
                'code_snippet': 'y = 2',
                'suggested_improvement': 'y = 2  # Add comment',
                'language': 'python',
                'issue_type': 'security_vulnerability',
                'severity': 'high'
            }
        ]
        
        mock_model = Mock()
        mock_tokenizer = Mock()
        
        # Mock the batch processing to avoid actual AI calls
        with patch('core.ai_tools.batch_process_suggestions') as mock_batch:
            mock_batch.return_value = ['AI explanation 1', 'AI explanation 2']
            
            report, training_data = generate_report_and_training_data(
                suggestions, "ollama", mock_model, mock_tokenizer
            )
        
        self.assertIsInstance(report, str)
        self.assertIsInstance(training_data, str)
        self.assertIn("Test issue 1", report)
        self.assertIn("Test issue 2", report)
    
    def test_batch_process_suggestions(self):
        """Test batch processing of suggestions."""
        suggestions = [
            {'description': 'Issue 1'},
            {'description': 'Issue 2'},
            {'description': 'Issue 3'}
        ]
        
        mock_model = Mock()
        mock_tokenizer = Mock()
        
        # Mock the individual processing
        with patch('core.ai_tools._process_suggestion_batch') as mock_process:
            mock_process.return_value = ['Explanation 1', 'Explanation 2', 'Explanation 3']
            
            explanations = batch_process_suggestions(
                suggestions, "ollama", mock_model, mock_tokenizer
            )
        
        self.assertIsInstance(explanations, list)
        self.assertEqual(len(explanations), 3)
    
    def test_process_suggestion_batch(self):
        """Test processing a batch of suggestions."""
        suggestions = [
            {'description': 'Issue 1'},
            {'description': 'Issue 2'}
        ]
        
        mock_model = Mock()
        mock_tokenizer = Mock()
        
        # Mock the AI explanation
        with patch('core.ai_tools.get_ai_explanation') as mock_explanation:
            mock_explanation.return_value = 'AI explanation'
            
            explanations = _process_suggestion_batch(
                suggestions, "ollama", mock_model, mock_tokenizer
            )
        
        self.assertIsInstance(explanations, list)
        self.assertEqual(len(explanations), 2)
    
    def test_get_ai_explanation_ollama(self):
        """Test AI explanation with Ollama."""
        suggestion = {
            'description': 'Test issue',
            'code_snippet': 'x = 1',
            'suggested_improvement': 'x = 1  # Add comment'
        }
        
        mock_model = Mock()
        mock_tokenizer = Mock()
        
        # Mock Ollama response
        with patch('core.ai_tools.ollama_client.get_ollama_response') as mock_ollama:
            mock_ollama.return_value = 'This is an AI explanation'
            
            explanation = get_ai_explanation(
                suggestion, "ollama", mock_model, mock_tokenizer
            )
        
        self.assertIsInstance(explanation, str)
        self.assertIn('AI explanation', explanation)
    
    def test_get_ai_explanation_own_model(self):
        """Test AI explanation with own model."""
        suggestion = {
            'description': 'Test issue',
            'code_snippet': 'x = 1',
            'suggested_improvement': 'x = 1  # Add comment'
        }
        
        mock_model = Mock()
        mock_tokenizer = Mock()
        
        explanation = get_ai_explanation(
            suggestion, "own_model", mock_model, mock_tokenizer
        )
        
        self.assertIsInstance(explanation, str)
        self.assertIn('not yet implemented', explanation)
    
    def test_get_ai_explanation_fallback(self):
        """Test AI explanation fallback."""
        suggestion = {
            'description': 'Test issue',
            'code_snippet': 'x = 1',
            'suggested_improvement': 'x = 1  # Add comment'
        }
        
        mock_model = Mock()
        mock_tokenizer = Mock()
        
        # Mock error in Ollama
        with patch('core.ai_tools.ollama_client.get_ollama_response') as mock_ollama:
            mock_ollama.side_effect = Exception("API Error")
            
            explanation = get_ai_explanation(
                suggestion, "ollama", mock_model, mock_tokenizer
            )
        
        self.assertIsInstance(explanation, str)
        self.assertIn('Test issue', explanation)
    
    def test_generate_ollama_explanation(self):
        """Test Ollama explanation generation."""
        suggestion = {
            'description': 'Test issue',
            'code_snippet': 'x = 1',
            'suggested_improvement': 'x = 1  # Add comment'
        }
        
        mock_model = Mock()
        
        # Mock Ollama response
        with patch('core.ai_tools.ollama_client.get_ollama_response') as mock_ollama:
            mock_ollama.return_value = 'This is an AI explanation'
            
            explanation = _generate_ollama_explanation(
                suggestion, mock_model, print
            )
        
        self.assertIsInstance(explanation, str)
        self.assertIn('AI explanation', explanation)
    
    def test_generate_ollama_explanation_error(self):
        """Test Ollama explanation generation with error."""
        suggestion = {
            'description': 'Test issue',
            'code_snippet': 'x = 1',
            'suggested_improvement': 'x = 1  # Add comment'
        }
        
        mock_model = Mock()
        
        # Mock Ollama API error
        with patch('core.ai_tools.ollama_client.get_ollama_response') as mock_ollama:
            mock_ollama.return_value = 'API_ERROR: Connection failed'
            
            explanation = _generate_ollama_explanation(
                suggestion, mock_model, print
            )
        
        self.assertIsInstance(explanation, str)
        self.assertIn('Test issue', explanation)
    
    def test_generate_own_model_explanation(self):
        """Test own model explanation generation."""
        suggestion = {
            'description': 'Test issue',
            'code_snippet': 'x = 1',
            'suggested_improvement': 'x = 1  # Add comment'
        }
        
        mock_model = Mock()
        mock_tokenizer = Mock()
        
        explanation = _generate_own_model_explanation(
            suggestion, mock_model, mock_tokenizer, print
        )
        
        self.assertIsInstance(explanation, str)
        self.assertIn('not yet implemented', explanation)
    
    def test_generate_fallback_explanation(self):
        """Test fallback explanation generation."""
        suggestion = {
            'description': 'Test issue',
            'code_snippet': 'x = 1',
            'suggested_improvement': 'x = 1  # Add comment'
        }
        
        explanation = _generate_fallback_explanation(suggestion)
        
        self.assertIsInstance(explanation, str)
        self.assertIn('Test issue', explanation)
    
    def test_browse_web_tool(self):
        """Test web browsing tool."""
        url = "https://example.com"
        
        # Mock requests and BeautifulSoup
        with patch('core.ai_tools.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.content = '<html><body><p>Test content</p></body></html>'
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            with patch('core.ai_tools.BeautifulSoup') as mock_soup:
                mock_soup_instance = Mock()
                mock_soup_instance.get_text.return_value = 'Test content'
                mock_soup_instance.find_all.return_value = []
                mock_soup.return_value = mock_soup_instance
                
                content = browse_web_tool(url)
        
        self.assertIsInstance(content, str)
        self.assertIn('Test content', content)
    
    def test_browse_web_tool_error(self):
        """Test web browsing tool with error."""
        url = "https://invalid-url.com"
        
        # Mock requests error
        with patch('core.ai_tools.requests.get') as mock_get:
            mock_get.side_effect = Exception("Connection error")
            
            content = browse_web_tool(url)
        
        self.assertIsInstance(content, str)
        self.assertIn('Error:', content)
    
    def test_transcribe_youtube_tool(self):
        """Test YouTube transcription tool."""
        url = "https://www.youtube.com/watch?v=test"
        
        # Mock YouTube transcript API
        with patch('core.ai_tools.YouTubeTranscriptApi.get_transcript') as mock_transcript:
            mock_transcript.return_value = [
                {'text': 'Hello world', 'start': 0.0, 'duration': 2.0},
                {'text': 'This is a test', 'start': 2.0, 'duration': 3.0}
            ]
            
            content = transcribe_youtube_tool(url)
        
        self.assertIsInstance(content, str)
        self.assertIn('Hello world', content)
        self.assertIn('This is a test', content)
    
    def test_transcribe_youtube_tool_error(self):
        """Test YouTube transcription tool with error."""
        url = "https://www.youtube.com/watch?v=invalid"
        
        # Mock YouTube transcript API error
        with patch('core.ai_tools.YouTubeTranscriptApi.get_transcript') as mock_transcript:
            mock_transcript.side_effect = Exception("Video not found")
            
            content = transcribe_youtube_tool(url)
        
        self.assertIsInstance(content, str)
        self.assertIn('Error:', content)
    
    def test_report_generation_with_progress(self):
        """Test report generation with progress callback."""
        suggestions = [
            {
                'file_path': '/test/file.py',
                'line_number': 10,
                'description': 'Test issue',
                'code_snippet': 'x = 1',
                'suggested_improvement': 'x = 1  # Add comment',
                'language': 'python',
                'issue_type': 'performance_issue',
                'severity': 'medium'
            }
        ]
        
        mock_model = Mock()
        mock_tokenizer = Mock()
        
        # Track progress calls
        progress_calls = []
        def progress_callback(current, total, message):
            progress_calls.append((current, total, message))
        
        # Mock the batch processing
        with patch('core.ai_tools.batch_process_suggestions') as mock_batch:
            mock_batch.return_value = ['AI explanation']
            
            report, training_data = generate_report_and_training_data(
                suggestions, "ollama", mock_model, mock_tokenizer,
                progress_callback=progress_callback
            )
        
        self.assertIsInstance(report, str)
        self.assertIsInstance(training_data, str)
        # Should have progress calls
        self.assertGreater(len(progress_calls), 0)
    
    def test_report_generation_with_logging(self):
        """Test report generation with logging callback."""
        suggestions = [
            {
                'file_path': '/test/file.py',
                'line_number': 10,
                'description': 'Test issue',
                'code_snippet': 'x = 1',
                'suggested_improvement': 'x = 1  # Add comment',
                'language': 'python',
                'issue_type': 'performance_issue',
                'severity': 'medium'
            }
        ]
        
        mock_model = Mock()
        mock_tokenizer = Mock()
        
        # Track log calls
        log_calls = []
        def log_callback(message):
            log_calls.append(message)
        
        # Mock the batch processing
        with patch('core.ai_tools.batch_process_suggestions') as mock_batch:
            mock_batch.return_value = ['AI explanation']
            
            report, training_data = generate_report_and_training_data(
                suggestions, "ollama", mock_model, mock_tokenizer,
                log_message_callback=log_callback
            )
        
        self.assertIsInstance(report, str)
        self.assertIsInstance(training_data, str)
        # Should have log messages
        self.assertGreater(len(log_calls), 0)
    
    def test_batch_processing_error_handling(self):
        """Test error handling in batch processing."""
        suggestions = [
            {'description': 'Issue 1'},
            {'description': 'Issue 2'}
        ]
        
        mock_model = Mock()
        mock_tokenizer = Mock()
        
        # Mock error in batch processing
        with patch('core.ai_tools._process_suggestion_batch') as mock_process:
            mock_process.side_effect = Exception("Processing error")
            
            explanations = batch_process_suggestions(
                suggestions, "ollama", mock_model, mock_tokenizer
            )
        
        self.assertIsInstance(explanations, list)
        self.assertEqual(len(explanations), 2)
        # Should have fallback explanations
        for explanation in explanations:
            self.assertIn('AI analysis for issue', explanation)


if __name__ == '__main__':
    unittest.main() 