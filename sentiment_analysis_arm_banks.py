# %%
#importing libraries
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import requests
import csv
import re
import warnings
import cloudscraper
from scrapethat import *
from bs4 import BeautifulSoup

warnings.filterwarnings('ignore')
print('Libraries imported!')

# %%
# bank1 Ardshinbank
mainurl1 = 'https://www.ardshinbank.am/en/news/main'
response = read_cloud(mainurl1)
# getting links 
links = ['https://www.ardshinbank.am' +
         i.find('a')['href'] for i in response.find_all(class_='field-content')
         if i.find('a') is not None][:-5]
print(links)

# %%
# bank2 Ameriabank
mainurl2 = 'https://ameriabank.am/en/media-room'
url2 = 'https://ameriabank.am/en/media-room/pageindex39755/2'
response1 = read_cloud(mainurl2)
response2 = read_cloud(url2)
links2 = [i.find('a')['href'] for i in response1.find_all(class_ = 'list-title')] + \
         [i.find('a')['href'] for i in response2.find_all(class_ = 'list-title')][:-2]
print(links2)

# %%
# bank3 Acbabank
mainurl3 = 'https://www.acba.am/en/news/'
response = read_cloud(mainurl3)
links3 = ['https://www.acba.am/'+ i.find('a')['href'] for i in response.find_all(class_='col-xs-12 col-sm-8')]
print(links3)

# %%
# bank4 Unibank 
mainurl4 = 'https://www.unibank.am/hy/news/'
response = read_cloud(mainurl4)
links4 = ['https://www.unibank.am' +
          i.find('a')['href'] for i in response.find_all(class_ ='list__item__header d-block')][:10]
print(links4)

# %%
# bank5 ID Bank
mainurl5 = 'https://idbank.am/information/about/news/news/'
response = read_cloud(mainurl5)
links5 = ['https://idbank.am' + i.find('a')['href'] for i in response.find_all(class_= 'news-list__item')][:10]
print(links5)


#%%
# Getting all articles from the links
# ardshinbank
def ardshin(link):
    response = read_cloud(link)
    text = response.find(class_= 'text-inf content').text.replace('\n', ' ').replace('\xa0', ' ')
    clean_text = re.sub(r'\s+', ' ', text)
    return clean_text
ardshinen = [ardshin(i) for i in links]

# ameriabank
def ameria(link):
    response = read_cloud(link)
    text = response.find(class_= 'detail-description').text.strip()
    # Replace non-breaking spaces, newlines, and carriage returns with a space
    clean_text = text.replace('\xa0', ' ').replace('\n', ' ').replace('\r', ' ')
    # Remove extra spaces
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text
ameriaen = [ameria(i) for i in links2]

# acba
def acba(link):
    response = read_cloud(link)
    text = response.find(class_='news_inner__text').text.replace('\n',' ').strip()
    return text
acbaen = [acba(i) for i in links3]

# unibank
def unibank(link):
    response = read_cloud(link)
    text = response.find(class_ = 'news__detail').text.replace('\n','').replace('\r','').strip()
    # Replace non-breaking spaces, newlines, and carriage returns with a space
    clean_text = text.replace('\xa0', ' ').replace('\n', ' ').replace('\r', ' ')
    # Remove extra spaces
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text
unibankhy = [unibank(i) for i in links4]

# idbank
def idbank(link):
    response = read_cloud(link)
    text = response.find(class_ = 'info__content').text.strip()
    # Replace non-breaking spaces, newlines, and carriage returns with a space
    clean_text = text.replace('\xa0', ' ').replace('\n', ' ').replace('\r', ' ')
    # Remove extra spaces
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text
idbankhy = [idbank(i) for i in links5]


# %%
import boto3
from botocore.exceptions import ClientError

s3 = boto3.client("s3")
bucket_name = 'your-bucket-name'

try:
    # Attempt to create the bucket
    default_region = s3.meta.region_name
    bucket_configuration = {"LocationConstraint": default_region}
    
    response = s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=bucket_configuration)
    print(f"Bucket '{bucket_name}' created.")
except ClientError as e:
    if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
        print(f"Bucket '{bucket_name}' already exists and is owned by you.")
    else:
        print(f"Failed to create bucket: {e}")




# %%
# Upload files to S3

bucket_name = 'your-bucket-name'

# A dictionary to hold all lists for easier processing
banks_articles = {
    'ardshinen': ardshinen,
    'ameriaen': ameriaen,
    'acbaen': acbaen,
    'unibankhy': unibankhy,
    'idbankhy': idbankhy
}

for bank_name, articles in banks_articles.items():
    for index, article in enumerate(articles, start=1):
        file_name = f'{bank_name}{index}.txt'
        s3.put_object(Bucket=bucket_name, Key=file_name, Body=article)
        print(f'Uploaded {file_name} to {bucket_name}')


# %%
# Tranlate files from S3

translate = boto3.client(service_name='translate', region_name='us-east-1', use_ssl=True)
bucket_name = 'your-bucket-name'

