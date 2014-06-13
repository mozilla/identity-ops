#!/usr/bin/env python2.7

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Build a user account map file"""

import json
import ldap # "sudo apt-get install python-ldap" or "sudo yum install python-ldap"
import ConfigParser
import argparse
import os
import sys
import logging

def type_loglevel(level):
    try:
        result = getattr(logging, level.upper())
    except AttributeError:
        raise argparse.ArgumentTypeError("'%s' is not a valid log level. Please use %s" % \
                                         (level, [x for x in logging._levelNames.keys() if isinstance(x, str)]))
    return result

def fix_pubkey(pubkey):
    if not pubkey:
        return None

    pubkey = pubkey.replace('ssh-rsa\r\n', 'ssh-rsa ') #
    pubkey = pubkey.replace('ssh-dss\r\n', 'ssh-dss ')
    pubkey = pubkey.replace('ssh-ecdsa\r\n', 'ssh-ecdsa ')
    pubkey = pubkey.replace('=\r\n', '= ')
    pubkey = pubkey.replace('\r\n', '')
    return pubkey

def main(args):
    try:
        l = ldap.initialize(args.uri)
        l.simple_bind_s(args.bind_user, args.bind_password)
    except ldap.LDAPError, error_message:
        print ("Couldn't connect to %s with bind_dn:pass of %s:%s. %s " % (args.uri, args.bind_use, args.bind_password, error_message))
        raise
    users = all_users(l, args.base_dn, args.teams)

    res = {}
    for user in users:
        res[user['uid']] = {'id': user['uid'],
                            'uid': int(user['uidNumber']),
                            'shell': user['loginShell'],
                            'home': user['homeDirectory'],
                            'ssh_keys': user['sshPublicKey'],
                            'comment': user['cn'],
                            'groups': user['groups']}
    if args.databag:
        for key in res.keys():
            with open(os.path.join(args.databag, "%s.json" % key), 'w') as f:
                f.write(json.dumps(res[key], indent=4, separators=(',', ': ')))
    else:
        if args.output == '-':
            f = sys.stdout
        else:
            f = open(args.output, 'w')
        f.write(json.dumps(res, indent=4, separators=(',', ': ')))

def get_uids(l, teams):
    users = {}
    for team in teams:
      search_result = l.search_s("ou=groups,dc=mozilla", 
                                 ldap.SCOPE_SUBTREE, 
                                 "(cn=%s)" % team, 
                                 ['member'])
      user = search_result[0][1]['member'] if len(search_result) > 0 else []
      users[team] = user
    return users

def all_users(l, base_dn, teams):
  
    def fixrecord(rec):
        for k, val in rec.iteritems():
            if k in FLATTEN_FIELDS:
                rec[k] = val[0]
            if k == "sshPublicKey":
                rec[k] = [pubkey for pubkey in (fix_pubkey(i) for i in val) if pubkey]

        
        return rec

    s = l.search_s(base_dn, 
                   ldap.SCOPE_SUBTREE, 
                   "(objectClass=posixAccount)",
                   attrlist=["sshPublicKey", 
                             "loginShell", 
                             "homeDirectory",
                             "mail", 
                             "uidNumber", 
                             "uid",
                             "cn"]
                   )
    users = {}
    groups = get_uids(l, teams)
    for rec in s:
        users[rec[0]] = fixrecord(rec[1])
        users[rec[0]]['groups'] = [x for x in groups.keys() if rec[0] in groups[x]]
    return [users[x] for x in users.keys() if len(users[x]['groups']) > 0]

if __name__=='__main__':
    FLATTEN_FIELDS = ['cn', 'loginShell', 'homeDirectory', 'mail', 'uidNumber', 'uid']
    
    conf_parser = argparse.ArgumentParser(
        # Turn off help, so we print all options in response to -h
            add_help=False
            )
    conf_parser.add_argument("-c", "--config",
                             help="Specify a configuration file", 
                             default=os.path.expanduser('~/.ldap_access.conf'),
                             metavar="FILE")
    args, remaining_argv = conf_parser.parse_known_args()
    defaults = {
        "uri" : "ldap://ldap.db.scl3.mozilla.com/",
        "bind_user" : "uid=bind-generateusers,ou=logins,dc=mozilla",
        "bind_password" : "DEFAULT PASSWORD",
        "teams" : ["team_identity_dev", "team_services_ops", "team_services_qa", "team_opsec"],
        "base_dn" : "dc=mozilla",
        "output" : '-',
        "databag" : False,
        "loglevel" : "INFO"
        }
    if args.config:
        config = ConfigParser.SafeConfigParser(defaults)
        config.read([args.config])
        defaults = dict(config.items("Defaults"))
    
    for key in defaults.keys():
        if "\n" in defaults[key]:
             defaults[key] = [x.strip() for x in defaults[key].splitlines()]

    # Don't suppress add_help here so it will handle -h
    parser = argparse.ArgumentParser(
        # Inherit options from config_parser
        parents=[conf_parser],
        # print script description with -h/--help
        description=__doc__,
        # Don't mess with format of description
        formatter_class=argparse.RawDescriptionHelpFormatter,
        )
    parser.set_defaults(**defaults)
    parser.add_argument('-u', '--uri', 
                       help="URI to access LDAP")
    parser.add_argument('--bind-user', metavar="DN",
                       help="User to bind to LDAP with")
    parser.add_argument('--bind-password', metavar="PASSWORD",
                       help="Password to bind to LDAP with")
    parser.add_argument('-t', '--teams', 
                       help="Teams to search")
    parser.add_argument('--base-dn', metavar="DN",
                       help="Base DN to search under")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-o', '--output', metavar="FILE",
                       help="File to write output to")
    group.add_argument('-d', '--databag', metavar="DIRECTORY",
                       help="Output in chef-solo databag format to the specified directory")
    parser.add_argument('-l', '--loglevel', type=type_loglevel,
                   help='Log level verbosity')
    args = parser.parse_args(remaining_argv)
    logging.basicConfig(level=args.loglevel)
    
    main(args)
