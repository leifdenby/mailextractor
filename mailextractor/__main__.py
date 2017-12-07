"""
Email download utility which connects to IMAP server and writes email content
to files, including attachments and Amazon SES delivery information

Copyright 2017 Leif Denby, GPL-3 License
"""
import getpass

from . import mailextractor


if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(__doc__)
    argparser.add_argument('hostname')
    argparser.add_argument('username')
    argparser.add_argument('-l', help="list IMAP folders", action="store_true")
    argparser.add_argument('-s', help="subject search pattern", default="")
    argparser.add_argument('-b', help="body search pattern", default="*")
    argparser.add_argument('-p', help="password", default=None)
    argparser.add_argument('-f', help="IMAP folder", default="INBOX")
    argparser.add_argument('--debug', help="Show debug info", default=False)

    args = argparser.parse_args()

    if args.p is not None:
        passord = args.p
    else:
        password = getpass.getpass()

    search_subject = args.s
    search_body = args.b

    imap_session = mailextractor.create_imap_session(username=args.username,
                                                     hostname=args.hostname,
                                                     password=password)

    if args.l:
        mailextractor.list_available_folders(imap_session)
    else:
        mailextractor.download_attachments(imap_session=imap_session,
                                           search_subject=search_subject,
                                           search_body=search_body,
                                           imap_folder=args.f,
                                           debug=args.debug)
