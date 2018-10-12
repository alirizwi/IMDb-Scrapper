import mysql.connector, smtplib
import requests, time, datetime
import sys, os, csv
from bs4 import BeautifulSoup
from mysql.connector import Error
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

### Enter the sender's email id and password for authentication
sender = ""                 # Enter sender's email ID
password = ""               # Enter password

# This function scrapes imdb.com and search for the given TV Series with its name and
# then return its new episode/season date, rating and genre.
def scrape_imdb(name):

    # URL for searching on imdb.com using TV Series name.
    base_url = "https://www.imdb.com/find?q="+ name +"&s=tt&exact=true&ref_=fn_tt_ex"

    res = requests.get(base_url)
    soup = BeautifulSoup(res.text, 'html.parser')
    try:
        link = soup.find_all('tr', {'class': 'findResult odd'})
        title = link[0].find('td', {'class': 'result_text'})
    except:
        # If no results found
        ans = "No results found for " + name
        return [ans, "NA", "NA"]

    if "TV Series" in title.getText().strip(" \n\t\r"):
        title_link = link[0].find('a')['href']
        title_url = "https://www.imdb.com" + title_link

        ### Uncomment the next line if getting error 104 connection reset by peer
        # time.sleep(0.01)

        title_res = requests.get(title_url)
        title_soup = BeautifulSoup(title_res.text, 'html.parser')
        try:
            rating = title_soup.find('div', {'class': 'ratingValue'}).getText().strip(" \n\t\r")
        except AttributeError:
            # if rating is not available
            rating = "NA"
        
        try:
            title_wrapper = title_soup.find('div', {'class': 'title_wrapper'}).find_all('a')
            genre = ""
            for i in range(len(title_wrapper)-1):
                genre += title_wrapper[i].getText().strip(" \n\t\r")
                if(i != len(title_wrapper)-2):
                    genre += "; "
        except AttributeError:
            # if genre is not available
            genre = "NA"

        season = title_soup.find('div', {'class': 'seasons-and-year-nav'})
        season_link = season.find('a')['href']
        season_url = "https://www.imdb.com" + season_link

        ### Uncomment the next line if getting error 104 connection reset by peer    
        # time.sleep(0.01)

        season_res = requests.get(season_url)
        season_soup = BeautifulSoup(season_res.text, 'html.parser')
        episodes = season_soup.find('div', {'class': 'list detail eplist'}).find_all('div',  {'class': 'info'})
        episode_dates = []
        now = datetime.datetime.now()
        for episode in episodes:
            ep_date = episode.find('div',  {'class': 'airdate'}).get_text().strip(" \n\t\r")
            if(ep_date):
                episode_dates.append(ep_date)

        ans_date = 0
        ans = ""
        for date in episode_dates:
            if(date.isdigit()):
                ans = "The next season begins in " + date
                ans_date = -1
                break
            else:
                date = date.replace('Jan.', '01').replace('Feb.', '02').replace('Mar.', '03')
                date = date.replace('Apr.', '04').replace('May', '05').replace('Jun.', '06')
                date = date.replace('Jul.', '07').replace('Aug.', '08').replace('Sep.', '09')
                date = date.replace('Oct.', '10').replace('Nov.', '11').replace('Dec.', '12')
                date = datetime.datetime.strptime(date, "%d %m %Y").strftime("%Y-%m-%d")
                date = datetime.datetime.strptime(date, "%Y-%m-%d")
                diff = (date - now).days
                if(diff > 0):
                    ans_date = date.date()
                    break

        if(ans_date == 0):
            ans = "The show has finished streaming all its episodes."
        elif(ans_date != -1):
            ans = "The next episode airs on "+str(ans_date)
        return [ans, rating, genre]

    # If no results found, return default values
    ans = "No results found for " + name
    return [ans, "NA", "NA"]

# This function fetch the data for every tv series given as input and 
# sends the output mail to the email provided by the user.
def fetch_and_email_result(email, tv_series_list):
    result = ""
    filename = 'tvseries'+'.csv'
    with open(filename, 'w') as csvfile:
        filewriter = csv.writer(csvfile, delimiter=',',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        filewriter.writerow(['TV Series Name', 'Rating', 'Genre', 'Status'])

    for tv_series in tv_series_list:
        current_result = ""
        ans = scrape_imdb(tv_series)
        print("TV Series: ",tv_series)
        print(ans)
        print()
        current_result += "Tv series name: " + tv_series
        current_result += "\nStatus: " + ans[0]
        current_result += "\n\n"
        # current_result = {"Tv series name":tv_series, "Status":ans}
        result += current_result
        with open(filename, 'a', newline='') as csvfile:
            filewriter = csv.writer(csvfile, delimiter=',',
                                    quotechar='|', quoting=csv.QUOTE_MINIMAL)
            filewriter.writerow([tv_series, ans[1], ans[2], ans[0]])

    """ Sending the email with the output and attached csv file """
    
    receivers = [email]
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = email
    msg['Subject'] = "TV series info"
    msg.attach(MIMEText(result))
    
    # Attaching the csv file
    attachment = open(filename, "rb")
    part = MIMEBase('application', 'octet-stream')
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
    msg.attach(part)
    try:
        # If the sender's email is not gmail.com, change the smtp server and port in the next line
        smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
        
        smtpObj.set_debuglevel(False)
        smtpObj.ehlo()
        smtpObj.starttls()
        smtpObj.login(sender, password)
        print("Sending mail...")
        try:
            smtpObj.sendmail(sender, receivers, msg.as_string())
        finally:
            print("Mail sent successfully.")
            smtpObj.quit()
        return True
    except smtplib.SMTPException as e:
        print("Exception: ",e)
        return False

# This function inputs the data and stores it in MySQL database
def input_and_store_data():
    while(1):
        email = input("Email address:")
        tv_series = input("TV Series:")
        tv_series_list = tv_series.split(', ')
        tv_series_list = tv_series.split(',')        

        """ Connecting to MySQL database """
        try:
            # Enter your MySQL password to make the connection
            # Input data is stored in database named imdb_database and table named user_data
            conn = mysql.connector.connect(host='localhost',
                                        user='root',
                                        password='galaxyj5')
            # print(conn)
            cursor = conn.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS imdb_database")
            cursor.execute("USE imdb_database")
            cursor.execute('CREATE TABLE IF NOT EXISTS user_data (email VARCHAR(255) NOT NULL, tv_series VARCHAR(255) NOT NULL)')
            add_input = ("INSERT INTO user_data "
                        "(email, tv_series) "
                        "VALUES (%s, %s)")
            args = (email, tv_series)
            cursor.execute(add_input, args)
            conn.commit()
            fetch_and_email_result(email, tv_series_list)

        except Error as error:
            print(error)
    
        finally:
            cursor.close()
            conn.close()            

def main():
    input_and_store_data()

if __name__ == '__main__':
    main()
