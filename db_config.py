from app import app
from flaskext.mysql import MySQL

msql = MySQL()
#db Confugurations
app.config['user-name'] = ''
app.config['password'] = ''
app.config['database'] = ''
app.config['localhost'] = ''
mysql.init_app(app)