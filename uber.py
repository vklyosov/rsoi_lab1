# -*- coding: UTF-8 -*-
from flask import Flask, render_template, flash, redirect, request
from flask_wtf import Form
from wtforms import StringField
from wtforms.validators import DataRequired
import requests

CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'

app_id = 'lkGOCMim0p8leqb-ZhEVN3snENnvMj5R'
app_secret = 'HU-h5wktXnrCUIQgkX2O0HAuXzSjfLNbm7x4Xba9'
server_token = 'VMA7hjw8yYv9s9uUW93pdlYbG2I3MfTFCMneuYJs'


app = Flask(__name__)
app.config.from_object(__name__)


class PricesForm(Form):
    start_location = StringField('start', validators=[DataRequired()])
    end_location = StringField('end', validators=[DataRequired()])


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    form = PricesForm()
    geocode_url = 'https://geocode-maps.yandex.ru/1.x/'
    uberapi_url = 'https://api.uber.com/v1/estimates/price'
    if form.validate_on_submit():
        start = form.start_location.data
        end = form.end_location.data
        geo_param = {'format': 'json', 'geocode': start}
        r = requests.get(geocode_url, geo_param)
        start_point = r.json()['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']
        t = start_point.partition(' ')
        start_longitude = float(t[0])
        start_latitude = float(t[2])

        geo_param['geocode'] = end
        r = requests.get(geocode_url, geo_param)
        end_point = r.json()['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']
        t = end_point.partition(' ')
        end_longitude = float(t[0])
        end_latitude = float(t[2])

        uber_param = {'server_token': server_token, 'start_latitude': start_latitude, 'start_longitude':
            start_longitude, 'end_latitude': end_latitude, 'end_longitude': end_longitude}
        r = requests.get(uberapi_url, uber_param)
        p = r.json()['prices']
        distance = p[0]['distance'] * 1.60934
        flash(u'Расстояние: ' + str(distance) + u' км')
        for item in p:
            flash(item['display_name'] + ': ' + item['estimate'])
    return render_template('index.html', form=form)


@app.route('/me')
def me():
    redirect_uri = 'http://localhost:5000/me'
    auth_url = 'https://login.uber.com/oauth/v2/authorize'
    uber_token_url = 'https://login.uber.com/oauth/v2/token'
    code = request.args.get('code')
    if code is None:
        return redirect(auth_url + '?response_type=code&client_id=' + app_id + '&redirect_uri=' + redirect_uri
                    + '&scope=profile')

    param = {'client_id': app_id, 'client_secret': app_secret, 'grant_type': 'authorization_code', 'redirect_uri':
             redirect_uri, 'code': code}
    r = requests.post(uber_token_url, data=param)
    if r.status_code != 200:
        return 'wrong code'

    token = r.json()['access_token']
    me_url = 'https://api.uber.com/v1/me'
    headers = {'Authorization': 'Bearer ' + token}
    r = requests.get(me_url, headers=headers)
    if r.status_code != 200:
        return 'wrong token'

    dic = r.json()
    first_name = dic['first_name']
    last_name = dic['last_name']
    email = dic['email']
    return render_template('me.html', first_name=first_name, last_name=last_name, email=email)


if __name__ == '__main__':
    app.run(debug=True)
