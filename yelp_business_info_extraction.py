import requests, bs4, pprint, csv, os
from bs4.element import Comment
emails = [[]]
notfound = True

def GetWebsite(some_url):
    try:
        with requests.Session() as r:
            yelp_link = r.get(some_url)
            yelp_link_soup = bs4.BeautifulSoup(yelp_link.text)
            comp_website = r'http://www.' + yelp_link_soup.find_all(text ='Business website')[0].parent.parent.select('a')[0].text
        r.close()
        return comp_website
    except:
        pass
        return True

def CheckIfTextIsEmail(text):
    #TODO NEED TO CHECK TO SEE IF THIS WILL ACCOUNT FOR TEXTS WITH MULTIPLE @ SYMBOLS
    if '@' in text:
        for j in range(len(text)):
            at_index = str.find(text[j:], '@')
            if '.' in text:
                period_index = str.find(text[j:], '.')
                if period_index > at_index:
                    first_half = True
                    for i in range(0, at_index-1):
                        if not str.isalnum(text[i]):
                            return False
                    if first_half:
                        second_half = True
                        for i in range(period_index, len(text)):
                            if not str.isalnum(text[i]):
                                return False
                    return True
    return False

def GetEmailTextFromLinks(weblinks):
    link_texts=[]
    for link in weblinks:
        link_texts.append(str(link['href']))
    email = GetEmailText(link_texts)
    if not email:
        return email
    with requests.session() as session:
        for link in weblinks:
            sub_webpage = session.get(link)
            sub_webpage_soup = bs4.BeautifulSoup(sub_webpage.text)
            sub_webpage_text = sub_webpage_soup.find_all(text=True)
            email = GetEmailText(sub_webpage_text)
            if not email:
                return email
    session.close()
    return None

def GetEmailText(webtexts):
    '''
    :param webtexts: list of texts on the webpage
    :return: found email address
    '''
    for i, text in enumerate(webtexts, 0):
        if CheckIfTextIsEmail(text):
            return text
        if 'email' in str.lower(text):      # Want to travel up and find parent and see if there is an email link
            parent = text.parent
            for i in range(5):
                try:
                    if CheckIfTextIsEmail(parent['href']):
                        return parent['href']
                except:
                    print('Error looking for \'email\' parent on', company_name)
                    try:
                        parent = parent.parent
                    except:
                        pass
    return None

with open(os.path.join(os.curdir, r'Company.csv'), mode='w', newline='', ) as my_csv:
    wr = csv.writer(my_csv)
    wr.writerow(['Company Name', 'Phone Number', 'Company Addres', 'Email', 'City', 'State', 'Website'])
    with requests.Session() as session:
        page = ['1', '20', '40', '60', '80']
        for i in page:
            r = session.get(r'https://www.yelp.com/search?find_desc=movers&find_loc=Tuscaloosa,+AL&start=' + i)
            soup = bs4.BeautifulSoup(r.text)
            companies = soup.select('li[class=regular-search-result]')

            for i in range(len(companies)):
                city = 'Tuscaloosa'
                state = 'AL'
                company_url = str.strip(r'https://yelp.com' + companies[i].select('a[data-analytics-label=biz-name]')[0]['href'])
                company_name = str.strip(companies[i].select('h3[class=search-result-title] a[class]')[0].text)
                phonenum = str.strip(companies[i].select('div[class=secondary-attributes] span[class=biz-phone]')[0].text)
                with requests.Session() as r:
                    yelp_link = r.get(company_url)
                    yelp_link_soup = bs4.BeautifulSoup(yelp_link.text)
                    try:
                        comp_website = r'http://www.' + \
                                   yelp_link_soup.find_all(text='Business website')[0].parent.parent.select('a')[0].text
                        website_to_print = comp_website
                    except:
                        comp_website = 'NA'
                r.close()
                if comp_website != 'NA':
                    try:
                        comp_website = requests.get(comp_website)
                        company_soup = bs4.BeautifulSoup(comp_website.text)
                        website_text = company_soup.find_all(text=True)
                        website_links = company_soup.find_all(href=True)
                        email = GetEmailText(website_text)
                    except:
                        print(comp_website, 'not found for,', company_name)
                        continue
                    #if not email:   #No email was found on the first page
                       # email = GetEmailTextFromLinks(website_links)
                else:
                    email = 'NA'
                try:
                    address = str.strip(companies[i].select('address')[0].text)
                    wr.writerow([company_name, phonenum, address, email, city, state, website_to_print])
                except IndexError:
                    try:
                        address = str.strip(companies[i].select('div[class=service-area]')[0].text)
                    except:
                        address = 'NA'
                    wr.writerow([company_name, phonenum, address,email, city, state, website_to_print])

my_csv.close()