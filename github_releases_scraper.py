#!/usr/bin/env python3
"""
GitHub Releases Scraper

This script uses the GitHub REST API to fetch release information from a specified repository
and provides version numbers and release dates.

It extracts major.minor version numbers (e.g., v24.1 from v24.1.1) to enable grouping
of releases by their major.minor version.

Usage:
    python github_releases_scraper.py --owner OWNER --repo REPO [--limit LIMIT] [--all]

Requirements:
    - requests
    - python-dotenv

Setup:
    1. Create a GitHub Personal Access Token (classic) with 'repo' scope
    2. Store it in a .env file as GITHUB_TOKEN=your_token_here
"""

import os
import argparse
import requests
import json
import csv
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get GitHub token from environment variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise ValueError("GitHub token not found. Please set GITHUB_TOKEN in your .env file.")

# GitHub API base URL
GITHUB_API_BASE = "https://api.github.com"

# Headers for API requests
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

def fetch_releases(owner, repo, limit=10, fetch_all=False):
    """
    Fetch releases from a GitHub repository using REST API.
    
    Args:
        owner: Repository owner (username or organization)
        repo: Repository name
        limit: Maximum number of releases to fetch (ignored if fetch_all is True)
        fetch_all: Whether to fetch all releases
    
    Returns:
        list: List of release data
    """
    releases = []
    page = 1
    per_page = 100  # GitHub API max per page
    
    while True:
        # Build the API URL
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/releases"
        params = {"page": page, "per_page": per_page}
        
        # Make the request
        response = requests.get(url, headers=HEADERS, params=params)
        
        # Check for errors
        if response.status_code != 200:
            raise Exception(f"API request failed with status code {response.status_code}. Response: {response.text}")
        
        # Parse the response
        page_releases = response.json()
        
        # Add releases to our list
        releases.extend(page_releases)
        
        # If we got fewer results than per_page, we've reached the end
        if len(page_releases) < per_page:
            break
            
        # If we've reached the limit and not fetching all, stop
        if not fetch_all and len(releases) >= limit:
            releases = releases[:limit]  # Trim to limit
            break
            
        # Move to the next page
        page += 1
    
    return releases

def extract_release_info(releases):
    """
    Extract relevant information from release data.
    
    Args:
        releases: List of release data from GitHub API
    
    Returns:
        list: List of dictionaries with extracted release information
    """
    release_info = []
    import re
    
    for release in releases:
        # Extract relevant fields
        info = {
            "tag_name": release["tag_name"],
            "name": release["name"] if release["name"] else release["tag_name"],
            "published_at": release["published_at"],
            "created_at": release["created_at"],
            "url": release["html_url"],
            "prerelease": release["prerelease"],
            "draft": release["draft"]
        }
        
        # Extract major.minor version
        tag = info["tag_name"]
        # Remove leading 'v' or 'V' if present
        if tag.lower().startswith('v'):
            tag = tag[1:]
        
        # Try to extract major.minor using regex
        # First, try to find major.minor.patch pattern
        version_match = re.search(r'(\d+\.\d+)(?:\.\d+)?', tag)
        if version_match:
            info["major_minor"] = f"v{version_match.group(1)}"
        else:
            # If no match found, check if the tag itself is a major.minor version
            if re.match(r'^\d+\.\d+$', tag):
                info["major_minor"] = f"v{tag}"
            else:
                # If still no match found, set to None
                info["major_minor"] = None
        
        # Format dates
        if info["published_at"]:
            published_date = datetime.fromisoformat(info["published_at"].replace("Z", "+00:00"))
            info["published_date"] = published_date.strftime("%Y-%m-%d")
        else:
            info["published_date"] = None
            
        release_info.append(info)
    
    return release_info

def display_releases(releases_info):
    """
    Display release information in a formatted table.
    
    Args:
        releases_info: List of dictionaries with release information
    """
    # Print header
    print("\n{:<20} {:<15} {:<30} {:<12} {:<10} {:<10}".format(
        "Version", "Major.Minor", "Name", "Release Date", "Prerelease", "Draft"
    ))
    print("-" * 100)
    
    # Print each release
    for release in releases_info:
        print("{:<20} {:<15} {:<30} {:<12} {:<10} {:<10}".format(
            release["tag_name"],
            release["major_minor"] if release["major_minor"] else "N/A",
            release["name"][:27] + "..." if len(release["name"]) > 30 else release["name"],
            release["published_date"] if release["published_date"] else "N/A",
            "Yes" if release["prerelease"] else "No",
            "Yes" if release["draft"] else "No"
        ))

