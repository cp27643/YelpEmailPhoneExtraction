import bs4, datetime, csv, os, re, requests, json

def GetContactPageInfo(set):
    if set != []:
        for contact in set:
            if type(contact) == bs4.NavigableString:
                contact = contact.parent
            try:
                email = CheckForEmailOnWebpage(contact['href'])
                if email is not None:
                    return email
            except:
                continue
    return None

def GetAddress():
    try:
        address = str.strip(company.select('address')[0].text)
        comma = str.find(address,',')
        street = address[:comma]
        zip = address[-5:]
        return [street, zip]
    except IndexError:
        try:
            address = str.strip(company.select('div[class=service-area]')[0].text)
        except:
            address = ['#NA', '#NA']
    return address

def CheckForEmailOnWebpage(webpage_url):
    try:
        with requests.session() as r:
            if 'http://www.' not in webpage_url:
                webpage_url = comp_website + '/' + webpage_url
            webpage_soup = bs4.BeautifulSoup(r.get(webpage_url).text, 'html5lib')  # contains companies homepage website html code
        r.close()
        at_text = webpage_soup.find_all(text=re.compile('@', re.IGNORECASE))  # all strings containing '@'
        email_objects = webpage_soup.find_all(href=re.compile('mail', re.IGNORECASE))  # all strings containing 'mail'
        for some_text in at_text:
            email = CheckIfEmailInText(str.strip(some_text))
            if email is not None:
                return email
        for obj in email_objects:
            email = CheckIfEmailInText(str.strip(obj.text))
            if email is not None:
                return email
            email = CheckIfEmailInText(str.strip(obj['href']))  # See if email in any hrefs nearby
            if email is not None:
                return email
        return None
    except:
        raise LookupError()

def DataAfterEmailText(text):
    endemail = str.find(text, '.')+3
    if len(text) > endemail +1:
        return True
    return False

def CheckIfEmailInText(text):
    if '@' in text and '.' in text and len(text) < 200:
        alist = [0]
        lookfora = True
        while lookfora:     #add all @ symbols to alist
            founda = str.find(text, '@', alist[-1]+1)
            if founda != -1:
                alist.append(founda)
            else:
                lookfora = False

        for i in alist[1:]: #Not including intialized 0
            period_index = str.find(text[i:], '.')
            if str.isalnum(text[i + 1:i + period_index]):
                if DataAfterEmailText(text):    # string that might just have garbage after email
                    if str.isalnum(text[i + period_index + 4]): #.com .net .org .gov all should be fine, but .asdf wont
                        return None
                if str.isalpha(text[i + period_index+1:i + period_index + 4]):#make sure its .com .net .org .gov type
                    if 'mailto:' in text[:i + period_index + 4]:
                        colon = str.find(text, ':')
                        return text[colon+1:i+period_index+4]
                    return text[:i + period_index + 4]
        return None

def GetEmailTextFromLinks(webobjs):
    for obj in webobjs:
        try:
            email = CheckIfEmailInText(obj['href'])  #email will be None, or will be email in text['href']
            if email is not None:
                return email
        except: #Current object doesn't have href attribute
            pass
        parent = obj.parent
        for i in range(5):      #Look 5 objects up for email in href
            try:
                email = CheckIfEmailInText(parent['href'])
                if email is not None:
                    return parent['href']
            except:
                try:
                    parent = parent.parent
                except:
                    break #No more parents, so we can just break out and return no email found.
    return None

print('Started at', datetime.datetime.now())
with open(os.path.join(os.curdir, r'CitiesToScrape.csv'), mode='r', newline ='') as my_csv:
    citiestoscrape = csv.reader(my_csv)
    for city in citiestoscrape:
        with requests.Session() as session:
            page = ['1', '20', '40', '60', '80']
            search_description = 'movers'
            for j in page:
                r = session.get(r'https://www.yelp.com/search?find_desc=' + search_description + '&find_loc='+city[0]+',+'+city[1]+'&start=' + j)
                soup = bs4.BeautifulSoup(r.text, 'html5lib')
                r.close()
                companies = soup.select('li[class=regular-search-result]') #companies = company boxes on yelp
                print('Number of Companies found:', len(companies))
                for i, company in enumerate(companies):
                    #TODO Pass varible of current city and state
                    email = None
                    yelp_company_url = str.strip(r'https://yelp.com'+company.select('a[data-analytics-label=biz-name]')[0]['href']) #Specific yelp site for company
                    company_name = str.strip(company.select('a[data-analytics-label=biz-name] span')[0].text)
                    if str.find(company_name, 'American') > 0:
                        flag = 1
                        pass
                    phonenum = str.strip(company.select('div[class=secondary-attributes] span[class=biz-phone]')[0].text)
                    with requests.Session() as r:
                        yelp_link_soup = bs4.BeautifulSoup(r.get(yelp_company_url).text, 'html5lib')
                    r.close()
                    try:
                        comp_website = r'http://www.' + \
                                       yelp_link_soup.find_all(text='Business website')[0].parent.parent.select('a')[0].text
                    except:
                        comp_website = '#NA'
                    if comp_website != '#NA':    #found an actual website
                        try:
                            email = CheckForEmailOnWebpage(comp_website)
                            if email is None:
                                # Look for contact page and check for email on it.
                                company_soup = bs4.BeautifulSoup(r.get(comp_website).text, 'html5lib')
                                contact_pages = company_soup.find_all(href=re.compile('Contact', re.IGNORECASE))
                                contact_texts = company_soup.find_all(text =re.compile('Contact', re.IGNORECASE))
                                email = GetContactPageInfo(contact_pages)
                                if email is None:
                                    email = GetContactPageInfo(contact_texts)
                        except:
                            print('Unexpected Error occurred when looking for email for,', company_name)
                            continue
                    else:
                        print(int(j)+i, 'Website not found for,', company_name)
                    address = GetAddress()
                    with open(os.path.join(os.curdir, r''+city[1]+'.csv'), mode='a', newline='', ) as input_csv:
                        wr = csv.writer(input_csv)
                        if email is None:
                            print(int(j)+i,'Unable to find email for,', company_name)
                            email = '#NA'
                        try:
                            if "Serving" in address:
                                wr.writerow([company_name, phonenum, email, address, city[0], city[1], "#NA", comp_website])
                            else:
                                wr.writerow([company_name, phonenum, email, address[0], city[0], city[1], address[1], comp_website])
                        except:
                            pass
                    input_csv.close()
    my_csv.close()
    print('Finished at', datetime.datetime.now())
