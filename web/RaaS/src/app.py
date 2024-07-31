from flask import Flask, request, render_template, Response, redirect,jsonify, make_response, g, redirect, send_file
import requests
import urllib.parse
import re

app = Flask(__name__)

@app.route('/', methods=['GET'])
def main_page():
    return render_template('home.html')

def check_url(url):
    url = url.lower()
    pattern = r'[()=$`]'
    if bool(re.search(pattern, url, re.IGNORECASE | re.DOTALL)):
        return False
    if url.startswith("j") or "javascript" in url:
        return False
    return True

def check_title(title):
    if "<" in title or ">" in title:
        return False
    return True

@app.route('/redirectTo', methods=['GET'])
def redirect_to():

    url = request.args.get("url")
    title = request.args.get("title")
    default_url = "https://www.youtube.com/watch?v=xvFZjo5PgG0&ab_channel=Duran"

    if not isinstance(title,str) or not isinstance(url,str):
        return render_template('redirect.html',url=default_url, title="title")
    url = url.strip()

    if not check_url(url) or not check_title(title):
        return render_template("redirect.html", title=title, url=default_url)
    return render_template('redirect.html',url=url, title=title)

@app.route('/redirectAdmin', methods=['GET'])
def redirect_admin():
    default_url = "https://www.youtube.com/watch?v=xvFZjo5PgG0&ab_channel=Duran"
    admin_bot = "http://raas-admin:3000/report_to_admin"
    url = request.args.get("url")
    title = request.args.get("title")
    
    if not isinstance(title,str) or not isinstance(url,str):
        requests.post(admin_bot, json={"url":default_url, "title":"title"})
        return jsonify({"message":"done"}), 201

    url = url.strip()
    if not check_url(url) or not check_title(title):
        requests.post(admin_bot, json={"url":default_url, "title":"title"})
        return jsonify({"message":"done"}), 201

    requests.post(admin_bot, json={"url":url, "title":title})
    return jsonify({"message":"done"}), 201


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)