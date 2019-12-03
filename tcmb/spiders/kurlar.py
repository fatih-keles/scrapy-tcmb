# -*- coding: utf-8 -*-
"""
Created on Fri Nov 29 13:11:21 2019

@author: fakeles

Scrapes FX exchange time series data from TCMB
""" 


import scrapy
import os
import pandas as pd
from dateutil import parser, rrule
from datetime import datetime, date, timedelta
from twisted.internet.error import DNSLookupError, TimeoutError, TCPTimedOutError
from urllib.parse import urlsplit
import cx_Oracle
#from sqlalchemy import types, create_engine

class TCMBSpider(scrapy.Spider):
    """Scrapes data from olx.ro web pages"""
    name = "tcmb"
    
    custom_settings = {
        'RETRY_ENABLED': False,
        'DEPTH_LIMIT' : 0,
        'DEPTH_PRIORITY' : 1,
        'LOG_ENABLED' : False,
        'CONCURRENT_REQUESTS_PER_DOMAIN' : 80,
        'CONCURRENT_REQUESTS' : 90,
        'DOWNLOAD_DELAY' : 5.0, 
        'AUTOTHROTTLE_ENABLED' : True,
        'HTTPCACHE_ENABLED' : True,
    }
    
    """ command line arguments """
    arguments = {
        'save_xml' : False,
        'append_csv' : False,
        'directory': '.',
        'date_start' : parser.parse('1999-01-04'),
        'date_end' : None,
    }
    
    """ pandas dataframe column """
    data_columns = ['CrawledDate', 'URL', 
                   'Tarih', 'Bulten_No', 
                   'CrossOrder', 'Kod', 'CurrencyCode',
		           'Unit', 'Isim', 'CurrencyName', 'ForexBuying', 'ForexSelling', 'BanknoteBuying', 'BanknoteSelling', 'CrossRateUSD', 'CrossRateOther'
                   ]
    
    """ Database related """
    db_table_exists = False
    insert_sql = """INSERT INTO demo.currency_time_series (
                                 crawleddate, url, tarih, bulten_no, crossorder, kod, currencycode, 
                                 unit, isim, currencyname, forexbuying, forexselling, banknotebuying,
                                 banknoteselling, crossrateusd, crossrateother )
                         VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9,:10,:11,:12,:13,:14,:15,:16) """
    delete_sql = """ DELETE FROM demo.currency_time_series WHERE tarih = :tarih"""
    check_table_sql = """ SELECT COUNT(*) ctr FROM all_tables WHERE 1=1 AND owner||'.'||table_name = 'DEMO.CURRENCY_TIME_SERIES'"""
    create_table_sql = """ CREATE TABLE demo.currency_time_series (	
                                CRAWLEDDATE Date, 
	                            URL VARCHAR2(4000 BYTE), 
	                            TARIH Date, 
	                            BULTEN_NO VARCHAR2(4000 BYTE), 
	                            CROSSORDER VARCHAR2(4000 BYTE), 
	                            KOD VARCHAR2(4000 BYTE), 
	                            CURRENCYCODE VARCHAR2(4000 BYTE), 
	                            UNIT number, 
	                            ISIM VARCHAR2(4000 BYTE), 
	                            CURRENCYNAME VARCHAR2(255 BYTE), 
	                            FOREXBUYING number, 
	                            FOREXSELLING number, 
	                            BANKNOTEBUYING number, 
	                            BANKNOTESELLING number, 
	                            CROSSRATEUSD number, 
	                            CROSSRATEOTHER number) """
    #WDF = pd.DataFrame(data=None, columns=data_columns)
    
    def start_requests(self):
        #print('1')
        self.logger.info('start requests'.center(80,'*'))
        
        base_url = "https://www.tcmb.gov.tr/kurlar/"
        #url = "https://www.tcmb.gov.tr/kurlar/201808/09082018.xml"
        #url = "https://www.tcmb.gov.tr/kurlar/1999/01011999.xml"
        
        self.logger.info('check for command line arguments')
        self.arguments['save_xml'] = self.str2bool(getattr(self, 'save-xml', 'false'))
        self.arguments['append_csv'] = self.str2bool(getattr(self, 'append-csv', 'false'))
        self.arguments['date_start'] = parser.parse(getattr(self, 'date-start', '1996-04-04'))
        self.arguments['date_end'] = parser.parse(getattr(self, 'date-end', datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d')))
        self.arguments['directory'] = getattr(self, 'directory', '.')
        self.logger.debug(f'Program Parameters: {self.arguments}')
        
        self.logger.info('generate URLs for days')
        days_list = list(rrule.rrule(freq=rrule.DAILY, dtstart=self.arguments['date_start'], until=self.arguments['date_end']))
        """ skip weekends as no data supplied by tcmb """
        days_list = [x for x in days_list if x.weekday() < 5]
        url_list = [base_url + datetime.strftime(x, '%Y%m/%d%m%Y.xml') for x in days_list]
        self.logger.debug(f'generated URLs: {url_list}')
        if len(url_list) == 0:
            raise Exception('URL list is empty', 'Check runtime parameters date-start and date-end')
        
        """ create database table if not exists """
        if not self.db_table_exists:
            self.create_table_not_exists()
        
        #print('2')
        for url in url_list:
            self.logger.info(f'URL: {url}')
            cURLCommandString = "curl '{}' ".format(url)
            cURLCommandString += " -H 'Connection: keep-alive' -H 'Cache-Control: max-age=0' -H 'DNT: 1' -H 'Upgrade-Insecure-Requests: 1' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36' -H 'Sec-Fetch-User: ?1' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3' -H 'Sec-Fetch-Site: none' -H 'Sec-Fetch-Mode: navigate' -H 'Accept-Encoding: gzip, deflate, br' -H 'Accept-Language: en-US,en;q=0.9,tr;q=0.8' -H 'Cookie: TS01ab7d04=015d31d691581b3673c0d902d50397e92f222b5b1706d1bfa9db0e5547be9d953843c5f1a849534dc1e79534ae322ddabce971a260' -H 'If-None-Match: ""c0579-200d-572ffc92dc440""' -H 'If-Modified-Since: Thu, 09 Aug 2018 12:30:01 GMT' --compressed"
        
            self.logger.debug(f'Starting with: {cURLCommandString}')
            request = scrapy.Request.from_curl(cURLCommandString)
            request.callback = self.download_xml_file
            request.errback = self.error_callback
            request.dont_filter = True
            request._meta = {'arguments' : self.arguments, }
            self.logger.debug("Existing settings: %s" % self.settings.attributes)
            yield request
            
        #self.WDF.to_csv('all-data.csv')
            
    def download_xml_file(self, response):
        """Download xml file in working directory"""
        #print('4')
        
        self.logger.info('Download XML File::[START]'.center(80,'*'))
        if response.status == 200:
            content_type = response.headers.get('Content-Type', 'unknown')
            content_type = content_type.decode('utf-8')
            content_length = int(response.headers.get('Content-Length', 0))
            """ if this is an XML file and not empty """
            if content_type == 'application/xml' and content_length >= 0:
                """ parse XML document """
                rows = []
                Tarih = response.xpath('/Tarih_Date/@Tarih').get()
                self.logger.info(Tarih)
                Tarih = parser.parse(Tarih)
                Bulten_No = response.xpath('/Tarih_Date/@Bulten_No').get()
                
                c_list = response.xpath('//Currency').getall()
                for c in c_list:
                    c_xml = scrapy.selector.Selector(text=c, type='xml')
                    row = {}
                    row['CrawledDate'] = datetime.now()
                    row['URL'] = response.url
                    row['Tarih'] = Tarih
                    row['Bulten_No'] = Bulten_No
                    row['CrossOrder'] = c_xml.xpath('@CrossOrder').get()
                    row['Kod'] = c_xml.xpath('@Kod').get()
                    row['CurrencyCode'] = c_xml.xpath('@CurrencyCode').get()
                    row['Unit'] = c_xml.xpath('Unit/text()').get()
                    row['Isim'] = c_xml.xpath('Isim/text()').get()
                    row['CurrencyName'] = c_xml.xpath('CurrencyName/text()').get()
                    row['ForexBuying'] = c_xml.xpath('ForexBuying/text()').get()
                    row['ForexSelling'] = c_xml.xpath('ForexSelling/text()').get()
                    row['BanknoteBuying'] = c_xml.xpath('BanknoteBuying/text()').get()
                    row['BanknoteSelling'] = c_xml.xpath('BanknoteSelling/text()').get()
                    row['CrossRateUSD'] = c_xml.xpath('CrossRateUSD/text()').get()
                    row['CrossRateOther'] = c_xml.xpath('CrossRateOther/text()').get()
                    for key,value in row.items():
                        if value and isinstance(value, str):
                            row[key] = value.strip()
                        if value == None:
                            row[key] = ''
                    rows.append(row)
                
                df = pd.DataFrame(data=rows, columns=self.data_columns)
                df.fillna(value='', inplace=True)
                #self.WDF.append(df)
                
                self.save_to_db(pandasDF=df, current_date=Tarih)
                self.save_xml_file(response)
                self.append_csv(response, pandasDF=df)
                
                                    
        self.logger.info('Download XML File::[END]'.center(80,'*'))
    
    def get_db_connection(self):
        """ get database connection """
        #db_user = 'ADMIN'
        #db_password = 'WelcomeADWC1!'
        #host = 'adb.eu-frankfurt-1.oraclecloud.com'
        #connection = create_engine('oracle+cx_oracle://scott:tiger@host:1521/?service_name=hr')
        
        dsn = '(description= (retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1522)(host=adb.eu-frankfurt-1.oraclecloud.com))(connect_data=(service_name=lpdmasisaukuwfd_fkweb19dec_high.adwc.oraclecloud.com))(security=(ssl_server_cert_dn="CN=adwc.eucom-central-1.oraclecloud.com,OU=Oracle BMCS FRANKFURT,O=Oracle Corporation,L=Redwood City,ST=California,C=US")))'
        connection = cx_Oracle.connect("ADMIN", "WelcomeADWC1!", dsn, encoding="UTF-8")
        return connection
    
    def create_table_not_exists(self):
        """ creates database table if not exists """
        connection = self.get_db_connection()
        cursor = connection.cursor()
        self.logger.debug(f'Connected: {connection}')
        
        cursor.execute(self.check_table_sql)
        ctr, = cursor.fetchone()
        if ctr == 0:
            cursor.execute(self.create_table_sql)
        self.db_table_exists = True
        connection.commit()
        connection.close()
    
    def save_to_db(self, pandasDF, current_date):
        """ save to database """
        #db_user = 'ADMIN'
        #db_password = 'WelcomeADWC1!'
        #host = 'adb.eu-frankfurt-1.oraclecloud.com'
        #connection = create_engine('oracle+cx_oracle://scott:tiger@host:1521/?service_name=hr')
        
        connection = self.get_db_connection()
        self.logger.debug(f'Connected: {connection}')
        rows = [tuple(x) for x in pandasDF.values]
        cursor = connection.cursor()
        self.logger.debug(f'Cursor: {cursor}')
        self.logger.debug(f'Rows: {rows}')
                
        cursor.execute(self.delete_sql, [current_date, ])
        self.logger.info(str(cursor.rowcount) + " rows deleted")
        connection.commit()
                
        self.logger.info(str(len(rows)) + ' rows will be inserted')
        cursor.executemany(self.insert_sql, rows)
        connection.commit()
        connection.close()
                
    def save_xml_file(self, response):
        """ if files are to be saved """
        fs_items = [x for x in urlsplit(response.url).path.split('/') if x != '']
        dir_path = '/'.join([x for x in fs_items if not x.endswith(r'.xml')])
                
        """ save xml """
        if self.arguments['save_xml']:
            file_name = [x for x in fs_items if x.endswith(r'.xml')][0]
            os.chdir(self.arguments['directory'])
            os.makedirs( name=dir_path, mode=0o777, exist_ok=True);
            self.logger.info(f'Created directory:{dir_path}')
            
            file_path = dir_path + '/' + file_name
            self.logger.info(f'Writing to XML file:{file_name}')
            with open(file_path, 'w', encoding='utf-8') as f:
                file_contents = response.body.decode('utf-8').translate(str.maketrans('', '', '\n\t\r'))
                f.write(file_contents)
                
    def append_csv(self, response, pandasDF):
        """ append csv """
        if self.arguments['append_csv']:
            file_name = 'currency.csv'
            file_path = './' + file_name
            self.logger.info(f'Appending to CSV file:{file_name}')
            pandasDF.to_csv(path_or_buf=file_path, mode='a', index=False, index_label='S/N', encoding='utf-8')
                        
    def error_callback(self, failure):
        # log all failures
        #print('3')
        #self.logger.error(repr(failure))
        # in case you want to do something special for some errors,
        # you may need the failure's type:
        if failure.check(scrapy.spidermiddlewares.httperror.HttpError):
            # these exceptions come from HttpError spider middleware
            # you can get the non-200 response
            response = failure.value.response
            #self.logger.error('HttpError on %s', response.url)
            if failure.value.response.status == 404:
                url_items = [x for x in urlsplit(response.url).path.split('/') if x != '']
                day_name = [x for x in url_items if x.endswith(r'.xml')][0]
                day_name = day_name.replace(r'.xml', '')
                self.logger.info(datetime.strftime(datetime.strptime(day_name, '%d%m%Y'), '%d.%m.%Y') + ' not found!')
                #self.logger.error(response.url + ' day data not found')
        elif failure.check(DNSLookupError):
            # this is the original request
            request = failure.request
            self.logger.error('DNSLookupError on %s', request.url)
        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            self.logger.error('TimeoutError on %s', request.url)
        
    
    def str2bool(self, v):
        return str(v).lower() in ("yes", "true", "t", "1")