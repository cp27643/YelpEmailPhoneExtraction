import requests, bs4, pprint, csv, os, re
emails = [[]]
notfound = True
email_domains = ['.com', '.net', '.org']

def GetWebsite(some_url):
    try:
        with requests.Session() as r:
            yelp_link = r.get(some_url)
            yelp_link_soup = bs4.BeautifulSoup(yelp_link.text)
            yelp_link.close()
            comp_website = r'http://www.' + yelp_link_soup.find_all(text ='Business website')[0].parent.parent.select('a')[0].text
        return comp_website
    except:
        pass
        return True

def CheckIfEmailInText(text_list):
    for some_text in text_list:
        #TODO NEED TO CHECK TO See IF THIS WILL ACCOUNT FOR TEXTS WITH MULTIPLE @ SYMBOLS
        if '@' in some_text and '.' in some_text and len(some_text) < 200:
            alist = []
            for n in range(len(some_text)):
                if some_text.find('@', n) == n:
                    alist.append(n)

            for i in alist:
                period_index = str.find(some_text[i:], '.')
                if str.isalnum(some_text[i+1:i+period_index]) and some_text[i + period_index:i + period_index+4] in email_domains:
                    if not str.isalnum(some_text[:i]):
                        for nonalnum, char in enumerate(some_text):
                            if not str.isalnum(char) and not char == ' ':
                                #TODO Modify function to search through string from @ and return space if non numeric,
                                #TODO if there is no space, then just return the full email
                                #TODO to account for 'email: alsd_fh@gmail.com" type strings
                                return some_text[nonalnum+1: i + period_index + 4]
                    return some_text[:i+period_index+4]
    return None

def GetEmailTextFromLinks(weblinks):
    for text in weblinks:
        try:
            CheckIfEmailInText(text['href'])
        except:
            parent = text.parent
        for i in range(5):
            try:
                if CheckIfEmailInText(parent['href']):
                    return parent['href']
            except:
                try:
                    parent = parent.parent
                except:
                    pass
        print("Unable to find email for", company_name, 'on', website_to_print)
        return None

def CheckIfEmailInLinks(weblinks, base_weblink):
    for link in weblinks:
        href = link['href']
        with requests.session() as s:
            request_link = s.get(base_weblink + href)
            link_soup = bs4.BeautifulSoup(request_link.text)
            request_link.close()
            link_email = CheckIfEmailInText(link_soup(text=re.compile('@')))
            if link_email is not None:
                return link_email
    return None

with open(os.path.join(os.curdir, r'Company.csv'), mode='w', newline='', ) as my_csv:
    wr = csv.writer(my_csv)
    wr.writerow(['Company Name', 'Phone Number', 'Company Addres', 'Email', 'City', 'State', 'Website'])
    with requests.Session() as session:
        page = ['1', '20', '40', '60', '80']
        search_description = 'movers'
        for i in page:
            r = session.get(r'https://www.yelp.com/search?find_desc=' + search_description + '&find_loc=Tuscaloosa,+AL&start=' + i)
            soup = bs4.BeautifulSoup(r.text)
            r.close()
            companies = soup.select('li[class=regular-search-result]')
            for i in range(len(companies)):
                print('Number of Companies found:', len(companies))
                city = 'Tuscaloosa'
                state = 'AL'
                company_url = str.strip(r'https://yelp.com' + companies[i].select('a[data-analytics-label=biz-name]')[0]['href'])
                company_name = str.strip(companies[i].select('h3[class=search-result-title] a[class]')[0].text)
                phonenum = str.strip(companies[i].select('div[class=secondary-attributes] span[class=biz-phone]')[0].text)
                with requests.Session() as r:
                    yelp_link = r.get(company_url)
                    yelp_link_soup = bs4.BeautifulSoup(yelp_link.text)
                    yelp_link.close()
                    try:
                        comp_website = r'http://www.' + \
                                   yelp_link_soup.find_all(text='Business website')[0].parent.parent.select('a')[0].text
                        website_to_print = comp_website
                    except:
                        comp_website = 'NA'
                        website_to_print = 'NA'
                r.close()
                if comp_website != 'NA':
                    try:
                        comp_website = requests.get(comp_website)
                        company_soup = bs4.BeautifulSoup(comp_website.text)
                        comp_website.close()
                        at_text = company_soup.find_all(text=re.compile('@', re.IGNORECASE))
                        email_objects = company_soup.find_all(text=re.compile('mail', re.IGNORECASE))
                        email = CheckIfEmailInText(at_text)
                        # if email is None or email is "": #Email is not on homepage
                        #     website_links = company_soup(href = re.compile('^/+[a-z-!#.,%]+/$'))    #Going to look for email in homepage hyperlink pages
                        #     if website_links is not None:
                        #         email = CheckIfEmailInLinks(website_links, website_to_print)
                        # if email is None:
                        #     email = GetEmailTextFromLinks(email_objects)
                        if email is None:
                            print(i, 'Unable to find email for', company_name)
                        else:
                            print('Found email for', company_name)
                        #     #TODO write function to return any email in email object text, or parent or child text containing email
                        #     #GetEmailObjectText(email_objects)
                        #     pass
                    except:
                        print(i, comp_website, 'not found for,', company_name)
                        continue
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
