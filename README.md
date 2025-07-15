# GTYSermons Downloader

A Python tool for downloading and organizing sermons from [Grace to You](https://www.gty.org/sermons/archive?tab=scripture) by book of the Bible, including sermon metadata and MP3s.

---

## 🚀 Features

- 🔍 Navigates the GTY sermon archive by Scripture references
- ⬇️ Downloads MP3 sermons with structured filenames
- 🗂️ Automatically organizes sermons into folders by Bible book (e.g., `01_Genesis`)
- 💬 Extracts and formats: sermon title, date, passage, and sermon code
- 🧠 Uses Selenium + BeautifulSoup for reliable scraping
- 🧾 Logs every step with [Loguru](https://github.com/Delgan/loguru)

---

## 📦 Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/gtysermons.git
cd gtysermons

# Set up the environment (recommended)
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -e .
```

---

## 🧰 Requirements

- Python 3.9+
- [Firefox browser](https://www.mozilla.org/en-US/firefox/new/)
- [Geckodriver](https://github.com/mozilla/geckodriver) (included as `geckodriver.exe`, or download your own)

---

## 🧪 Usage

Run via command-line using the `gtysermons` CLI:

```bash
# Download all sermons from all books
python -m gtysermons.scripts --all

# Download sermons from a specific book (e.g., Genesis)
python -m gtysermons.scripts --book Genesis
```

📂 Output structure:
```
sermons/
├── 00_Genesis/
│   ├── 1999-03-21 - Creation - Genesis 1-1 - 90-208.mp3
│   └── ...
├── 01_Exodus/
│   └── ...
```

---

## 🧱 File Structure

```
src/gtysermons/
│
├── sermon_downloader.py   # Core scraping & download logic
├── scripts.py             # CLI interface using Click
└── __init__.py
```

---

## 📝 License

This project is licensed under the MIT License, with additional Copyright Policy from Grace To You. See `LICENSE` for details.

---

## 🙏 Credits

Sermons provided by [Grace to You](https://www.gty.org/), the Bible-teaching ministry of John MacArthur.

This tool is independently developed and not affiliated with GTY.org.

---

## 🤝 Contributing

Feel free to open issues or PRs. Suggestions and improvements are welcome!
