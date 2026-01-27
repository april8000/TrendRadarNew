#!/usr/bin/env python3
import requests
import os

token = os.environ.get('GITHUB_TOKEN')
if not token:
    print('Please set GitHub Token first.')
    print('Run in PowerShell: $env:GITHUB_TOKEN="your_token"')
    exit(1)

headers = {
    'Authorization': f'token {token}',
    'Accept': 'application/vnd.github.v3+json'
}
data = {
    'name': 'trendRadarbrand',
    'description': 'TrendRadar merge test repository',
    'public': True
}
response = requests.post('https://api.github.com/user/repos', headers=headers, json=data)
print(f'Status: {response.status_code}')
if response.status_code == 201:
    print('Repository created successfully!')
    print(f'URL: {response.json().get("html_url")}')
else:
    print(response.text)

