from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from email.mime.multipart import MIMEMultipart
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from collections import defaultdict
from datetime import datetime
from bs4 import BeautifulSoup
import argparse
import pickle
import base64
import os


PAPERS_PATH = 'papers.pkl'


def authenticate_google_api():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens.
    if os.path.exists('token.pkl'):
        with open('token.pkl', 'rb') as token:
            creds = pickle.load(token)

    # If there are no valid credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            scopes = ['https://www.googleapis.com/auth/gmail.modify',
                      'https://www.googleapis.com/auth/gmail.send']
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', scopes)
            creds = flow.run_local_server(port=0)
        # Save the credentials for subsequent runs
        with open('token.pkl', 'wb') as token:
            pickle.dump(creds, token)

    return creds


def get_label_id(service, label_name):
    response = service.users().labels().list(userId='me').execute()
    labels = response.get('labels', [])
    for label in labels:
        if label['name'] == label_name:
            return label['id']

    return None


def get_msgs(service, label_ids, filter_name, filter_match):
    results = service.users().messages().list(userId='me', labelIds=label_ids).execute()
    messages = results.get('messages', [])

    matching_msgs = []
    for msg in messages:
        txt = service.users().messages().get(userId='me', id=msg['id']).execute()
        payload = txt['payload']
        headers = payload['headers']
        filter_value = next(header['value'] for header in headers if header['name'] == filter_name)
        if filter_match in filter_value:
            matching_msgs.append(msg)

    return matching_msgs


def remove_label_from_message(service, user_id, message_id, label_id):
    body = {
        'removeLabelIds': [label_id]
    }
    message = service.users().messages().modify(userId=user_id, id=message_id, body=body).execute()
    return message


def get_html_body(service, msg):
    txt = service.users().messages().get(userId='me', id=msg['id']).execute()

    html_content_64 = txt['payload']['body']['data']
    html_content = base64.urlsafe_b64decode(html_content_64).decode('utf-8')

    return html_content


def process_msgs(service, msgs, papers):
    duplicates = defaultdict(int)

    for msg in msgs:
        msg_html = get_html_body(service, msg)
        soup = BeautifulSoup(msg_html, 'html.parser')
        links = soup.select('body > div > h3 > a')

        for link in links:
            paper_title = link.text
            parent = link.parent
            paper_html = (parent.prettify() + parent.next_sibling.prettify()  # type: ignore
                          + parent.next_sibling.next_sibling.prettify())  # type: ignore  # noqa

            if paper_title not in papers:
                papers[paper_title] = paper_html
            else:
                duplicates[paper_title] += 1


def load_or_create_dictionary(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            dictionary = pickle.load(file)
            print('Dictionary loaded successfully.')
    else:
        dictionary = {}
        print('New dictionary created.')

    return dictionary


def create_message(sender, to, subject, html_content):
    message = MIMEMultipart('alternative')
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject

    # Add HTML part
    part2 = MIMEText(html_content, 'html')
    message.attach(part2)

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw_message}


def send_message(service, user_id, message):
    message = service.users().messages().send(userId=user_id, body=message).execute()
    print('Message Id: %s' % message['id'])
    return message


# TODO: not sure ever got the send permission but it's working anyway
def main(email: str):
    papers = load_or_create_dictionary(PAPERS_PATH)

    credentials = authenticate_google_api()
    service = build('gmail', 'v1', credentials=credentials)
    papers_label_id = get_label_id(service, 'Google Scholar')  # 'Label_4071262017048438834'
    unread_label_id = 'UNREAD'
    msgs = get_msgs(service, [papers_label_id, unread_label_id], 'From', 'scholaralerts-noreply')

    # TODO: something better than this and the set difference, below
    papers_old = papers.copy()

    process_msgs(service, msgs, papers)
    for msg in msgs:
        # TODO: should this be done in process msgs in case of failure
        remove_label_from_message(service, 'me', msg['id'], 'UNREAD')

    difference_dict = {key: papers[key] for key in set(papers.keys()) - set(papers_old.keys())}

    if difference_dict:
        formatted_date = datetime.now().strftime('%a %b %d')
        text = '<br/>'.join([value for value in difference_dict.values()])
        aggregate_msg = create_message(EMAIL_ADDR, EMAIL_ADDR, f'Google Scholar Updates {formatted_date}', f'<html><body>{text}</body></html>')
        send_message(service, 'me', aggregate_msg)

    with open(PAPERS_PATH, 'wb') as file:
        pickle.dump(papers, file)
        print('Dictionary saved successfully.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('email', type=str, help='The email address to use.')
    args = parser.parse_args()
    main(args.email)
