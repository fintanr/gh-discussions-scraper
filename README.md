# GitHub Discussions & Releases Scraper

This repository contains scripts that use the GitHub APIs to fetch discussions and releases from specified repositories.

## GitHub Discussions Scraper

This script uses the GitHub GraphQL API to fetch discussions from a specified repository and save them as markdown files.

## Features

- Fetch discussions from any public or authorized GitHub repository
- Filter discussions by category
- Save discussions including comments as markdown files
- Custom formatting of discussion content
- Limit the number of discussions to fetch

## Requirements

- Python 3.6+
- `requests` library
- `python-dotenv` library

## Setup

1. Create a GitHub Personal Access Token:
   - Go to GitHub Settings > Developer settings > Personal access tokens
   - Generate a new token with the `repo` scope, we recommend limiting to just discussions with read only access
   - Copy the token. 

2. Create a `.env` file in the same directory as the script:
   ```
   GITHUB_TOKEN=your_github_token_here
   ```

3. Install the required packages:
   ```bash
   pip install requests python-dotenv
   ```

## Usage

Basic usage:
```bash
python github_discussions_scraper.py --owner OWNER --repo REPO
```

With additional options:
```bash
python github_discussions_scraper.py --owner OWNER --repo REPO --category CATEGORY_NAME --limit 20 --output-dir ./my_discussions --include-comments
```

We suggest using venv for your environment
```bash
python3 -m venv venc
source venv/bin/acticate
pip install -r requirements.txt
```
### Arguments

- `--owner`: Repository owner (username or organization) - REQUIRED
- `--repo`: Repository name - REQUIRED
- `--category`: Filter discussions by category name
- `--limit`: Maximum number of discussions to fetch (default: 10)
- `--output-dir`: Directory to save markdown files (default: './discussions')
- `--include-comments`: Include discussion comments in the output (by default, comments are excluded)

## Output Format

Each discussion is saved as a markdown file with the following structure:

```markdown
# Discussion Title

**Author:** [username](https://github.com/username)  
**Created:** 2023-06-01T12:34:56Z  
**URL:** https://github.com/owner/repo/discussions/123  

## Discussion

The content of the discussion goes here...
```

If the `--include-comments` flag is used, comments will also be included:

```markdown
## Comments

### [commenter](https://github.com/commenter) - 2023-06-01T13:45:12Z

Comment content goes here...
```

## Example

```bash
python github_discussions_scraper.py --owner microsoft --repo vscode --limit 5
```

This will fetch the 5 most recent discussions from the Microsoft VS Code repository and save them as markdown files in the `./discussions` directory.

To include comments:

```bash
python github_discussions_scraper.py --owner microsoft --repo vscode --limit 5 --include-comments
```

## GitHub Releases Scraper

This script uses the GitHub REST API to fetch release information from a specified repository and provides version numbers and release dates.

### Features

- Fetch releases from any public or authorized GitHub repository
- Option to fetch all releases or limit to a specific number
- Extracts major.minor version numbers (e.g., v24.1 from v24.1.1) for easier grouping of releases
- Display release information in a formatted table
- Export data to JSON or CSV formats
- Filter out prerelease and draft releases (information is included in output)

### Usage

Basic usage:
```bash
python github_releases_scraper.py --owner OWNER --repo REPO
```

With additional options:
```bash
python github_releases_scraper.py --owner OWNER --repo REPO --limit 20 --format json --output releases.json
```

To fetch all releases:
```bash
python github_releases_scraper.py --owner OWNER --repo REPO --all
```

### Arguments

- `--owner`: Repository owner (username or organization) - REQUIRED
- `--repo`: Repository name - REQUIRED
- `--limit`: Maximum number of releases to fetch (default: 10)
- `--all`: Fetch all releases (ignores limit)
- `--format`: Output format: "table", "json", or "csv" (default: table)
- `--output`: Output file for JSON or CSV format (default: {owner}_{repo}_releases.{format})

### Example

```bash
python github_releases_scraper.py --owner microsoft --repo vscode --limit 5
```

This will fetch the 5 most recent releases from the Microsoft VS Code repository and display them in a table format.

To save all releases as CSV:

```bash
python github_releases_scraper.py --owner microsoft --repo vscode --all --format csv --output vscode_releases.csv
```
