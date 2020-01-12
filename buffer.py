#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2018 Andy Stewart
#
# Author:     Andy Stewart <lazycat.manatee@gmail.com>
# Maintainer: Andy Stewart <lazycat.manatee@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QColor
from PyQt5.QtWebEngineWidgets import QWebEngineSettings
from core.browser import BrowserBuffer
from core.utils import touch
import os

class AppBuffer(BrowserBuffer):
    def __init__(self, buffer_id, url, config_dir, arguments, emacs_var_dict):
        BrowserBuffer.__init__(self, buffer_id, url, config_dir, arguments, emacs_var_dict, False, QColor(255, 255, 255, 255))

        self.config_dir = config_dir

        # When arguments is "temp_html_file", browser will load content of html file, then delete temp file.
        # Usually use for render html mail.
        if arguments == "temp_html_file":
            with open(url, "r") as html_file:
                self.buffer_widget.setHtml(html_file.read())
                if os.path.exists(url):
                    os.remove(url)
        else:
            self.buffer_widget.setUrl(QUrl(url))

        self.history_log_file_path = os.path.join(self.config_dir, "browser", "history", "log.txt")

        self.buffer_widget.titleChanged.connect(self.record_history)
        self.buffer_widget.titleChanged.connect(self.change_title)
        self.buffer_widget.open_url_in_new_tab.connect(self.open_url)
        self.buffer_widget.translate_selected_text.connect(self.translate_text)
        self.buffer_widget.setZoomFactor(float(self.emacs_var_dict["eaf-browser-default-zoom"]))

        settings = QWebEngineSettings.globalSettings()
        try:
            settings.setAttribute(QWebEngineSettings.PluginsEnabled, self.emacs_var_dict["eaf-browser-enable-plugin"] == "true")
            settings.setAttribute(QWebEngineSettings.JavascriptEnabled, self.emacs_var_dict["eaf-browser-enable-javascript"] == "true")
        except Exception:
            pass

    def clear_history(self):
        if os.path.exists(self.history_log_file_path):
            os.remove(self.history_log_file_path)
            self.message_to_emacs.emit("Cleared browsing history.")
        else:
            self.message_to_emacs.emit("There is no browsing history.")

    def record_history(self, title):
        if self.emacs_var_dict["eaf-browser-remember-history"] == "true":
            touch(self.history_log_file_path)
            with open(self.history_log_file_path, "a") as f:
                filtered_url = self.buffer_widget.filter_url(self.buffer_widget.url().toString())
                if title == self.buffer_widget.url().toString():
                    f.write(filtered_url + " " + filtered_url + "\n")
                else:
                    f.write(title + " " + filtered_url + "\n")

            self.remove_duplicate_history()

    def remove_duplicate_history(self):
        lines_seen = set() # holds lines already seen
        with open(self.history_log_file_path, "r") as f:
            lines = f.readlines()

        with open(self.history_log_file_path, "w") as f:
            for line in lines:
                if line not in lines_seen: # not a duplicate
                    f.write(line)
                    lines_seen.add(line)
