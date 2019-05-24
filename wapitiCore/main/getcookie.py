#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This file is part of the Wapiti project (http://wapiti.sourceforge.net)
# Copyright (C) 2006-2018 Nicolas Surribas
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
from urllib.parse import urlparse, urlunparse
import argparse

from wapitiCore.net import jsoncookie
from wapitiCore.net.crawler import Crawler
from wapitiCore.language.language import _
from wapitiCore.net.web import Request


def getcookie_main():
    parser = argparse.ArgumentParser(description="Wapiti-getcookie: An utility to grab cookies from a webpage")

    parser.add_argument(
        '-u', '--url',
        help='First page to fetch for cookies',
        required=True
    )

    parser.add_argument(
        '-c', '--cookie',
        help='Cookie file in Wapiti JSON format where cookies will be stored',
        required=True
    )

    parser.add_argument(
        '-p', '--proxy',
        help='Address of the proxy server to use'
    )

    parser.add_argument(
        '-d', '--data',
        help='Data to send to the form with POST'
    )

    args = parser.parse_args()

    parts = urlparse(args.url)
    if not parts.scheme or not parts.netloc or not parts.path:
        print(_("Invalid base URL was specified, please give a complete URL with protocol scheme"
                " and slash after the domain name."))
        exit()

    server = parts.netloc
    base = urlunparse((parts.scheme, parts.netloc, parts.path, '', '', ''))

    crawler = Crawler(base)

    if args.proxy:
        proxy_parts = urlparse(args.proxy)
        if proxy_parts.scheme and proxy_parts.netloc:
            if proxy_parts.scheme.lower() in ("http", "https", "socks"):
                crawler.set_proxy(args.proxy)

    # Open or create the cookie file and delete previous cookies from this server
    jc = jsoncookie.JsonCookie()
    jc.open(args.cookie)
    jc.delete(server)

    page = crawler.get(Request(args.url), follow_redirects=True)

    # A first crawl is sometimes necessary, so let's fetch the webpage
    jc.addcookies(crawler.session_cookies)

    if not args.data:
        # Not data specified, try interactive mode by fetching forms
        forms = []
        for i, form in enumerate(page.iter_forms(autofill=False)):
            if i == 0:
                print('')
                print(_("Choose the form you want to use or enter 'q' to leave :"))
            print("{0}) {1}".format(i, form))
            forms.append(form)

        ok = False
        if forms:
            nchoice = -1
            print('')
            while not ok:
                choice = input(_("Enter a number : "))
                if choice.isdigit():
                    nchoice = int(choice)
                    if len(forms) > nchoice >= 0:
                        ok = True
                elif choice == 'q':
                    break

            if ok:
                form = forms[nchoice]
                print('')
                print(_("Please enter values for the following form: "))
                print(_("url = {0}").format(form.url))

                post_params = form.post_params
                for i, kv in enumerate(post_params):
                    field, value = kv
                    if value:
                        new_value = input(field + " (" + value + ") : ")
                    else:
                        new_value = input("{}: ".format(field))
                    post_params[i] = [field, new_value]

                request = Request(form.url, post_params=post_params)
                crawler.send(request, follow_redirects=True)

                jc.addcookies(crawler.session_cookies)
    else:
        request = Request(args.url, post_params=args.data)
        crawler.send(request, follow_redirects=True)

        jc.addcookies(crawler.session_cookies)

    jc.dump()
    jc.close()


