# Teletype Blog Backup Tool

A comprehensive tool to backup Teletype blogs, capturing all posts, images, and content. This utility can handle custom domain Teletype blogs (like titanida.com) and preserves the original content structure.

[Teletype Backup Demo](https://example.com/demo.gif)

## Features

- 📚 Backs up all posts from any Teletype blog
- 🔍 Intelligently discovers content by navigating through sections
- 📷 Downloads and properly links all images and assets
- 📊 Displays real-time progress with detailed metrics
- 📅 Preserves metadata like publish dates and authors
- 📝 Creates Markdown files for each post
- 🌐 Supports custom domain Teletype blogs
- 📄 Generates detailed backup summaries and logs

## Requirements

- Python 3.7+
- Firefox browser
- Geckodriver (Firefox WebDriver)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/teletype-backup.git
   cd teletype-backup
   ```

2. Install the required Python packages:
   ```bash
   pip install requests beautifulsoup4 selenium tqdm
   ```

3. Install Firefox browser if you don't already have it.

4. Install geckodriver (Firefox WebDriver):
   - **Windows**: Download from [geckodriver releases](https://github.com/mozilla/geckodriver/releases) and add to your PATH
   - **Ubuntu/Debian**: `sudo apt install firefox-geckodriver`
   - **macOS**: `brew install geckodriver`
   - **Arch Linux**: `sudo pacman -S geckodriver`

## Usage

### Basic Usage

Run the script and follow the prompts:

```bash
python teletype_backup.py
```

When prompted, enter the URL of the Teletype blog you want to backup (e.g., `https://titanida.com`).

### Command Line Arguments

```bash
python teletype_backup.py --url https://titanida.com --output ./backups
```

Options:
- `--url`: The URL of the Teletype blog to backup
- `--output`: Directory to save the backup (default: automatically generated)
- `--sections`: Whether to backup by exploring all sections (default: true)
- `--delay`: Delay between requests in seconds (default: 1)
- `--max-scrolls`: Maximum number of scrolls per section (default: 30)

## Output Structure

The backup tool creates a structured output directory:

```
teletype_backup_domain_YYYYMMDD_HHMMSS/
├── backup.log                 # Detailed log of the backup process
├── backup_summary.json        # Summary of the backup operation
├── blog_info.json             # Metadata about the blog
├── homepage.html              # Original HTML of the homepage
├── post_urls.json             # List of all discovered post URLs
├── sections.json              # Information about blog sections
└── posts/                     # Directory containing all posts
    ├── post-slug-1/           # Directory for each post
    │   ├── index.md           # Markdown version of the post
    │   ├── original.html      # Original HTML of the post
    │   ├── post.json          # Post metadata in JSON format
    │   └── assets/            # Downloaded images and other assets
    └── post-slug-2/
        └── ...
```

## Features in Detail

### Post Discovery

The tool uses several techniques to discover all posts:
- Scrolls through the main blog page to load all posts
- Analyzes each section/category listed in the blog's navigation
- Uses separate scrolling for each section to ensure all posts are found
- Eliminates duplicates while preserving post order

### Content Preservation

For each post, the tool:
- Saves the original HTML for reference
- Creates a Markdown version with proper front matter
- Downloads all images and updates links to point to local copies
- Preserves post metadata (title, date, author)

### Progress Tracking

The tool provides detailed progress feedback:
- Progress bars for each stage of the backup
- Real-time counts of discovered and processed posts
- Timing information showing elapsed time
- Post-by-post status updates

## Common Issues and Solutions

### Selenium WebDriver Issues

**Problem**: `WebDriverException: Message: 'geckodriver' executable needs to be in PATH`

**Solution**: Ensure you've installed geckodriver and it's in your system PATH.

### Encoding Problems

**Problem**: Post titles or content shows as garbled text

**Solution**: The tool automatically handles UTF-8 encoding. If you still see issues, check if your terminal supports UTF-8.

### Slow Backup Process

**Problem**: Backup is taking a long time

**Solution**: The tool intentionally adds delays between requests to avoid overwhelming the server. You can adjust the delay with `--delay` but use caution not to overload the server.

## Technical Details

This tool uses:
- **Selenium** for browser automation and scrolling
- **BeautifulSoup** for HTML parsing
- **Requests** for image downloads
- **TQDM** for progress visualization

All content is downloaded respecting copyright and fair use principles. This tool is intended for personal backups only.

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Acknowledgments

- Thanks to the Teletype platform for creating a great blogging experience
- Inspired by various web archiving and backup tools

---

⭐ If this tool helped you, please consider giving it a star on GitHub! ⭐
