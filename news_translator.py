import openai
from html import escape
from bs4 import BeautifulSoup
import requests
import feedparser
import time
import os

# Your OpenAI API key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Set the OpenAI API key
openai.api_key = OPENAI_API_KEY

# News RSS feeds
NEWS_FEEDS = {
    "Japan": [
        "https://www3.nhk.or.jp/rss/news/cat0.xml",
        "https://www.japantimes.co.jp/feed/",
        "https://english.kyodonews.net/rss/news",
        # "https://www.asahi.com/rss/asahi/newsheadlines.rdf",
        "https://www.yomiuri.co.jp/feed/rss/",
        # "https://mainichi.jp/rss/etc/mainichi-flash.rss",
        "https://www.sankei.com/rss/news/flash.xml",
        "https://www.tokyo-np.co.jp/topics/rss.rdf",
        "https://www.nikkansports.com/rss/news/flash-tp0.xml",
        "https://www.fnn.jp/rss/fnn-flash.rdf",
    ],
    "USA": [
        "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        "https://rss.cnn.com/rss/cnn_topstories.rss",
        "https://feeds.npr.org/1001/rss.xml",
        "https://www.aljazeera.com/xml/rss/all.xml",
        # "https://www.reuters.com/rssFeed/topNews",
        # "https://apnews.com/rss/apf-topnews",
        # "https://www.buzzfeed.com/world.xml",
        # "https://www.washingtonpost.com/rss-feeds/2014/08/04/ab6f109a-1bf7-11e4-ae54-0cfe1f974f8a_story.html",
        # "https://www.bbc.co.uk/news/world/us_and_canada/rss.xml",
        # "https://feeds.foxnews.com/foxnews/latest",
    ],
    "Europe": [
        # "https://www.theguardian.com/world/rss",
        # "https://www.bbc.co.uk/news/world/europe/rss.xml",
        "https://www.france24.com/en/rss",
        "https://www.dw.com/overlay/rss_en_all",
        # "https://www.euronews.com/rss",
        "https://www.repubblica.it/rss/homepage/rss2.0.xml",
        "https://elpais.com/rss/elpais/portada.xml",
        # "https://www.tagesschau.de/xml/rss2",
        # "https://www.thelocal.fr/rss",
        # "https://www.rtlnieuws.nl/service/rss/nieuws/index.xml",
    ],
}

# API request cost and limit
API_COST_PER_REQUEST = 0.05  # Cost per request in USD
API_COST_LIMIT = 5.00  # Maximum cost limit in USD
API_REQUEST_LIMIT = API_COST_LIMIT / \
    API_COST_PER_REQUEST  # Maximum number of requests
NEWS_PER_FEED = 1  # Maximum number of news items per feed
MAX_PARAGRAPHS = 3  # Maximum number of paragraphs to include in the translation


def translate_text(text, target_language="zh-TW"):
    """Translate text to target language using GPT-3."""
    while True:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-16k-0613",
                messages=[
                    {"role": "user", "content": f"Translate the following English text to {target_language}:\n{text}"},
                ],
            )
            return response.choices[0].message['content'].strip()
        except openai.error.ServiceUnavailableError:
            print("OpenAI server is busy. Retrying in 5 seconds...")
            time.sleep(5)


def fetch_news():
    """Fetch news from RSS feeds and translate to Traditional Chinese."""
    request_counter = 0
    html_output = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <title>News Template</title>
            <meta content="width=device-width, initial-scale=1.0" name="viewport">
            <meta content="News Template" name="keywords">
            <meta content="News Template" name="description">

            <!-- Favicon -->
            <link href="img/favicon.ico" rel="icon">

            <!-- Google Fonts -->
            <link href="https://fonts.googleapis.com/css?family=Montserrat:400,600&display=swap" rel="stylesheet"> 

            <!-- CSS Libraries -->
            <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.10.0/css/all.min.css" rel="stylesheet">
            <link href="lib/slick/slick.css" rel="stylesheet">
            <link href="lib/slick/slick-theme.css" rel="stylesheet">

            <!-- Template Stylesheet -->
            <link href="css/style.css" rel="stylesheet">
        </head>

        <body>
            <!-- Single News Start-->
            <div class="single-news">
                <div class="container">
                    <div class="row">
                        <div class="col-lg-8">
                            <div class="sn-container">
                                <!-- News content will be generated here -->
                            </div>
                        </div>

                        <div class="col-lg-4">
                            <div class="sidebar">
                                <!-- Sidebar content will be generated here -->
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <!-- Single News End-->
        </body>
        </html>
    """

    for country, feeds in NEWS_FEEDS.items():
        html_output += f"<h1 style='font-size: 24px; margin-top: 30px;'>Fetching news from {country}...</h1>"
        for feed in feeds:
            print(f"Fetching news from {feed}...")
            d = feedparser.parse(feed)
            for entry in d.entries[:NEWS_PER_FEED]:
                if request_counter >= API_REQUEST_LIMIT:
                    print(
                        f"Reached the request limit of {API_REQUEST_LIMIT}. Stopping further requests.")
                    break
                translated_title = translate_text(entry.title)
                html_output += f"<h2 style='font-size: 20px; margin-top: 20px;'><a href='{entry.link}' style='text-decoration: none; color: #0053a0;'>{escape(translated_title)}</a></h2>"
                if 'description' in entry:
                    paragraphs = entry.description.split("\n\n")[
                        :MAX_PARAGRAPHS]
                    full_content = " ".join(paragraphs)
                    try:
                        # 檢查是否以「Translated summary:」開頭
                        if full_content.startswith("Translated summary:"):
                            continue  # 跳過這個項目
                        html_output += f"<p>{translate_text(full_content)}</p>"
                        request_counter += 1
                    except openai.error.ServiceUnavailableError:
                        print("OpenAI server is busy. Retrying in 5 seconds...")
                        time.sleep(5)
                        # 檢查是否以「Translated summary:」開頭
                        if full_content.startswith("Translated summary:"):
                            continue  # 跳過這個項目
                        html_output += f"<p>{translate_text(full_content)}</p>"
                        request_counter += 1

    html_output += "</body></html>"

    with open("news_output.html", "w") as f:
        f.write(html_output)


def beautify_html():
    """Load and beautify the generated HTML file."""
    with open("news_output.html", "r") as f:
        html_content = f.read()
        soup = BeautifulSoup(html_content, "html.parser")

        # 在這裡可以使用 BeautifulSoup 的功能修改和美化 HTML 的結構和樣式

    with open("news_output.html", "w") as f:
        f.write(soup.prettify())


if __name__ == "__main__":
    fetch_news()
    beautify_html()
