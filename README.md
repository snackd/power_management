# power_management
###### tags: `DAE`


### 啟用

1.使用 cmd 切到虛擬環境

##### windows
```
cd venv\Scripts
activate
```

##### Linux
```
source venv/bin/activate
```


##### 若無使用虛擬環境

使用 pip 安裝 requirements.txt 中的 Python 類庫內容：
```
$ pip install -r requirements.txt
```

> requirements.txt 內容：
```
# Library dependencies for the python code.  You need to install these with
# `pip install -r requirements.txt` before you can run this.

alembic==1.7.7
APScheduler==3.9.1
async-timeout==4.0.2
blinker==1.4
certifi==2022.5.18.1
charset-normalizer==2.0.12
click==8.1.3
colorama==0.4.4
Deprecated==1.2.13
dnspython==2.2.1
dominate==2.6.0
email-validator==1.2.1
flake8==4.0.1
Flask==2.1.2
Flask-Bootstrap==3.3.7.1
Flask-Login==0.6.1
Flask-Mail==0.9.1
Flask-Migrate==2.6.0
Flask-Moment==1.0.2
Flask-Script==2.0.5
Flask-SQLAlchemy==2.5.1
Flask-WTF==1.0.1
gpio==0.3.0
greenlet==1.1.2
idna==3.3
importlib-metadata==4.11.4
itsdangerous==2.1.2
Jinja2==3.1.2
Mako==1.2.0
MarkupSafe==2.1.1
mccabe==0.6.1
mysqlclient==2.1.0
packaging==21.3
paho-mqtt==1.6.1
pycodestyle==2.8.0
pyflakes==2.4.0
PyJWT==2.4.0
PyMySQL==1.0.2
pyparsing==3.0.9
pyserial==3.5
python-magic-bin==0.4.14
pytz==2022.1
pytz-deprecation-shim==0.1.0.post0
redis==4.3.1
requests==2.27.1
six==1.16.0
SQLAlchemy==1.4.36
tzdata==2022.1
tzlocal==4.2
urllib3==1.26.9
visitor==0.1.3
Werkzeug==2.1.2
wrapt==1.14.1
WTForms==3.0.1
zipp==3.8.0
```

#### 2.切到環境的指定路徑，執行程式

```
cd XXX\power_management
python manage.py runserver -h 0.0.0.0 -p 5000 -d
```

#### 3.到當地網頁頁面登入

```
ip:
localhost:5000

account:
User1
password:
123456
```
