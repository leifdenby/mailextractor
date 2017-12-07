# IMAP email extraction utility

This simple utility allows you to download email content (including
attachments) from an IMAP server.

Emails are downloaded to `emails/{email-uid}/` with header information added to
`emails/{email-uid}/headers.yaml` and attachments to
`emails/{email-uid}/attachments`.

install:

```
python setup.py install
```

usage:

    > python -m mailextractor imap.gmail.com your.user@gmail.com

doc:
```
Email download utility which connects to IMAP server and writes email
content to files, including attachments and Amazon SES delivery information

Copyright 2017 Leif Denby, GPL-3 License

       [-h] [-l] [-s S] [-b B] [-p P] [-f F] [--debug DEBUG] hostname username

positional arguments:
  hostname
  username

optional arguments:
  -h, --help     show this help message and exit
  -l             list IMAP folders
  -s S           subject search pattern
  -b B           body search pattern
  -p P           password
  -f F           IMAP folder
  --debug DEBUG  Show debug info
```
