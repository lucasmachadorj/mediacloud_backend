#!/usr/bin/env python
#-*- coding:utf-8 -*-
u"""
Created on 26/09/13
by fccoelho
license: GPL V3 or Later
"""

__docformat__ = 'restructuredtext en'


import feedfinder
import urlscanner
import argparse


def main(urls, depth):
    with open(urls[0]) as f:
        for u in f:
            print "scanning {} with depth {}".format(u, depth)
            u2 = urlscanner.url_scanner(u.strip(), depth)
            for U in u2:
                print "searching for feeds in: ", U
                feeds = feedfinder.feeds(U.strip())
                print "found %s feeds" % len(feeds)
                if feeds:
                    print feeds
                    feedfinder.store_feeds(feeds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Search for feeds on a set of web pages (urls)')
    parser.add_argument('file', metavar='file', nargs=1, help='file with one or more urls to check (one per line)')
    parser.add_argument('-d', '--depth', type=int, default=2, help='Depth of the search, from the initial url')

    args = parser.parse_args()
    # print args.file
    main(args.file, args.depth)

