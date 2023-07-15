import os
import time
import feedparser
import openai
from html import escape
from jinja2 import Environment, FileSystemLoader

# Your OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Ensure API key is present
if not OPENAI_API_KEY:
    raise ValueError(
        "Missing OpenAI API key. Please set it as an environment variable.")

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
    news_data = {}
    request_counter = 0

    for country, feeds in NEWS_FEEDS.items():
        news_list = []
        for feed in feeds:
            print(f"Fetching news from {feed}...")
            try:
                d = feedparser.parse(feed)
            except Exception as e:
                print(f"Error parsing feed {feed}: {e}")
                continue

            for entry in d.entries[:NEWS_PER_FEED]:
                news_item = {
                    'link': entry.link,
                    'title': escape(entry.title),
                }

                if request_counter < API_REQUEST_LIMIT and 'description' in entry:
                    paragraphs = entry.description.split("\n\n")[
                        :MAX_PARAGRAPHS]
                    full_content = " ".join(paragraphs)

                    # 檢查是否以「Translated summary:」開頭
                    if not full_content.startswith("Translated summary:"):
                        news_item['description'] = translate_text(full_content)
                        request_counter += 1
                    else:
                        news_item['description'] = full_content
                else:
                    print(
                        f"Reached the request limit of {API_REQUEST_LIMIT}. Skipping further translation requests but continuing to fetch news.")
                    if 'description' in entry:
                        paragraphs = entry.description.split("\n\n")[
                            :MAX_PARAGRAPHS]
                        news_item['description'] = " ".join(paragraphs)
                news_list.append(news_item)

        news_data[country] = news_list

    return news_data


def generate_html(news_data):
    """Generate HTML output using a Jinja2 template."""
    file_loader = FileSystemLoader('.')
    env = Environment(loader=file_loader)

    template = env.get_template('news_template.html')

    output = template.render(news=news_data)

    with open("news_output.html", "w") as f:
        f.write(output)


if __name__ == "__main__":
    news_data = fetch_news()
    generate_html(news_data)
