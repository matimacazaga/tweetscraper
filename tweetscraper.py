from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import time
import datetime
import typing
import pickle

NUM_MAP = {'K':1000, 'M':1000000, 'B':1000000000}


def parse_date(str_date:str)->datetime.datetime:
    """
    Convert date from Twitter format (e.g.: Aug 9, 2014)
    
    Parameters
    ----------
    str_date: Date in Twitter format.
    
    Return
    ------
    Date as datetime object.
    """
    return datetime.datetime.strptime(str_date, '%b %d, %Y')


def convert_str_to_number(x:str)->int:
    """
    Convert string to number, replacing 'K', 'M' or 'B' if necessary.
    
    """
    total_stars = 0
    if x.isdigit():
        total_stars = int(x)
    else:
        if len(x) > 1:
            total_stars = float(x[:-1]) * NUM_MAP.get(x[-1], 1)
    return int(total_stars)


def get_data_from_tweet(tweet)->dict:
    
    tweet_data = {}
    
    tweet_split = tweet.text.split('\n')
    
    #tweet['text'] = tweet_split[4] if len(tweet_split) >= 8 else ''

    text = tweet.find_elements_by_css_selector('div[class="css-1dbjc4n"]')[2].text
    
    tweet_data['text'] = text
    
    tweet_data['date'] = parse_date(tweet.find_element_by_tag_name('time').text)
    
    tweet_data['favs'] = convert_str_to_number(
        tweet.find_element_by_css_selector('div[data-testid="like"]').text
    )
    
    tweet_data['retweets'] = convert_str_to_number(
        tweet.find_element_by_css_selector('div[data-testid="retweet"]').text
    )
    
    return tweet_data


def find_tweets(driver):
    
    tweets = []
    
    keep_scrolling = True
    
    for t in driver.find_elements_by_css_selector('div[data-testid="tweet"]'):
        
        tweet = get_data_from_tweet(t)
        
        tweets.append(tweet)
            
    return tweets


def get_tweets(usernames:typing.List[str], start_date:datetime.datetime, end_date:datetime.datetime, scroll_pause_time:float=1., save:bool=False) -> dict:
    """
    Get tweets using the 'advanced_search' function of Twitter.
    
    Parameters
    ----------
    usernames: List of twitter usernames to search for.
    start_date: Start date.
    end_date: Last date.
    scroll_pause_time: Time to sleep between each scroll. Increase in case no tweet is found.
    
    Return
    ------
    tweets: Dictionary with tweets information for each username in usernames.
    """
    tweets = {username: [] for username in usernames}
    
    op = webdriver.ChromeOptions()
    
    op.add_argument('headless')
    
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=op)
    
    for username in usernames:
        
        print(f'Scraping tweets for {username}')
        
        url = f'https://twitter.com/search?q=(from%3A{username})%20until%3A{end_date.strftime("%Y-%m-%d")}%20since%3A{start_date.strftime("%Y-%m-%d")}&src=typed_query&f=live'
        
        driver.get(url)
        
        time.sleep(scroll_pause_time)
        
        tweets[username].extend(find_tweets(driver))
        
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # Scroll down to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait to load page
            time.sleep(scroll_pause_time)

            tweets[username].extend(find_tweets(driver))
            
            print(f'----Found {len(tweets[username])} tweets', end='\r')

            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                break

            last_height = new_height
        
        print('\n')
    
    driver.quit()
    
    if save:
        
        with open('tweets.pickle', 'wb') as fp:
            pickle.dump(tweets, fp)
        
    return tweets