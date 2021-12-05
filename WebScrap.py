from flask import Flask,render_template,redirect,jsonify,url_for,make_response
from flask.globals import current_app, request, session
from flask_sqlalchemy import SQLAlchemy
import jwt
from datetime import datetime,timedelta
import requests
from functools import wraps

from werkzeug.wrappers import response
from bs4 import BeautifulSoup



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///users.db'
app.config['SECRET_KEY']='mysecretkey'
db = SQLAlchemy(app)

class Users(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100),nullable=False)
    password = db.Column(db.String(100),nullable=False)

    def __init__(self,name,password):
        self.name = name
        self.password = password

class Coin:
    def __init__(self):
        print('Loading...')
    
    def parse(coin):
        print(coin)
        url= f'https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listing'
        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'}
        r = requests.get(url)
        data = r.json()
        ids = []
        for i in range(0,5):
            ids.append({
                'id':data['data']['cryptoCurrencyList'][i]['id'],
                'name':data['data']['cryptoCurrencyList'][i]['name'],
            })

        print(ids)
        coin_id = 0
        print(coin.title())

        for i in range(0,5):
            if ids[i]['name'] == coin.title():
                coin_id = ids[i]['id']
                print('\n\n')
                print(coin_id)

        second_url = f'https://api.coinmarketcap.com/content/v3/news?coins={coin_id}&size=5'


        r2 = requests.get(second_url)
        data2 = r2.json()

        link_news = []
        for i in range(0,len(data2['data'])):
            link_news.append(data2['data'][i]['meta']['sourceUrl']) 

        print('\n\n')
        print(link_news)

        actual_news = []
        base_url = f'https://coinmarketcap.com/headlines/news'

        for urls in link_news:
            try:
                yrl = urls
                r3 = requests.get(urls,headers = headers).text
            except:
                print(urls)
                r4 = urls[urls.rfind('.com/'):]
                r5 = r4.replace('.com','')
                print(r5)
                q = (base_url+r5)
                print(q)
                yrl = q
                r3 = requests.get(q,headers = headers).text

            soup = BeautifulSoup(r3,'html.parser')
            for div1 in soup.find_all("nav"): 
                div1.decompose()

            for div2 in soup.find_all("div" ,class_="uikit-col-16 uikit-col-lg-2"): 
                div2.decompose()

            for div5 in soup.find_all("footer"): 
                div5.decompose()
                
            for div4 in soup.find_all("div" ,class_="sc-16r8icm-0 gViJez"): 
                div4.decompose() 

            for div4 in soup.find_all("div" ,class_="rc-collapse"): 
                div4.decompose()

            paragraphs = soup.find_all('p')
            txt = [result.text for result in paragraphs]
            ARTICLE = ' '.join(txt)
            if ARTICLE == '':
                continue
            try:
                head = soup.find('h1').text
            except:
                head = soup.find('h2').text
            print(head)
            
            
            actual_news.append({
                'title':head,   
                'news':ARTICLE,
                'url':yrl
                })

        print('\n\n')
        print(actual_news)
        return actual_news


def token_required(func):
    @wraps(func)
    def decorated(*args,**kwargs):
        token = None
        token = request.cookies.get('tokenn')
        if not token:
            session['username'] = None
            session['message'] = 'First you need to Log In'
            not_token = redirect(url_for('login'))
            return not_token
        else:
            try:
                data = jwt.decode(token,app.config['SECRET_KEY'],algorithms=["HS256"])
                current_user = data['user']
            except:
                print(token)
                session['username'] = None
                session['message'] = 'You need to Log In again'
                not_token = redirect(url_for('login'))
                return not_token 
        return func(current_user,*args,**kwargs)
    return decorated



@app.route('/')
@app.route('/home')
def index():
    return render_template('index.html')

@app.route('/login',methods=["GET"])
def login_index():
    try:
        mss = session['message']
        session['message']=None
    except:
        mss=None
    return render_template('login.html',message=mss)
    

@app.route('/login',methods=["POST"])
def login():
    name = request.form['name']
    password = request.form['pass']
    user = Users.query.filter_by(name = name).first()
    if user:
        if password == user.password:
            token = jwt.encode({'user' : name , 'exp':datetime.utcnow() + timedelta(seconds=30)},str(app.config['SECRET_KEY']))
            resp = make_response(redirect(url_for('coin'))) 
            resp.set_cookie('tokenn',token)
            session['username'] = name
            return resp

        else:
            session['message'] = 'Invalid password'
    elif not user:
        session['message'] = 'No such user in database'
    

    
    res = make_response(render_template('login.html',message=session['message']))
    session.pop('message',None)
    return res
    
    

@app.route('/register',methods=["POST","GET"])
def register():
    if request.method == "POST":
        login = request.form['login']
        try:
            user = Users.query.filter_by(name = login).first()
            username = user.name
        except:
            username = None
        print(username)
        if login :
            if not username:
                password = request.form['pass']
                rpassword = request.form['rpass']
                if password == rpassword:
                    user = Users(name=login,password=rpassword)
                    try:
                        db.session.add(user)
                        db.session.commit()
                        return redirect('/login')
                    except:
                        session['message'] = "Произошла ошибка сервера"
                else:
                    session['message'] = "Not same passwords"
            else:
                session['message'] = "Пользователь с таким именем уже существует"
        else:
            session['message'] = "Пустое поле Логина"
        res = make_response(render_template('register.html',message=session['message']))
        session.pop('message',None)
        return res
    
    return render_template('register.html')

@app.route('/coin',methods=["POST","GET"])
@token_required
def coin(current_user):
    if request.method=='POST':
        coin = request.form.get('coin')
        c = Coin.parse(coin)
        print(len(c))
        return render_template('coin.html',coin = coin,news = c,user = current_user)
    return render_template('coin.html')

@app.route('/logout')
def logout():
    response = redirect(url_for('login'))
    response.delete_cookie('tokenn')
    session['username'] = None
    return response



@app.route('/users')
def users():
    coin_users = Users.query.all()
    users = []
    for user in coin_users:
        user_info = {}
        user_info['login'] = user.name
        user_info['password'] = user.password
        users.append(user_info)
    
    return jsonify({'users':users})


if __name__ == '__main__':   
    app.run(debug=True)