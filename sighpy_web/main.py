from flask import Flask, request, render_template
from sqlalchemy import create_engine

app = Flask(__name__)

engine = create_engine('mysql+pymysql://colin:colinpass1@127.0.0.1/sighpy')


@app.route("/")
def home():
    with engine.begin() as connection:
        cxn_trans = connection.execute("SELECT address FROM dc_site_location ORDER BY RAND() LIMIT 10")
        home_data = cxn_trans.fetchall()
        home_data = home_data[1:]

    return render_template("home.html", home_data=home_data)


@app.route("/data")
def data():
    return render_template("data.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/calculator")
def calculator():
    return render_template("calculator.html")


if __name__ == "__main__":
    app.run(debug=True)
