# Web Scraping Guide

## Overview

The AI Coder Assistant provides robust web scraping capabilities for acquiring documentation and training data. The system supports two modes of operation: Enhanced and Simple, with built-in safeguards for reliability and performance.

## Features

### Enhanced Mode (Recommended for Documentation)
- Multi-page crawling with configurable depth
- Smart link following with domain restrictions
- Concurrent processing with proper resource management
- Automatic content cleaning and formatting
- Progress tracking and cancellation support
- Robust error handling and recovery
- Session management to prevent connection issues
- Memory usage optimization

### Simple Mode (Single Page)
- Fast single-page extraction
- No link following
- Minimal resource usage
- Perfect for quick content grabs

## Configuration Parameters

### Enhanced Mode Parameters
- **Max Pages** (default: 15)
  - Range: 1-50
  - Controls how many pages to scrape per URL
  - Higher values mean more content but longer processing time

- **Max Depth** (default: 4)
  - Range: 1-10
  - Controls how deep to follow links from the starting page
  - Higher values explore more nested content

- **Same Domain Only** (default: true)
  - When enabled, only follows links on the same domain
  - Recommended for focused documentation scraping

- **Links Per Page** (default: 50)
  - Maximum number of links to extract from each page
  - Helps prevent overwhelming target servers

- **Timeout** (default: 30 seconds)
  - Overall timeout for processing each URL
  - Individual requests have shorter timeouts (5 seconds)

### Resource Management
- Maximum 4 concurrent threads for web scraping
- Automatic session cleanup
- Memory usage limits (50KB per page)
- Proper thread naming for debugging
- Graceful cancellation handling

## Usage Examples

### Basic Usage
```python
from backend.services.acquire import crawl_docs

urls = [
    "https://docs.python.org/3/library/",
    "https://docs.python.org/3/tutorial/"
]

result = crawl_docs(urls, "output_dir")
```

### Advanced Configuration
```python
result = crawl_docs(
    urls,
    "output_dir",
    max_pages=20,
    max_depth=5,
    same_domain_only=True,
    links_per_page=30,
    timeout=45
)
```

### Progress Tracking
```python
def log_progress(message):
    print(f"Progress: {message}")

def update_progress(current, total, message):
    print(f"{current}/{total}: {message}")

result = crawl_docs(
    urls,
    "output_dir",
    log_message_callback=log_progress,
    progress_callback=update_progress
)
```

## Error Handling

The system handles various error conditions:
- Network timeouts
- Invalid URLs
- Server errors
- Memory limits
- Cancellation requests

Each error is logged and included in the result summary:
```python
{
    "success_count": int,  # Number of successfully scraped URLs
    "total": int,         # Total URLs attempted
    "files": List[str],   # Paths to saved files
    "urls": List[str],    # Successfully scraped URLs
    "errors": List[str]   # Error messages if any
}
```

## Best Practices

1. **Start Small**
   - Begin with a few URLs to test
   - Gradually increase parameters as needed

2. **Domain Respect**
   - Keep `same_domain_only=True` when possible
   - Use reasonable delays between requests (built-in)
   - Honor robots.txt (automatic)

3. **Resource Management**
   - Monitor memory usage with large sites
   - Use cancellation callback for long-running jobs
   - Clean up output directory periodically

4. **Error Handling**
   - Always check the result summary
   - Log errors for troubleshooting
   - Implement retries for important content

5. **Content Quality**
   - Verify scraped content quality
   - Adjust parameters if content is incomplete
   - Use appropriate timeouts for slow sites

## Troubleshooting

### Common Issues

1. **Timeouts**
   - Increase timeout parameter
   - Reduce concurrent threads
   - Check network connectivity

2. **Memory Usage**
   - Reduce max_pages
   - Reduce max_depth
   - Clean up old files

3. **Missing Content**
   - Check max_depth setting
   - Verify URL accessibility
   - Check for JavaScript requirements

4. **Performance**
   - Adjust concurrent threads
   - Use Simple mode for basic needs
   - Implement proper error handling

### Debug Logging

Enable detailed logging to troubleshoot issues:
```python
def detailed_log(message):
    print(f"[DEBUG] {message}")

result = crawl_docs(
    urls,
    "output_dir",
    log_message_callback=detailed_log
)
```

## Security Considerations

1. **URL Validation**
   - Only HTTPS URLs are recommended
   - Validate URLs before processing
   - Implement domain whitelisting

2. **Resource Protection**
   - Timeout limits prevent hanging
   - Memory limits prevent overflow
   - Concurrent thread limits

3. **Content Safety**
   - Content size limits
   - File path sanitization
   - Output directory protection

## Future Improvements

1. **Planned Features**
   - JavaScript rendering support
   - Custom content extractors
   - Advanced filtering options
   - Improved content cleaning

2. **Performance Optimizations**
   - Adaptive concurrency
   - Smarter link prioritization
   - Better memory management

## API Reference

### crawl_docs
```python
def crawl_docs(
    urls: List[str],
    output_dir: str,
    **kwargs: Any
) -> Dict[str, Any]
```

**Parameters:**
- `urls`: List of URLs to scrape
- `output_dir`: Directory to save scraped content
- `**kwargs`: Optional parameters including:
  - `log_message_callback`: Logging function
  - `progress_callback`: Progress update function
  - `cancellation_callback`: Function to check for cancellation
  - `max_pages`: Maximum pages per URL
  - `max_depth`: Maximum link depth
  - `same_domain_only`: Domain restriction
  - `timeout`: Operation timeout
  - `links_per_page`: Links to follow per page

**Returns:**
Dictionary containing:
- `success_count`: Successful scrapes
- `total`: Total attempts
- `files`: Saved file paths
- `urls`: Processed URLs
- `errors`: Error messages 