def translate_text_in_chunks(text, source_lang='hy', target_lang='en', chunk_size=5000):
    """
    Translate text in chunks. Each chunk will be less than chunk_size bytes.
    """
    translated_text = ''
    while text:
        # Take a chunk of text to translate
        chunk = text[:chunk_size]
        text = text[chunk_size:]

        # Translate the chunk
        result = translate.translate_text(Text=chunk, SourceLanguageCode=source_lang, TargetLanguageCode=target_lang)
        translated_text += result.get('TranslatedText', '')

    return translated_text

for bank_name in ['unibankhy', 'idbankhy']:
    for index in range(1, 11):
        file_name = f'{bank_name}{index}.txt'
        
        # Get the text from S3
        file_obj = s3.get_object(Bucket=bucket_name, Key=file_name)
        text = file_obj['Body'].read().decode('utf-8')

        # Translate the text in chunks
        translated_text = translate_text_in_chunks(text)

        # Upload the translated text back to S3
        translated_file_name = f'translated_{file_name}'
        s3.put_object(Bucket=bucket_name, Key=translated_file_name, Body=translated_text)
        print(f'Uploaded translated {translated_file_name}')


# %%
# Sentiment Analysis

comprehend = boto3.client(service_name='comprehend', region_name='us-east-1')
s3 = boto3.client('s3')
bucket_name = 'your-bucket-name'

def analyze_sentiment_in_chunks(text):
    """
    Analyze sentiment of the given text in chunks. Each chunk will be less than 4900 bytes.
    """
    chunk_size = 4900  # Slightly less than the AWS Comprehend's limit
    sentiments = []

    # Split the text into chunks
    while text:
        chunk = text[:chunk_size]
        text = text[chunk_size:]

        # Call AWS Comprehend's detect_sentiment
        sentiment = comprehend.detect_sentiment(Text=chunk, LanguageCode='en')
        sentiments.append(sentiment['Sentiment'])

    # Aggregating the sentiments
    most_common_sentiment = max(set(sentiments), key=sentiments.count)
    return most_common_sentiment

# List to hold sentiment analysis results
sentiment_results = []

# Define the bank names for reference
bank_names = {
    'ardshinen': 'Ardshinbank',
    'ameriaen': 'Ameriabank',
    'acbaen': 'Acbabank',
    'unibankhy': 'Unibank',
    'idbankhy': 'ID Bank'
}

for bank_key, bank_name in bank_names.items():
    for index in range(1, 11):
        file_key = f'translated_{bank_key}{index}.txt' if bank_key in ['unibankhy', 'idbankhy'] else f'{bank_key}{index}.txt'
        
        # Get the text from S3
        file_obj = s3.get_object(Bucket=bucket_name, Key=file_key)
        text = file_obj['Body'].read().decode('utf-8')

        # Analyze sentiment in chunks
        sentiment = analyze_sentiment_in_chunks(text)
        sentiment_results.append([index, bank_name, file_key, sentiment])

# Write results to CSV
csv_file_name = 'sentiment_analysis_results.csv'
with open(csv_file_name, 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['#', 'Bank Name', 'Article Name', 'Sentiment'])
    writer.writerows(sentiment_results)

# Upload the CSV to S3
s3.upload_file(Filename=csv_file_name, Bucket=bucket_name, Key=csv_file_name)
print(f"Uploaded '{csv_file_name}' to S3 bucket '{bucket_name}'.")

# %%
# Download the CSV file from S3 to the Codespaces directory
local_file_path = './' + csv_file_name  # Path where you want to save the file
s3.download_file(Bucket=bucket_name, Key=csv_file_name, Filename=local_file_path)
print(f"Downloaded '{csv_file_name}' to the Codespaces directory.")

# %%
# Load your CSV data into a DataFrame
df = pd.read_csv('sentiment_analysis_results.csv')

# Set the aesthetic style of the plots
sns.set(style="whitegrid")

# Visualization 1: Overall Sentiment Distribution
plt.figure(figsize=(8, 8))
df['Sentiment'].value_counts().plot(kind='pie', autopct='%1.1f%%', colors=sns.color_palette('pastel'))
plt.title('Overall Sentiment Distribution', fontsize=16)
plt.ylabel('')
plt.savefig('overall_sentiment_distribution.png', bbox_inches='tight')  # Save the plot as a PNG file

# Visualization 2: Sentiment Distribution for Each Bank
plt.figure(figsize=(12, 8))
sns.countplot(x='Bank Name', hue='Sentiment', data=df, palette='Set2')
plt.title('Sentiment Distribution for Each Bank', fontsize=16)
plt.xlabel('Bank Name', fontsize=12)
plt.ylabel('Number of Articles', fontsize=12)
plt.xticks(rotation=45)
plt.legend(title='Sentiment')
plt.savefig('sentiment_distribution_each_bank.png', bbox_inches='tight')  # Save the plot as a PNG file

plt.show()



