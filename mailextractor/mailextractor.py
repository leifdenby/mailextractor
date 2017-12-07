"""
Email download utility which connects to IMAP server and writes email content
to files, including attachments and Amazon SES delivery information

Copyright 2017 Leif Denby, GPL-3 License
"""
from __future__ import print_function

import email
import email.parser
import imaplib
import os
import yaml
import tqdm

ROOT_PATH = "emails"

header_parser = email.parser.HeaderParser()

def _save_attachment(part, path):
    part_filename = part.get_filename()
    file_path = os.path.join(path, "attachments", part_filename)

    if not os.path.exists(os.path.dirname(file_path)):
        os.mkdir(os.path.dirname(file_path))

    if not os.path.isfile(file_path):
        with open(file_path, "wb") as fh:
            fh.write(part.get_payload(decode=True))
            fh.close()

    return file_path

def _handle_part(part, msg_dir, indent="  ", debug=False):
    maintype = part.get_content_maintype()
    contenttype = part.get_content_type()
    filename = part.get_filename()
    if debug:
        print("{}--> {} {} ({})".format(indent, maintype,
                                        contenttype, filename))

    if contenttype == "text/plain":
        n = 0
        found_filename = False
        while not found_filename:
            filename = os.path.join(msg_dir, "body-{}.txt".format(n))
            if not os.path.exists(filename):
                found_filename = True
                with open(filename, "w") as fh:
                    fh.write(part.get_payload())
            n += 1

    elif contenttype == "text/html":
        with open(os.path.join(msg_dir, "body.html"), "w") as fh:
            fh.write(part.get_payload())
    elif maintype in ["application", "image"]:
        _save_attachment(part, msg_dir)
    elif contenttype in ["multipart/alternative", "multipart/related",
                         "multipart/mixed"]:
        for mp in part.get_payload():
            _handle_part(mp, msg_dir=msg_dir, indent=indent+"  ")
    elif contenttype == "message/delivery-status":
        delivery_status_path = os.path.join(msg_dir, "delivery-status")
        if not os.path.exists(delivery_status_path):
            os.mkdir(delivery_status_path)

        n = 0
        for mp in part.get_payload():
            found_filename = False
            while not found_filename:
                filename = os.path.join(delivery_status_path,
                                        "delivery-status-{}.yaml".format(n))
                if not os.path.exists(filename):
                    found_filename = True
                else:
                    n += 1

            mp_header = header_parser.parsestr(str(mp))
            with open(filename, "w") as fh:
                yaml.dump(dict(mp_header.items()), fh,
                          default_flow_style=False)

    elif contenttype == "message/rfc822":
        for mp in part.get_payload():
            _handle_part(mp, msg_dir=msg_dir)
    else:
        raise NotImplementedError("{} {}".format(maintype, contenttype))

def _do_search(imap_session, field, value, debug=False):
    if debug:
        print("Seaching `{}` for `{}`...".format(field, value), end=" ")
    typ, data = imap_session.search(None, '({} "{}")'.format(field, value))
    if typ != 'OK':
        raise Exception("Error searching inbox: {}".format(str(type)))

    email_ids = [int(s) for s in data[0].split()]
    if debug:
        print(len(email_ids))
    return email_ids

def _parse_folder_string(data):
    '''
    parse_mailbox() will extract the three pieces of information from
    the items returned from a call to IMAP4.list(). The initial data
    array looks like:
    [b'(\\HasChildren) "/" NameOfFolder', ...]
    At least on my server. If the folder name has spaces then it will
    be quote delimited.

    from
    http://tech.franzone.blog/2012/11/24/listing-imap-mailboxes-with-python/
    '''
    flags, b, c = data.partition(' ')
    separator, b, name = c.partition(' ')
    return (flags, separator.replace('"', ''), name.replace('"', ''))

def list_available_folders(imap_session):
    resp_status, resp_data = imap_session.list()

    for entry in resp_data:
        flags, _, name = _parse_folder_string(entry)
        print(flags, u"  {}".format(name))

def select_folder(imap_session, folder_name):
    resp_status, resp_mesg = imap_session.select(folder_name)

    if resp_status != "OK":
        print("Available folders:")
        list_available_folders(imap_session)

        raise Exception("Couldn't open IMAP folder `{}`".format(folder_name))

def create_imap_session(hostname, username, password):
    print("Connecting to `{}` as {}...".format(hostname, username), end="")
    imap_session = imaplib.IMAP4_SSL(hostname)
    typ, accountDetails = imap_session.login(username, password)
    if typ != 'OK':
        raise Exception("Couldn't sign in: {}".format(str(typ)))
    print("connected")
    return imap_session

def download_attachments(imap_session, search_subject, search_body,
                         imap_folder="INBOX", debug=False):
    select_folder(imap_session, imap_folder)

    if not os.path.exists(ROOT_PATH):
        os.mkdir(ROOT_PATH)

    msg_ids_0 = _do_search(imap_session, "SUBJECT", search_subject)
    msg_ids_1 = _do_search(imap_session, "BODY", search_body)
    msg_ids = set(msg_ids_0).intersection(msg_ids_1)
    print("{} emails found".format(len(msg_ids)))
    print()

    # Iterating over all emails
    print("Downloading...")
    for msg_id in tqdm.tqdm(msg_ids):
        typ, message_parts = imap_session.fetch(msg_id, '(RFC822)')
        if typ != 'OK':
            raise Exception("Error fetching email: {}".format(str(typ)))

        email_body = message_parts[0][1]

        msg_header = header_parser.parsestr(email_body)
        msg_uid = msg_header['message-id'][1:-1]

        if debug:
            print("uid: {}".format(msg_uid))

        msg_dir = os.path.join(ROOT_PATH, msg_uid)
        if not os.path.exists(msg_dir):
            os.mkdir(msg_dir)

        with open(os.path.join(msg_dir, "headers.yaml"), "w") as fh:
            yaml.dump(dict(msg_header.items()), fh, default_flow_style=False)

        mail = email.message_from_string(email_body)

        for part in mail.walk():
            part_maintype = part.get_content_maintype()
            if part_maintype == 'multipart':
                for mp in part.get_payload():
                    _handle_part(mp, msg_dir=msg_dir, debug=debug)
            else:
                _handle_part(part, msg_dir=msg_dir, debug=debug)

    imap_session.close()
    imap_session.logout()

    print("Downloaded {} emails to {}".format(len(msg_ids), ROOT_PATH))
