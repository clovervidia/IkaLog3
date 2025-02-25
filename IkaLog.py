#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  IkaLog
#  ======
#  Copyright (C) 2015 Takeshi HASEGAWA
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#


from ikalog.utils import Localization, IkaUtils
Localization.print_language_settings()

import argparse
import logging
import signal
import sys
import time

from ikalog import inputs
from ikalog.engine import IkaEngine
from ikalog.utils import config_loader
from ikalog.logger import init_logger


logger = logging.getLogger()


def signal_handler(num, frame):
    IkaUtils.dprint('IkaLog: got signal %d' % num)
    if num == 2:
        engine.stop()

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', dest='input', type=str,
                        choices=['DirectShow', 'CVCapture', 'ScreenCapture',
                                 'AVFoundationCapture', 'CVFile'])
    parser.add_argument('--input_file', '-f', dest='input_file', type=str,
                        nargs='*', help='Input video file. '
                        'Other flags can refer this flag as __INPUT_FILE__')
    parser.add_argument('--output_json', '--json',
                        dest='output_json', type=str)
    parser.add_argument('--output_description', '--desc',
                        dest='output_description', type=str)
    parser.add_argument('--statink_payload',
                        dest='statink_payload', type=str,
                        help='Payload file to stat.ink. '
                        'If this is specified, the data is not uploaded.')
    parser.add_argument('--profile', dest='profile', action='store_true',
                        default=False)
    parser.add_argument('--time', '-t', dest='time', type=str)
    parser.add_argument('--time_msec', dest='time_msec', type=int)
    parser.add_argument('--video_id', dest='video_id', type=str)
    parser.add_argument('--keep_alive', action='store_true', default=False,
                        help='Do not exit on EOFError with no next inputs.')
    parser.add_argument('--debug', dest='debug', action='store_true',
                        default=False)

    return vars(parser.parse_args())


def get_pos_msec(args):
    if args['time_msec']:
        return args['time_msec']
    elif args['time']:
        minute, sec = args['time'].split(':')
        return (int(minute) * 60 + int(sec)) * 1000
    else:
        return 0


if __name__ == "__main__":
    init_logger()
    signal.signal(signal.SIGINT, signal_handler)

    args = get_args()
    capture, output_plugins = config_loader.config(args)
    capture.set_pos_msec(get_pos_msec(args))

    keep_alive = args.get('keep_alive') or capture.keep_alive

    engine = IkaEngine(enable_profile=args.get('profile'),
                       keep_alive=keep_alive)
    engine.pause(False)
    engine.set_capture(capture)

    engine.set_plugins(output_plugins)
    for op in output_plugins:
        engine.enable_plugin(op)

    from ikalog.configuration import read_from_file
    read_from_file(engine, 'ikalog.conf.json')

    engine.close_session_at_eof = True
    logger.info('IkaLog: start.')
    engine.run()
    logger.info('bye!')
