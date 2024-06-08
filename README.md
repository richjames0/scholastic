# scholastic
Google Scholar aggregator and deduper

## Overview
Google Scholar is fantastic but has two behaviours that I don't prefer:
- It sends a different email for each author to whom one has subscribed
- It sends duplicates both within and across authors

This means I get a bunch of separate emails at the end of each day and I have to mentally dedupe based on what I recall seeing before.

This tool addresses both of these things - when it runs it will look at all unread scholar emails, mark them as read and send a new, aggregated, deduped email.

## Requirements

- You must be using Gmail
- You're going to have to set up a GCP account (easy)
- We'll be charged per API call I guess

## Usage

### Set up GCP project

1.	Create a Google Cloud Project: Go to the Google Cloud Console (https://console.cloud.google.com/) and create a new project.
2.	Enable the Gmail API: In the Cloud Console, navigate to “APIs & Services” > “Dashboard”, and enable the Gmail API for your project.
3.	Create Credentials:
	- Go to “APIs & Services” > “Credentials”.
	- Click “Create Credentials” and choose “OAuth client ID”.
	- Configure the consent screen if prompted.
	- For application type, select “Desktop app”.
	- Once created, download the client configuration (a JSON file) by clicking “Download JSON”.

### Install GCP libraries
- pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2

### Install scholastic
- pip install -e .

### Run scholastic

python -m scholastic.scholastic <YOUR_GMAIL_ADDR>
