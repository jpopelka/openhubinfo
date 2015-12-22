#!/usr/bin/python

"""
Copyright (c) 2015 Red Hat, Inc.
All rights reserved.

This software may be modified and distributed under the terms
of the BSD license. See the LICENSE file for details.
"""

import argparse
import json
import os
import requests
import sys
import xmltodict

PROG = 'openhubinfo.py'
DESCRIPTION = 'Print info (json) about an OpenHub (Ohloh) project or account.'
API_KEY_WARNING = "Set OH_API_KEY environment variable to your Ohloh API key. If you don't have " \
                  "one, see https://www.openhub.net/accounts/<your_login>/api_keys/new"


class OpenHubInfo(object):
    def __init__(self, api_key, indent=None):
        """
        :param api_key: Your Ohloh API key.
                        See https://github.com/blackducksoftware/ohloh_api#api-key
        :param indent: if not None then indent the output json
        """
        self.api_key = api_key
        self.indent = indent

    @staticmethod
    def _request(url):
        """
        Connect to OpenHub website and retrieve the data.

        :param url: Ohloh API url
        :return: dict (json)
        """
        r = requests.get(url)
        if r.ok:
            xml_string = r.text or r.content
            # Ohloh API returns XML, convert it to dict (json)
            d = xmltodict.parse(xml_string)
            return d

    def _info_url(self, info_type, info_id):
        # see https://github.com/blackducksoftware/ohloh_api
        if info_type == 'project':
            return "https://www.openhub.net/p/{project_id}.xml?api_key={key}".\
                format(project_id=info_id, key=self.api_key)
        elif info_type == 'account':
            return "https://www.openhub.net/accounts/{account_id}.xml?api_key={key}".\
                format(account_id=info_id, key=self.api_key)
        else:
            raise NotImplementedError('Info type not implemented')

    def _dump_info(self, info_type, info_id):
        url = self._info_url(info_type, info_id)
        info_json = self._request(url)
        json.dump(info_json, sys.stdout, indent=self.indent)

    def dump_project_info(self, project_id):
        return self._dump_info('project', project_id)

    def dump_account_info(self, account_id):
        return self._dump_info('account', account_id)


class CLI(object):
    def __init__(self):
        self.api_key = os.getenv('OH_API_KEY')
        if not self.api_key:
            raise ValueError(API_KEY_WARNING)
        self.parser = argparse.ArgumentParser(prog=PROG,
                                              description=DESCRIPTION,
                                              formatter_class=argparse.HelpFormatter)
        self.parser.add_argument("-i", "--indent", action="store_true",
                                 help='pretty-print output json')
        self.parser.add_argument("-d", "--debug", action="store_true")

        subparsers = self.parser.add_subparsers(help='commands ')

        self.project_parser = subparsers.add_parser(
            'project',
            usage="%s [OPTIONS] project ..." % PROG,
            description='get info about a project'
        )
        self.project_parser.add_argument('project_id',
                                         help="unique id (name) of a project to get info about")
        self.project_parser.set_defaults(func=self.project_info)

        self.account_parser = subparsers.add_parser(
            'account',
            usage="%s [OPTIONS] account ..." % PROG,
            description='get info about an account (user)'
        )
        self.account_parser.add_argument('account_id',
                                         help="unique id (name) of a project to get info about")
        self.account_parser.set_defaults(func=self.account_info)

    def project_info(self, args):
        oh_info = OpenHubInfo(self.api_key, args.indent)
        oh_info.dump_project_info(args.project_id)

    def account_info(self, args):
        oh_info = OpenHubInfo(self.api_key, args.indent)
        oh_info.dump_account_info(args.account_id)

    def run(self):
        args = self.parser.parse_args()
        args.indent = 1 if args.indent else None

        try:
            args.func(args)
        except AttributeError:
            if hasattr(args, 'func'):
                raise
            else:
                self.parser.print_help()
        except KeyboardInterrupt:
            pass
        except Exception as ex:
            if args.debug:
                raise
            else:
                print("exception caught: %r", ex)

if __name__ == '__main__':
    cli = CLI()
    sys.exit(cli.run())
