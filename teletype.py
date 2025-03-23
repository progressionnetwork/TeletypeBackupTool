import os
import re
import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm
import logging
import time

class TeletypeBackup:
    def __init__(self, blog_url):
        self.blog_url = blog_url.rstrip('/')
        self.domain = urlparse(self.blog_url).netloc
        self.start_time = time.time()
        
        # Set up logging
        self.output_dir = f"teletype_backup_{self.domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(self.output_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(self.output_dir, 'backup.log'), encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("TeletypeBackup")
        
        # Initialize selenium with Firefox
        self.setup_selenium()
        
        # Regular HTTP session for downloads
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0'
        })
        
        # Blog metadata
        self.logger.info(f"Starting backup of blog at {self.blog_url}")
        self.blog_info = self.get_blog_info()
        
    def setup_selenium(self):
        """Initialize Selenium WebDriver with Firefox"""
        try:
            options = FirefoxOptions()
            options.add_argument("--headless")
            options.add_argument("--width=1920")
            options.add_argument("--height=1080")
            
            self.driver = webdriver.Firefox(options=options)
            self.logger.info("Firefox WebDriver initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Firefox WebDriver: {str(e)}")
            raise
    
    def log_time_elapsed(self, message):
        """Log message with time elapsed since start"""
        elapsed = time.time() - self.start_time
        elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
        self.logger.info(f"{message} - Time elapsed: {elapsed_str}")
    
    def get_blog_info(self):
        """Get basic blog information"""
        self.logger.info(f"Getting blog info from {self.blog_url}")
        
        self.driver.get(self.blog_url)
        time.sleep(3)  # Allow page to load fully
        
        # Save homepage for reference
        with open(os.path.join(self.output_dir, "homepage.html"), 'w', encoding='utf-8') as f:
            f.write(self.driver.page_source)
            
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        
        # Extract blog title
        title = None
        title_elements = soup.select(".blog__info_name_text")
        if title_elements:
            title = title_elements[0].get_text().strip()
        
        # Extract username
        username = None
        username_elements = soup.select(".blog__info_username")
        if username_elements:
            username_text = username_elements[0].get_text().strip()
            if username_text.startswith("@"):
                username = username_text[1:]
        
        # Extract post count
        post_count = None
        post_count_elements = soup.select(".blog__info_items .blog__info_item:nth-child(3)")
        if post_count_elements:
            post_text = post_count_elements[0].get_text().strip()
            match = re.search(r'(\d+)', post_text)
            if match:
                post_count = int(match.group(1))
        
        # Extract bio
        bio = None
        bio_elements = soup.select(".blog__info_bio")
        if bio_elements:
            bio = bio_elements[0].get_text().strip()
            
        blog_info = {
            "title": title,
            "username": username,
            "post_count": post_count,
            "bio": bio,
            "url": self.blog_url
        }
        
        self.logger.info(f"Blog info: {title}, @{username}, {post_count} posts")
        
        # Save blog info
        with open(os.path.join(self.output_dir, "blog_info.json"), 'w', encoding='utf-8') as f:
            json.dump(blog_info, f, ensure_ascii=False, indent=2)
            
        return blog_info
    
    def scroll_and_get_post_links(self):
        """Scroll through the blog to find all post links"""
        self.logger.info("Scrolling to find all post links...")
        
        # Load main blog page
        self.driver.get(self.blog_url)
        time.sleep(3)
        
        # Start collecting post URLs
        post_urls = []
        previous_count = 0
        max_attempts = 50  # Limit scrolling attempts
        
        # Create progress bar for scrolling
        pbar = tqdm(total=self.blog_info.get('post_count', 100), 
                   desc="Finding posts", 
                   unit="posts")
        
        # Function to extract post URLs from current page state
        def extract_posts():
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            links = []
            # Look for article cards with links
            for article in soup.select(".articleCard"):
                title_link = article.select_one(".articleCard-title a")
                if title_link and title_link.get('href'):
                    href = title_link.get('href')
                    if href.startswith('/'):
                        full_url = f"https://{self.domain}{href}"
                    else:
                        full_url = href
                    links.append(full_url)
            return links
        
        # Scroll and collect posts
        stagnant_count = 0
        for scroll_count in range(max_attempts):
            # Extract posts from current view
            current_posts = extract_posts()
            
            # Count new posts found in this scroll
            new_posts = 0
            for url in current_posts:
                if url not in post_urls:
                    post_urls.append(url)
                    new_posts += 1
            
            # Update progress bar
            pbar.update(new_posts)
            if len(post_urls) >= pbar.total:
                pbar.total = len(post_urls) + 10  # Adjust total if we found more
            
            # Check if we've made progress
            if new_posts == 0:
                stagnant_count += 1
                if stagnant_count > 5:  # Stop if no new posts after 5 scrolls
                    self.logger.info("No new posts found after multiple scrolls, stopping.")
                    break
            else:
                stagnant_count = 0
            
            # Scroll down
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait for content to load
            
            # If we found as many posts as expected, we can stop
            if self.blog_info.get('post_count') and len(post_urls) >= self.blog_info['post_count']:
                self.logger.info(f"Found all {len(post_urls)} posts, stopping scroll.")
                break
        
        # Close progress bar
        pbar.close()
        
        # Save the list of post URLs
        with open(os.path.join(self.output_dir, "post_urls.json"), 'w', encoding='utf-8') as f:
            json.dump(post_urls, f, ensure_ascii=False, indent=2)
            
        self.log_time_elapsed(f"Found a total of {len(post_urls)} posts")
        return post_urls
    
    def download_post(self, url):
        """Download and save a single post"""
        try:
            # Get the post slug for the directory name
            parsed_url = urlparse(url)
            slug = parsed_url.path.strip('/')
            
            # Ensure slug is valid for filesystem
            safe_slug = re.sub(r'[^\w\-]', '_', slug)
            post_dir = os.path.join(self.output_dir, 'posts', safe_slug)
            os.makedirs(post_dir, exist_ok=True)
            
            # Load the post page
            self.driver.get(url)
            time.sleep(3)  # Allow page to fully load
            
            # Save original HTML
            with open(os.path.join(post_dir, "original.html"), 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
                
            # Parse the post content
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Extract post metadata
            post_data = {
                'url': url,
                'slug': slug,
                'title': None,
                'date': None,
                'author': None,
                'content': None
            }
            
            # Title
            title_elem = soup.select_one(".article__title")
            if title_elem:
                post_data['title'] = title_elem.get_text().strip()
            else:
                # Try other title selectors if needed
                title_elem = soup.select_one("h1") or soup.select_one("title")
                if title_elem:
                    title_text = title_elem.get_text().strip()
                    # Remove blog name if present
                    if " — " in title_text:
                        post_data['title'] = title_text.split(" — ")[0].strip()
                    else:
                        post_data['title'] = title_text
            
            # Date
            date_elem = soup.select_one(".article__date")
            if date_elem:
                post_data['date'] = date_elem.get_text().strip()
            
            # Author
            author_elem = soup.select_one(".article__authorName")
            if author_elem:
                post_data['author'] = author_elem.get_text().strip()
            elif self.blog_info.get('title'):
                post_data['author'] = self.blog_info['title']
            
            # Content
            content_elem = soup.select_one(".article__content")
            if not content_elem:
                # Try alternative content selectors
                content_elem = soup.select_one("article") or soup.select_one(".post-content") or soup.select_one(".entry-content")
            
            if content_elem:
                # Download images and other assets
                for img in content_elem.find_all('img'):
                    if img.get('src'):
                        img_url = img['src']
                        if not img_url.startswith(('http://', 'https://')):
                            img_url = urljoin(url, img_url)
                        
                        # Download the image
                        try:
                            img_filename = os.path.basename(urlparse(img_url).path)
                            if not img_filename:
                                img_filename = f"image_{hash(img_url) % 10000}.jpg"
                            
                            # Create assets directory
                            assets_dir = os.path.join(post_dir, "assets")
                            os.makedirs(assets_dir, exist_ok=True)
                            
                            # Download and save the image
                            img_path = os.path.join(assets_dir, img_filename)
                            response = self.session.get(img_url, stream=True)
                            if response.status_code == 200:
                                with open(img_path, 'wb') as f:
                                    for chunk in response.iter_content(chunk_size=8192):
                                        f.write(chunk)
                                
                                # Update the image source in HTML
                                img['src'] = f"assets/{img_filename}"
                        except Exception as e:
                            self.logger.error(f"Error downloading image {img_url}: {str(e)}")
                
                # Save the content with updated image links
                post_data['content'] = str(content_elem)
            
            # Create markdown content
            md_content = f"---\n"
            if post_data['title']:
                md_content += f'title: "{post_data["title"]}"\n'
            if post_data['date']:
                md_content += f'date: "{post_data["date"]}"\n'
            if post_data['author']:
                md_content += f'author: "{post_data["author"]}"\n'
            md_content += f'url: "{post_data["url"]}"\n'
            md_content += f'slug: "{post_data["slug"]}"\n'
            md_content += "---\n\n"
            
            if post_data['content']:
                md_content += post_data['content']
            
            # Save as markdown file
            with open(os.path.join(post_dir, "index.md"), 'w', encoding='utf-8') as f:
                f.write(md_content)
                
            # Save post data as JSON
            with open(os.path.join(post_dir, "post.json"), 'w', encoding='utf-8') as f:
                json.dump(post_data, f, ensure_ascii=False, indent=2)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error downloading post {url}: {str(e)}")
            return False
    
    def check_section_posts(self, section_url):
        """Get posts from a specific section"""
        self.logger.info(f"Checking section: {section_url}")
        
        self.driver.get(section_url)
        time.sleep(3)  # Allow page to load
        
        # Scroll to get all posts in this section
        post_urls = []
        previous_count = 0
        max_scrolls = 30
        
        # Create progress bar for scrolling this section
        pbar = tqdm(total=max_scrolls, 
                   desc=f"Scrolling section {urlparse(section_url).path}", 
                   unit="scroll")
        
        for scroll in range(max_scrolls):
            pbar.update(1)
            
            # Extract posts from current view
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            for article in soup.select(".articleCard"):
                title_link = article.select_one(".articleCard-title a")
                if title_link and title_link.get('href'):
                    href = title_link.get('href')
                    if href.startswith('/'):
                        full_url = f"https://{self.domain}{href}"
                    else:
                        full_url = href
                    if full_url not in post_urls:
                        post_urls.append(full_url)
            
            # Update progress description with count
            pbar.set_description(f"Section {urlparse(section_url).path} ({len(post_urls)} posts)")
            
            # Check if we found new posts
            if len(post_urls) == previous_count:
                # No new posts after scrolling, we're probably at the end
                if scroll > 3:  # Give it a few scrolls to be sure
                    break
            else:
                previous_count = len(post_urls)
            
            # Scroll down
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        pbar.close()
        self.logger.info(f"Found {len(post_urls)} posts in section {section_url}")
        return post_urls

    def find_all_sections(self):
        """Find all sections in the blog"""
        self.logger.info("Finding all blog sections...")
        
        self.driver.get(self.blog_url)
        time.sleep(3)
        
        sections = []
        
        # Extract sections from the page
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        section_links = soup.select(".blog__section_item")
        
        for link in section_links:
            href = link.get('href')
            if href and href != self.blog_url and href != '/':
                # Make sure it's a full URL
                if href.startswith('/'):
                    section_url = f"https://{self.domain}{href}"
                elif not href.startswith('http'):
                    section_url = f"{self.blog_url}/{href.lstrip('/')}"
                else:
                    section_url = href
                
                # Get the section name
                section_name = link.get_text().strip()
                sections.append({
                    'name': section_name,
                    'url': section_url
                })
        
        self.logger.info(f"Found {len(sections)} sections")
        
        # Save sections info
        with open(os.path.join(self.output_dir, "sections.json"), 'w', encoding='utf-8') as f:
            json.dump(sections, f, ensure_ascii=False, indent=2)
            
        return sections
    
    def backup_with_sections(self):
        """Backup the blog by exploring all sections"""
        try:
            # Create posts directory
            os.makedirs(os.path.join(self.output_dir, 'posts'), exist_ok=True)
            
            # Find all sections
            sections = self.find_all_sections()
            
            # Collect posts from each section
            all_posts = []
            
            # Create progress bar for sections
            section_pbar = tqdm(total=len(sections) + 1, 
                              desc="Processing sections", 
                              unit="section")
            
            # Add main page (all posts)
            section_pbar.set_description("Processing main page")
            all_posts.extend(self.check_section_posts(self.blog_url))
            section_pbar.update(1)
            
            # Add each section's posts
            for section in sections:
                section_pbar.set_description(f"Processing section: {section['name']}")
                section_posts = self.check_section_posts(section['url'])
                all_posts.extend(section_posts)
                section_pbar.update(1)
            
            section_pbar.close()
            
            # Remove duplicates while preserving order
            unique_posts = []
            for post in all_posts:
                if post not in unique_posts:
                    unique_posts.append(post)
            
            self.log_time_elapsed(f"Found {len(unique_posts)} unique posts across all sections")
            
            # Save post URLs
            with open(os.path.join(self.output_dir, "post_urls.json"), 'w', encoding='utf-8') as f:
                json.dump(unique_posts, f, ensure_ascii=False, indent=2)
            
            # Download each post with progress bar
            successful = 0
            failed = 0
            
            post_pbar = tqdm(total=len(unique_posts), 
                           desc="Downloading posts", 
                           unit="post")
            
            for i, url in enumerate(unique_posts):
                # Extract post name for better progress description
                post_name = url.split('/')[-1]
                post_pbar.set_description(f"Downloading post: {post_name}")
                
                if self.download_post(url):
                    successful += 1
                else:
                    failed += 1
                
                post_pbar.update(1)
                post_pbar.set_postfix({"success": successful, "failed": failed})
                
                # Be nice to the server
                time.sleep(1)
            
            post_pbar.close()
            
            # Calculate elapsed time
            elapsed = time.time() - self.start_time
            elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
            
            # Save summary
            summary = {
                "blog_url": self.blog_url,
                "domain": self.domain,
                "title": self.blog_info.get('title'),
                "username": self.blog_info.get('username'),
                "sections": len(sections),
                "total_posts": len(unique_posts),
                "successful_downloads": successful,
                "failed_downloads": failed,
                "backup_date": datetime.now().isoformat(),
                "elapsed_time": elapsed_str
            }
            
            with open(os.path.join(self.output_dir, "backup_summary.json"), 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
                
            self.log_time_elapsed(f"Backup complete! Saved {successful}/{len(unique_posts)} posts to {self.output_dir}")
            
        except Exception as e:
            self.logger.error(f"Error during backup: {str(e)}")
        finally:
            # Clean up
            if hasattr(self, 'driver'):
                self.driver.quit()


if __name__ == "__main__":
    print("Teletype Blog Backup Tool")
    print("------------------------")
    blog_url = input("Enter your blog URL (e.g., https://titanida.com): ")
    
    start_time = time.time()
    backup = TeletypeBackup(blog_url)
    
    # Choose the more complete backup method that checks each section
    backup.backup_with_sections()
    
    # Show total time
    elapsed = time.time() - start_time
    elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
    print(f"Done! Total time: {elapsed_str}")
