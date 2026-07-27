from newspaper import Article


def extract_news(url):
    """
    Downloads and extracts text from a news article.
    """

    try:
        article = Article(url)

        article.download()
        article.parse()

        return article.title, article.text

    except Exception as e:
        return None, f"Error: {e}"