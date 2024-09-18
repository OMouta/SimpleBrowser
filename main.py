import sys
import os
import json
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLineEdit, QPushButton, QHBoxLayout, QDialog, QListWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineSettings
from PyQt5.QtGui import QIcon

user_data_folder = 'browserdata/user'
assets_folder = 'browserdata/assets'
pages_folder = 'browserdata/pages'

bookmarks_storage = user_data_folder + '/bookmarks.json'
history_storage = os.path.join(user_data_folder, '/history.json')

app_icon = assets_folder + '/icon.png'

class EmbeddedBrowserApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Browser")
        self.setWindowIcon(QIcon(app_icon))
        self.setGeometry(100, 100, 800, 600)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tab_widget)
        self.add_tab("file:///" + pages_folder + "/newtab.html")

        new_tab_button = QPushButton("+")
        new_tab_button.clicked.connect(self.add_new_tab)
        self.tab_widget.setCornerWidget(new_tab_button, Qt.TopRightCorner)

        self.bookmarks = self.load_bookmarks()
        self.history = self.load_history()

    def add_new_tab(self):
        self.add_tab("file:///" + pages_folder + "/newtab.html")

    def add_tab(self, url: str): 
        tab_widget = self.create_tab_widget(url)
        self.tab_widget.addTab(tab_widget, "Home")

    def create_tab_widget(self, url: str) -> QWidget:
        browser = QWebEngineView()
        browser.load(QUrl(url))
        browser.loadFinished.connect(self.update_ui)
        browser.urlChanged.connect(self.update_url_bar)
        browser.page().windowCloseRequested.connect(self.close_tab)
        
        QWebEnginePage.moveToThread(browser.page(), browser.page().thread())

        url_bar = QLineEdit()
        url_bar.returnPressed.connect(self.load_url)

        bookmark_button = QPushButton("Bookmark")
        bookmark_button.clicked.connect(lambda: self.add_bookmark(browser.url().toString()))

        history_button = QPushButton("History")
        history_button.clicked.connect(self.show_history)

        navigation_layout = QHBoxLayout()
        navigation_layout.addWidget(self.create_navigation_button("<", browser.back))
        navigation_layout.addWidget(self.create_navigation_button(">", browser.forward))
        navigation_layout.addWidget(self.create_navigation_button("Reload", browser.reload))
        navigation_layout.addWidget(url_bar)
        navigation_layout.addWidget(bookmark_button)
        navigation_layout.addWidget(history_button)

        layout = QVBoxLayout()
        layout.addLayout(navigation_layout)
        layout.addWidget(browser)

        tab_widget = QWidget()
        tab_widget.setLayout(layout)

        browser.url_bar = url_bar
        return tab_widget

    def create_navigation_button(self, text: str, slot) -> QPushButton:
        button = QPushButton(text)
        button.clicked.connect(slot)
        return button

    def load_url(self):
        browser = self.sender().parentWidget().findChild(QWebEngineView)
        
        renames = pages_folder + '/renames.json'
        if os.path.exists(renames):
            with open(renames, "r") as f:
                renames = json.load(f)
                if self.sender().text() in renames:
                    browser.setUrl(QUrl(renames[self.sender().text()]))
                else:
                    browser.setUrl(QUrl(self.sender().text()))

    def update_url_bar(self, url: QUrl):
        browser = self.sender()

        urlstring = url.toString()
        
        renames = pages_folder + '/renames.json'
        if os.path.exists(renames):
            with open(renames, "r") as f:
                renames = json.load(f)
                if urlstring in renames:
                    urlstring = renames[urlstring]

        browser.url_bar.setText(urlstring)
        self.save_history(urlstring)

    def update_ui(self):
        browser = self.sender()
        index = self.tab_widget.indexOf(browser.parentWidget())
        self.tab_widget.setTabText(index, browser.page().title())
        widget = self.tab_widget.widget(index)
        if widget:
            layout = widget.layout()
            if layout:
                item = layout.itemAt(0)
                if item:
                    url_bar = item.widget()
                    if url_bar:
                        url_bar.setText(browser.url().toString())

    def close_tab(self, index: int = None):
        if index is None:
            browser = self.sender()
            index = self.tab_widget.indexOf(browser.parentWidget())
        else:
            browser = self.tab_widget.widget(index).findChild(QWebEngineView)
        browser.close()
        self.tab_widget.removeTab(index)
        if self.tab_widget.count() == 0:
            self.close()

    def add_bookmark(self, url: str):
        self.bookmarks.append({"url": url, "title": ""})
        self.save_bookmarks()

    def load_bookmarks(self):
        try:
            with open(bookmarks_storage, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def save_bookmarks(self):
        with open(bookmarks_storage, "w") as f:
            json.dump(self.bookmarks, f)

    def show_history(self):
        history_dialog = HistoryDialog(self.history)
        history_dialog.exec_()

    def load_history(self):
        try:
            with open(history_storage, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def save_history(self, url: str):
        self.history.append({"url": url, "title": ""})
        #self.save_history_file()

    def save_history_file(self):
        with open(history_storage, "w") as f:
            json.dump(self.history, f)

class HistoryDialog(QDialog):
    def __init__(self, history):
        super().__init__()
        self.setWindowTitle("History")
        self.setGeometry(100, 100, 400, 300)

        self.list_widget = QListWidget()
        for item in history:
            self.list_widget.addItem(item["url"])

        self.load_button = QPushButton("Load")
        self.load_button.clicked.connect(self.load_history_item)

        layout = QVBoxLayout()
        layout.addWidget(self.list_widget)
        layout.addWidget(self.load_button)

        self.setLayout(layout)

    def load_history_item(self):
        item = self.list_widget.currentItem()
        if item:
            url = item.text()
            self.add_tab(url)
            self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(app_icon))
    
    QWebEngineSettings.globalSettings().setAttribute(QWebEngineSettings.PluginsEnabled, False)
    QWebEngineSettings.globalSettings().setAttribute(QWebEngineSettings.JavascriptEnabled, True)
    QWebEngineSettings.globalSettings().setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
    QWebEngineSettings.globalSettings().setAttribute(QWebEngineSettings.ScreenCaptureEnabled, False)
    QWebEngineSettings.globalSettings().setAttribute(QWebEngineSettings.WebGLEnabled, True)
    QWebEngineSettings.globalSettings().setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, True)
    
    os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--use-gl=swiftshader'

    window = EmbeddedBrowserApp()
    window.show()
    sys.exit(app.exec_())