def save_as_json(releases_info, output_file):
    """
    Save release information as JSON.
    
    Args:
        releases_info: List of dictionaries with release information
        output_file: Path to the output file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(releases_info, f, indent=2)
    
    return output_file

def save_as_csv(releases_info, output_file):
    """
    Save release information as CSV.
    
    Args:
        releases_info: List of dictionaries with release information
        output_file: Path to the output file
    """
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ["tag_name", "major_minor", "name", "published_date", "url", "prerelease", "draft"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        for release in releases_info:
            writer.writerow({k: release[k] for k in fieldnames})
    
    return output_file

def test_major_minor_extraction():
    """
    Test the major.minor version extraction for various version formats.
    This is a development function to verify the regex pattern works correctly.
    """
    import re
    
    test_cases = [
        # Standard formats
        ("v1.2.3", "v1.2"),
        ("1.2.3", "v1.2"),
        ("v10.20.30", "v10.20"),
        
        # Major.minor only (no patch)
        ("v1.2", "v1.2"),
        ("1.2", "v1.2"),
        
        # Pre-release identifiers
        ("v1.2.3-beta", "v1.2"),
        ("1.2.3-alpha.1", "v1.2"),
        
        # Build metadata
        ("v1.2.3+build123", "v1.2"),
        ("1.2.3+build.456", "v1.2"),
        
        # Prefixed versions
        ("release-v1.2.3", "v1.2"),
        ("node-v10.15.3", "v10.15"),
        
        # Multiple dots
        ("v1.2.3.4", "v1.2"),
        
        # Single number
        ("v5", None),
        ("5", None),
    ]
    
    results = []
    
    for test_case, expected in test_cases:
        tag = test_case
        # Remove leading 'v' or 'V' if present
        if tag.lower().startswith('v'):
            tag = tag[1:]
            
        # First, try to find major.minor.patch pattern
        version_match = re.search(r'(\d+\.\d+)(?:\.\d+)?', tag)
        if version_match:
            major_minor = f"v{version_match.group(1)}"
        else:
            # If no match found, check if the tag itself is a major.minor version
            if re.match(r'^\d+\.\d+$', tag):
                major_minor = f"v{tag}"
            else:
                # If still no match found, set to None
                major_minor = None
                
        results.append((test_case, major_minor, expected, major_minor == expected))
    
    # Print results
    print("\nMajor.Minor Version Extraction Test")
    print("=" * 60)
    print(f"{'Version':<20} {'Extracted':<15} {'Expected':<15} {'Result':<10}")
    print("-" * 60)
    
    for test_case, extracted, expected, passed in results:
        print(f"{test_case:<20} {extracted if extracted else 'None':<15} {expected if expected else 'None':<15} {'✓' if passed else '✗'}")
    
    # Check if all tests passed
    all_passed = all(r[3] for r in results)
    print("\n" + ("All tests passed!" if all_passed else "Some tests failed!"))
    
    return all_passed

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description="Fetch release information from a GitHub repository")
    parser.add_argument("--owner", required=True, help="Repository owner (username or organization)")
    parser.add_argument("--repo", required=True, help="Repository name")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of releases to fetch")
    parser.add_argument("--all", action="store_true", help="Fetch all releases (ignores limit)")
    parser.add_argument("--format", choices=["table", "json", "csv"], default="table", 
                        help="Output format (default: table)")
    parser.add_argument("--output", help="Output file for JSON or CSV format")
    parser.add_argument("--test", action="store_true", help="Run tests for major.minor version extraction")
    
    args = parser.parse_args()
    
    if args.test:
        test_major_minor_extraction()
        return
    
    limit_str = "all" if args.all else args.limit
    print(f"Fetching {limit_str} releases from {args.owner}/{args.repo}...")
    
    try:
        # Fetch releases
        releases = fetch_releases(args.owner, args.repo, args.limit, args.all)
        
        # Extract relevant information
        releases_info = extract_release_info(releases)
        
        print(f"Found {len(releases_info)} releases")
        
        # Display or save based on format
        if args.format == "table":
            display_releases(releases_info)
        else:
            # Determine output filename if not specified
            if not args.output:
                args.output = f"{args.owner}_{args.repo}_releases.{args.format}"
            
            # Save to file
            if args.format == "json":
                filepath = save_as_json(releases_info, args.output)
            elif args.format == "csv":
                filepath = save_as_csv(releases_info, args.output)
                
            print(f"\nRelease information saved to {filepath}")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
