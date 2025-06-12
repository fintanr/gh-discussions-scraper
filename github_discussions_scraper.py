#!/usr/bin/env python3
"""
GitHub Discussions Scraper

This script uses the GitHub GraphQL API to fetch discussions from a specified repository
and saves them as markdown files.

Usage:
    python github_discussions_scraper.py --owner OWNER --repo REPO [--category CATEGORY] [--limit LIMIT]

Requirements:
    - requests
    - python-dotenv

Setup:
    1. Create a GitHub Personal Access Token with 'repo' scope
    2. Store it in a .env file as GITHUB_TOKEN=your_token_here
"""

import os
import re
import json
import argparse
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get GitHub token from environment variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise ValueError("GitHub token not found. Please set GITHUB_TOKEN in your .env file.")

# GraphQL API endpoint
GITHUB_API = "https://api.github.com/graphql"

# Headers for API requests
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json",
}

def sanitize_filename(name):
    """Convert a string to a valid filename."""
    # Replace spaces and special characters
    name = re.sub(r'[^\w\s-]', '', name.lower())
    name = re.sub(r'[\s]+', '_', name)
    return name[:100]  # Limit filename length

def format_discussion_as_markdown(discussion, include_comments=False):
    """
    Format a discussion as markdown content.
    
    Args:
        discussion: The discussion data from GitHub API
        include_comments: Whether to include comments in the output
    
    Returns:
        str: Formatted markdown content
    """
    # Basic discussion metadata
    title = discussion["title"]
    author = discussion["author"]["login"] if discussion["author"] else "Anonymous"
    created_at = discussion["createdAt"]
    body = discussion["body"]
    url = discussion["url"]
    
    # Format the discussion header
    md_content = f"# {title}\n\n"
    md_content += f"**Author:** [{author}](https://github.com/{author})  \n"
    md_content += f"**Created:** {created_at}  \n"
    md_content += f"**URL:** {url}  \n\n"
    md_content += f"## Discussion\n\n{body}\n\n"
    
    # Add comments if enabled and available
    if include_comments and "comments" in discussion and discussion["comments"]["nodes"]:
        md_content += "## Comments\n\n"
        for comment in discussion["comments"]["nodes"]:
            comment_author = comment["author"]["login"] if comment["author"] else "Anonymous"
            md_content += f"### [{comment_author}](https://github.com/{comment_author}) - {comment['createdAt']}\n\n"
            md_content += f"{comment['body']}\n\n"
    
    return md_content

def fetch_discussions(owner, repo, category=None, limit=10):
    """
    Fetch discussions from a GitHub repository using GraphQL API.
    
    Args:
        owner: Repository owner (username or organization)
        repo: Repository name
        category: Optional category name to filter discussions
        limit: Maximum number of discussions to fetch
    
    Returns:
        list: List of discussion data
    """
    # Build the GraphQL query
    category_filter = f', categoryId: "{category}"' if category else ""
    query = """
    query($owner: String!, $repo: String!, $limit: Int!) {
      repository(owner: $owner, name: $repo) {
        discussions(first: $limit%s) {
          nodes {
            id
            title
            body
            url
            createdAt
            author {
              login
            }
            category {
              name
            }
            comments(first: 50) {
              nodes {
                author {
                  login
                }
                body
                createdAt
              }
            }
          }
        }
      }
    }
    """ % category_filter
    
    # Variables for the GraphQL query
    variables = {
        "owner": owner,
        "repo": repo,
        "limit": limit
    }
    
    # Make the request
    response = requests.post(
        GITHUB_API,
        headers=HEADERS,
        json={"query": query, "variables": variables}
    )
    
    # Check for errors
    if response.status_code != 200:
        raise Exception(f"Query failed with status code {response.status_code}. Response: {response.text}")
    
    # Parse the response
    result = response.json()
    
    if "errors" in result:
        raise Exception(f"GraphQL query error: {json.dumps(result['errors'], indent=2)}")
    
    # Extract and return discussions
    return result["data"]["repository"]["discussions"]["nodes"]

def save_discussion_as_markdown(discussion, output_dir, include_comments=False):
    """
    Save a discussion as a markdown file.
    
    Args:
        discussion: The discussion data
        output_dir: Directory to save the file
        include_comments: Whether to include comments in the output
    
    Returns:
        str: Path to the saved file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a filename from the discussion title
    date_prefix = datetime.fromisoformat(discussion["createdAt"].replace("Z", "+00:00")).strftime("%Y%m%d")
    filename = f"{date_prefix}-{sanitize_filename(discussion['title'])}.md"
    filepath = os.path.join(output_dir, filename)
    
    # Format the discussion as markdown
    md_content = format_discussion_as_markdown(discussion, include_comments)
    
    # Save to file
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    return filepath

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description="Fetch discussions from a GitHub repository")
    parser.add_argument("--owner", required=True, help="Repository owner (username or organization)")
    parser.add_argument("--repo", required=True, help="Repository name")
    parser.add_argument("--category", help="Filter by category name")
    parser.add_argument("--output-dir", default="discussions", help="Directory to save markdown files")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of discussions to fetch")
    parser.add_argument("--include-comments", action="store_true", help="Include comments in the output")
    
    args = parser.parse_args()
    
    print(f"Fetching up to {args.limit} discussions from {args.owner}/{args.repo}...")
    
    try:
        # Fetch discussions
        discussions = fetch_discussions(args.owner, args.repo, args.category, args.limit)
        
        # Create output directory if specified
        output_dir = args.output_dir
        if not os.path.isabs(output_dir):
            output_dir = os.path.join(os.getcwd(), output_dir)
        
        print(f"Found {len(discussions)} discussions")
        
        # Save each discussion as markdown
        for i, discussion in enumerate(discussions, 1):
            filepath = save_discussion_as_markdown(discussion, output_dir, args.include_comments)
            print(f"[{i}/{len(discussions)}] Saved: {os.path.basename(filepath)}")
        
        print(f"\nAll discussions saved to {output_dir}")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
