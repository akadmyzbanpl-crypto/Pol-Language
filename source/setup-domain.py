#!/usr/bin/env python3
"""Prepare initial domain settings locally; does not deploy or modify DNS."""
import argparse
import json
import re
import secrets
from pathlib import Path
from build import build

parser=argparse.ArgumentParser(description='Prepare domain configuration; run once for a new installation.')
parser.add_argument('public_domain',help='Example: example.com')
parser.add_argument('panel_domain',help='Example: panel.example.com')
args=parser.parse_args()
pattern=re.compile(r'(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z](?:[a-z0-9-]{0,61}[a-z0-9])?$',re.I)
if not all(pattern.fullmatch(x) for x in (args.public_domain,args.panel_domain)):
    parser.error('Use hostnames only, without https://, paths or ports. Use punycode for international domains.')
if args.public_domain.lower()==args.panel_domain.lower():
    parser.error('The public site and panel must have different hostnames.')
root=Path(__file__).resolve().parent.parent
env=root/'deploy/.env'
if env.exists():
    parser.error('deploy/.env already exists. Edit existing configuration manually; no secret or file was overwritten.')
text=(root/'deploy/.env.example').read_text()
text=text.replace('panel.example.com',args.panel_domain.lower()).replace('PUBLIC_DOMAIN=example.com','PUBLIC_DOMAIN='+args.public_domain.lower())
text=text.replace('POL_SITE_ORIGIN=https://example.com','POL_SITE_ORIGIN=https://'+args.public_domain.lower())
text=text.replace('REPLACE_WITH_A_RANDOM_SECRET_AT_LEAST_50_CHARACTERS',secrets.token_urlsafe(64))
with env.open('x') as file:
    file.write(text)
try:
    env.chmod(0o600)
except OSError:
    pass
path=root/'source/site-config.json'
config=json.loads(path.read_text())
config['backendOrigin']='https://'+args.panel_domain.lower()
path.write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n')
build()
print('Domain configuration prepared. No DNS changes or deployment were performed. Keep deploy/.env private.')
