# scrapy-tcmb

## deploy

1. Install [scrapyd-client](https://github.com/scrapy/scrapyd-client)
```
pip install scrapyd-client
```
[Resolve 'scrapyd-deploy' is not recognized as an internal or external command](#scrapyd-deploy-is-not-recognized-as-an-internal-or-external-command)

2. Create a deploy profile in scrapy configuration file. File is named scrapy.cfg and can be found in project folder.

```
# Automatically created by: scrapy startproject
#
# For more information about the [deploy] section see:
# https://scrapyd.readthedocs.io/en/latest/deploy.html

[settings]
default = tcmb.settings

[deploy]
url = http://localhost:6800/
project = tcmb
```

3. Run [scrapyd](http://doc.scrapy.org/en/0.16/topics/scrapyd.html) on localhost or create ssh tunnel for remote server
```
$ ssh -i fkeles-nopass -L 6800:localhost:6800 opc@130.61.84.44 -N
```

4. Explore deployment profiles
```
(base) C:\Users\fakeles\Desktop\py-project\data-scraper\tcmb>scrapyd-deploy -l
C:\Anaconda3\Scripts\scrapyd-deploy:23: ScrapyDeprecationWarning: Module `scrapy.utils.http` is deprecated, Please import from `w3lib.http` instead.
  from scrapy.utils.http import basic_auth_header
default              http://localhost:6800/
```

4. Run deploy command, you should see 200 Http response code and a JSON similar to below
```
(base) C:\Users\fakeles\Desktop\py-project\data-scraper\tcmb>scrapyd-deploy -v 1
C:\Anaconda3\Scripts\scrapyd-deploy:23: ScrapyDeprecationWarning: Module `scrapy.utils.http` is deprecated, Please import from `w3lib.http` instead.
  from scrapy.utils.http import basic_auth_header
Packing version 1575403501
Deploying to project "tcmb" in http://localhost:6800/addversion.json
Server response (200):
{"node_name": "fkeles-scrapyd-server", "status": "ok", "project": "tcmb", "version": "1575403501", "spiders": 1}
```
[Resolve deployment errors](#Deployment-errors)

5. List projects and versions, delete
```
(base) C:\Users\fakeles\Desktop\py-project\data-scraper\tcmb>curl http://localhost:6800/listprojects.json
{"node_name": "fkeles-scrapyd-server", "status": "ok", "projects": ["myproject", "tcmb"]}
(base) C:\Users\fakeles\Desktop\py-project\data-scraper\tcmb>curl http://localhost:6800/listversions.json?project=tcmb
{"node_name": "fkeles-scrapyd-server", "status": "ok", "versions": ["1"]}
(base) C:\Users\fakeles\Desktop\py-project\data-scraper\tcmb>curl http://localhost:6800/delproject.json -d project=tcmb
{"node_name": "fkeles-scrapyd-server", "status": "ok"}
```

6. Schedule a job for downloading whole 2000 year data, list scheduled jobs
```
(base) C:\Users\fakeles\Desktop\py-project\data-scraper\tcmb>curl http://localhost:6800/schedule.json -d project=tcmb -d spider=tcmb --d setting=loglevel=INFO d directory=. -d save-xml=false -d append-csv=false -d date-start=2000-01-01 -d date-end=2000-12-31
{"node_name": "fkeles-scrapyd-server", "status": "ok", "jobid": "86a5ea9416a711eaa13e8956a92e6e77"}

(base) C:\Users\fakeles\Desktop\py-project\data-scraper\tcmb>curl http://localhost:6800/listjobs.json?project=tcmb | python -m json.tool
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   219  100   219    0     0   1921      0 --:--:-- --:--:-- --:--:--  1921
{
    "node_name": "fkeles-scrapyd-server",
    "status": "ok",
    "pending": [],
    "running": [
        {
            "id": "86a5ea9416a711eaa13e8956a92e6e77",
            "spider": "tcmb",
            "pid": 28512,
            "start_time": "2019-12-04 15:05:37.364675"
        }
    ],
    "finished": []
}
```

## Deploy with .egg file
1. Create setup.py script
```python
from setuptools import setup, find_packages

setup(
    name='tcmb',
    version=2,
    description='A data scraper for importing XML files from tcmb.gov.tr',
    long_description='I would just open("README.md").read() here',
    author='Fatih Keles',
    author_email='fatihkeles@gmail.com',
    url='https://github.com/fatih-keles/scrapy-tcmb',
    #packages=find_packages(exclude=['*tests*']),
    packages=find_packages(),
    entry_points={'scrapy': ['settings = tcmb.settings']},
)
```
2. Generate .egg file
```
$ python setup.py bdist_egg
```

For more on ```setuptools``` and ```setup.py``` see [tutorial](https://pythonhosted.org/an_example_pypi_project/setuptools.html)

### Error Messages

#### scrapyd-deploy is not recognized as an internal or external command
If you get errors about scrapyd-client commands not known for windows environment 
```
(base) C:\Users\fakeles\Desktop\py-project\data-scraper\tcmb>scrapyd-deploy
'scrapyd-deploy' is not recognized as an internal or external command,
operable program or batch file.
```
Create a bat file around Python file scrapyd-deploy in C:\Anaconda3\Scripts (or in your own python environment, I am using Anaconda3)
```
@echo off
C:\Anaconda3\python C:\Anaconda3\Scripts\scrapyd-deploy %*
```

#### Deployment errors
If you get error messages you should resolve them. Below message is about a missing library ([cx_Oracle](https://cx-oracle.readthedocs.io/en/latest/user_guide/installation.html)) on server side, after installing it I was able to deploy without any issues. 
  ```
  (base) C:\Users\fakeles\Desktop\py-project\data-scraper\tcmb>scrapyd-deploy
C:\Anaconda3\Scripts\scrapyd-deploy:23: ScrapyDeprecationWarning: Module `scrapy.utils.http` is deprecated, Please import from `w3lib.http` instead.
  from scrapy.utils.http import basic_auth_header
Packing version 1575402733
Deploying to project "tcmb" in http://localhost:6800/addversion.json
Server response (200):
{
	"node_name": "fkeles-scrapyd-server",
	"status": "error",
	"message": 
	   "Traceback (most recent call last):\n  
	      File \"/root/anaconda3/lib/python3.7/runpy.py\", line 193, in _run_module_as_main\n
		  \"__main__\", mod_spec)\n
		  File \"/root/anaconda3/lib/python3.7/runpy.py\", line 85, in _run_code\n
		  exec(code, run_globals)\n
		  File \"/root/anaconda3/lib/python3.7/site-packages/scrapyd/runner.py\", line 40, in <module>\n
		  main()\n
		  File \"/root/anaconda3/lib/python3.7/site-packages/scrapyd/runner.py\", line 37, in main\n
		  execute()\n
		  File \"/root/anaconda3/lib/python3.7/site-packages/scrapy/cmdline.py\", line 145, in execute\n
		  cmd.crawler_process = CrawlerProcess(settings)\n
		  File \"/root/anaconda3/lib/python3.7/site-packages/scrapy/crawler.py\", line 267, in __init__\n
		  super(CrawlerProcess, self).__init__(settings)\n  
		  File \"/root/anaconda3/lib/python3.7/site-packages/scrapy/crawler.py\", line 145, in __init__\n
		  self.spider_loader = _get_spider_loader(settings)\n
		  File \"/root/anaconda3/lib/python3.7/site-packages/scrapy/crawler.py\", line 347, in _get_spider_loader\n
		  return loader_cls.from_settings(settings.frozencopy())\n
		  File \"/root/anaconda3/lib/python3.7/site-packages/scrapy/spiderloader.py\", line 61, in from_settings\n
		  return cls(settings)\n
		  File \"/root/anaconda3/lib/python3.7/site-packages/scrapy/spiderloader.py\", line 25, in __init__\n
		  self._load_all_spiders()\n
		  File \"/root/anaconda3/lib/python3.7/site-packages/scrapy/spiderloader.py\", line 47, in _load_all_spiders\n
		  for module in walk_modules(name):\n
		  File \"/root/anaconda3/lib/python3.7/site-packages/scrapy/utils/misc.py\", line 73, in walk_modules\n
		  submod = import_module(fullpath)\n
		  File \"/root/anaconda3/lib/python3.7/importlib/__init__.py\", line 127, in import_module\n
		  return _bootstrap._gcd_import(name[level:], package, level)\n
		  File \"<frozen importlib._bootstrap>\", line 1006, in _gcd_import\n
		  File \"<frozen importlib._bootstrap>\", line 983, in _find_and_load\n
		  File \"<frozen importlib._bootstrap>\", line 967, in _find_and_load_unlocked\n
		  File \"<frozen importlib._bootstrap>\", line 668, in _load_unlocked\n
		  File \"<frozen importlib._bootstrap>\", line 638, in _load_backward_compatible\n
		  File \"/tmp/tcmb-1575402733-0k7si0n8.egg/tcmb/spiders/kurlar.py\", line 18, in <module>\nModuleNotFoundError: No module named 'cx_Oracle'\n
	   "
}
  ```