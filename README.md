# IMDb TV Series Scraper

### Usage:
1. Download the required dependencies using the command:
``` pip3 install -r requirements.txt ```
2. Enter the sender's email id and password in the script for user authentication.
3. Run imdb_script.py using python3.  
``` python3 imdb.py ```  
4. A new file "tvseries.csv" with the output data, rating and genre will be created.

### General Information
1. The script will take email and list of TV Series from user as input.
2. It will then scrape imdb.com and fetch the details of the next episode/season, genre and rating.
3. Email will be sent to the email id provided by the user. The content of email will be name of TV Series and status of the next episode/season and an attached csv file which contains Name of TV Series, its rating, Genre and status of the next episode/season.

### Dependencies
Built using Python version 3.5
1. BeautifulSoup4
2. mysql-connector-python
3. requests
3. smptplib
4. csv
5. email