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

import gettext
import os
import threading

import wx
import wx.lib.scrolledpanel
import yaml

import ikalog.outputs
from ikalog.engine import *
from ikalog.ui.events import *
from ikalog.ui.panel import *
from ikalog.ui import VideoCapture
from ikalog.utils import *

_ = Localization.gettext_translation('IkaUI', fallback=True).gettext

class IkaLogGUI(object):

    def on_next_frame(self, context):
        # This IkaEngine thread a bit, so that GUI thread can process events.
        time.sleep(0.01)

    def on_options_apply_click(self, sender):
        self.engine.call_plugins('on_config_apply', debug=True)
        self.engine.call_plugins('on_config_save_to_context', debug=True)
        self.save_current_config(self.engine.context)

    def on_options_reset_click(self, sender):
        self.engine.call_plugins('on_config_load_from_context', debug=True)
        self.engine.call_plugins('on_config_reset', debug=True)

    def on_options_load_default_click(self, sender):
        r = wx.MessageDialog(
            None,
            _('IkaLog preferences will be reset to default. Continue?'),
            _('Confirm'),
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION
        ).ShowModal()

        if r != wx.ID_YES:
            return

        self.engine.call_plugins('on_config_reset', debug=True)
        self.engine.call_plugins('on_config_save_to_context', debug=True)
        self.save_current_config(self.engine.context)

    # 現在の設定値をYAMLファイルからインポート
    #
    def load_config(self, context, filename='IkaConfig.yaml'):
        try:
            yaml_file = open(filename, 'r')
            self.engine.context['config'] = yaml.load(yaml_file)
            yaml_file.close()
        except:
            pass

    # 現在の設定値をYAMLファイルにエクスポート
    #
    def save_current_config(self, context, filename='IkaConfig.yaml'):
        yaml_file = open(filename, 'w')
        yaml_file.write(yaml.dump(context['config']))
        yaml_file.close

    # パネル切り替え時の処理
    #
    def switch_to_panel(self, activeButton):

        for button in [self.button_preview, self.button_last_result, self.button_options]:
            panel = {
                self.button_preview: self.preview,
                self.button_last_result: self.last_result,
                self.button_options: self.options,
            }[button]

            if button == activeButton:
                button.Disable()
                panel.Show()
                # print('%s is shown' % panel)
            else:
                button.Enable()
                panel.Hide()
                # print('%s is hidden' % panel)

        # リサイズイベントが発生しないと画面レイアウトが正しくならないので
        try:
            # Project Phoenix
            self.layout.Layout()
        except:
            # If it doesn't work... for old wxPython
            w, h = self.frame.GetClientSizeTuple()
            self.frame.SetSizeWH(w, h)

    def on_switch_panel(self, event):
        active_button = event.GetEventObject()
        self.switch_to_panel(active_button)

    def update_enable_button(self):
        color = '#00A000' if self.enable else '#C0C0C0'
        label = _('Stop') if self.enable else _('Start')
        self.button_enable.SetBackgroundColour(color)
        self.button_enable.SetLabel(label)

    def set_enable(self, enable):
        self.enable = enable
        self.engine.pause(not enable)
        self.update_enable_button()

    def on_enable_button_click(self, event):
        self.set_enable(not self.enable)

    def on_close(self, event):
        self.engine.stop()
        while self.engine_thread.is_alive():
            time.sleep(0.5)
        self.frame.Destroy()

    def on_input_file_added(self, event):
        input_file = event.input_file
        if input_file in self._file_list:
            wx.MessageBox(_('Already added.'), _('Error'))
            return
        self._file_list.append(input_file)
        self.engine.put_source_file(event.input_file)

    def on_input_initialized(self, event):
        self.engine.reset_capture()
        # Propagate the event as the top level event.
        wx.PostEvent(self.frame, event)

    def create_buttons_ui(self):
        panel = self.frame
        self.button_enable = wx.Button(panel, wx.ID_ANY, _('Enable'))
        self.button_preview = wx.Button(panel, wx.ID_ANY, _('Preview'))
        self.button_last_result = wx.Button(panel, wx.ID_ANY, _('Last Result'))
        self.button_options = wx.Button(panel, wx.ID_ANY, _('Options'))

        self.buttons_layout = wx.BoxSizer(wx.HORIZONTAL)
        self.buttons_layout.Add(self.button_enable)
        self.buttons_layout.Add(self.button_preview)
        self.buttons_layout.Add(self.button_last_result)
        self.buttons_layout.Add(self.button_options)

        self.button_preview.Bind(wx.EVT_BUTTON, self.on_switch_panel)
        self.button_last_result.Bind(wx.EVT_BUTTON, self.on_switch_panel)
        self.button_options.Bind(wx.EVT_BUTTON, self.on_switch_panel)

    def engine_thread_func(self):
        IkaUtils.dprint('IkaEngine thread started')
        self.engine.run()
        IkaUtils.dprint('IkaEngine thread terminated')

    def create_engine(self):
        self.engine = IkaEngine(keep_alive=True)
        return self.engine

    def start_engine(self):
        self.engine_thread = threading.Thread(target=self.engine_thread_func)
        self.engine_thread.daemon = True
        self.engine_thread.start()

    def init_outputs(self, outputs):
        output_dict = {}
        for output in outputs:
            output_dict[output.__class__] = output

        # Keys for outputs in the main page.
        keys = [
            ikalog.outputs.OBS,
            ikalog.outputs.StatInk,
            ikalog.outputs.Twitter
        ]
        # Keys for outputs combined into the misc tab.
        misc_keys = [
            ikalog.outputs.CSV,
            ikalog.outputs.JSON,
            ikalog.outputs.Screenshot,
            ikalog.outputs.Boyomi,
            ikalog.outputs.Slack,
            ikalog.outputs.WebSocketServer,
            ikalog.outputs.DebugVideoWriter,
        ]
        for key in output_dict.keys():
            if key in misc_keys:
                continue
            if key not in keys:
                keys.append(key)

        # Main tabs
        index = 1
        for key in keys:
            output = output_dict.get(key)
            if not output:
                continue

            output.on_option_tab_create(self.options.notebookOptions)
            self.options.notebookOptions.InsertPage(
                index, output.panel, output.panel_name)
            index += 1

        # Misc tab
        self.misc_panel = wx.lib.scrolledpanel.ScrolledPanel(
            self.options.notebookOptions, wx.ID_ANY, size=(640, 360))
        self.misc_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        default_font = self.misc_panel.GetFont()
        title_font = wx.Font(default_font.GetPointSize(),
                             wx.FONTFAMILY_DEFAULT,
                             wx.FONTSTYLE_NORMAL,
                             wx.FONTWEIGHT_BOLD)

        for key in misc_keys:
            output = output_dict.get(key)
            if not output:
                continue

            output.on_option_tab_create(self.misc_panel)
            title = wx.StaticText(self.misc_panel, wx.ID_ANY, output.panel_name)
            title.SetFont(title_font)
            self.misc_panel_sizer.Add(title)
            self.misc_panel_sizer.Add(
                output.panel, flag=wx.EXPAND | wx.ALL, border=10)
            self.misc_panel_sizer.Add((-1, 25))

        self.misc_panel.SetSizer(self.misc_panel_sizer)
        self.misc_panel.SetupScrolling()

        self.options.notebookOptions.InsertPage(
            index, self.misc_panel, _('Misc.'))


    def __init__(self, capture):
        self.capture = capture
        self.frame = wx.Frame(None, wx.ID_ANY, "IkaLog GUI", size=(700, 500))

        self.layout = wx.BoxSizer(wx.VERTICAL)

        self.create_buttons_ui()
        self.layout.Add(self.buttons_layout)

        self.preview = PreviewPanel(self.frame, size=(640, 420))
        self.preview.Bind(EVT_INPUT_FILE_ADDED, self.on_input_file_added)

        self.last_result = LastResultPanel(self.frame, size=(640, 360))
        self.options = OptionsPanel(self.frame)

        self.capture.on_option_tab_create(self.options.notebookOptions)
        self.options.notebookOptions.InsertPage(
            0, capture.panel, capture.panel_name)
        self.capture.panel.Bind(EVT_INPUT_INITIALIZED,
                                self.on_input_initialized)

        self.layout.Add(self.last_result, flag=wx.EXPAND)
        self.layout.Add(self.preview, flag=wx.EXPAND)
        self.layout.Add(self.options, flag=wx.EXPAND)

        self.frame.SetSizer(self.layout)

        # Frame events
        self.frame.Bind(wx.EVT_CLOSE, self.on_close)
        self.button_enable.Bind(wx.EVT_BUTTON, self.on_enable_button_click)

        # Set event handlers for options tab
        self.options.Bind('optionsApply', self.on_options_apply_click)
        self.options.Bind('optionsReset', self.on_options_reset_click)
        self.options.Bind('optionsLoadDefault',
                          self.on_options_load_default_click)

        self.switch_to_panel(self.button_preview)

        # Video files processed and to be processed.
        self._file_list = []

        # Ready.
        self.frame.Show()
