# Something in lines of http://stackoverflow.com/questions/348630/how-can-i-download-all-emails-with-attachments-from-gmail
# Make sure you have IMAP enabled in your gmail settings.
# Right now it won't download same file name twice even if their contents are different.

import email
import email.parser
import getpass, imaplib
import os
import sys
import yaml

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

def _handle_part(part, msg_dir, indent="  "):
    maintype = part.get_content_maintype()
    contenttype = part.get_content_type()
    filename = part.get_filename()
    print("{}--> {} {} ({})".format(indent, maintype, contenttype, filename))

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
    elif contenttype in ["multipart/alternative", "multipart/related"]:
        for mp in part.get_payload():
            _handle_part(mp, msg_dir=msg_dir, indent=indent+"  ")
    elif contenttype == "message/delivery-status":
        delivery_status_path = os.path.join(msg_dir, "delivery-status")
        if not os.path.exists(delivery_status_path):
            os.mkdir(delivery_status_path)
        for mp in part.get_payload():
            _handle_part(mp, msg_dir=msg_dir, indent=indent+"  ")
    elif contenttype == "message/rfc822":
        for mp in part.get_payload():
            import ipdb
            ipdb.set_trace()
            _handle_part(mp, msg_dir=msg_dir)
    else:
        raise NotImplementedError("{} {}".format(maintype, contenttype))

def download_attachments(hostname, username, password, search_str):
    imap_session = imaplib.IMAP4_SSL(hostname)
    typ, accountDetails = imap_session.login(username, password)
    if typ != 'OK':
        raise Exception("Couldn't sign in: {}".format(str(typ)))

    if not os.path.exists(ROOT_PATH):
        os.mkdir(ROOT_PATH)

    imap_session.select('inbox')
    typ, data = imap_session.search(None, '(SUBJECT "{}")'.format(search_str))
    if typ != 'OK':
        raise Exception("Error searching inbox: {}".format(str(type)))

    msg_ids = data[0].split()
    print "{} emails found".format(len(msg_ids))

    # Iterating over all emails
    for msg_id in msg_ids:
        typ, message_parts = imap_session.fetch(msg_id, '(RFC822)')
        if typ != 'OK':
            raise Exception("Error fetching email: {}".format(str(typ)))

        email_body = message_parts[0][1]

        msg_header = header_parser.parsestr(email_body)
        msg_uid = msg_header['message-id'][1:-1]

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
                    _handle_part(mp, msg_dir=msg_dir)
            else:
                _handle_part(part, msg_dir=msg_dir)

    imap_session.close()
    imap_session.logout()


if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(__doc__)
    argparser.add_argument('hostname')
    argparser.add_argument('username')
    argparser.add_argument('-s', help="search pattern", default="*")
    argparser.add_argument('-p', help="password", default=None)

    args = argparser.parse_args()

    password = getpass.getpass()
    search_str = args.s

    download_attachments(username=args.username, hostname=args.hostname,
                         password=password, search_str=search_str)
