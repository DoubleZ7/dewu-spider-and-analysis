from flask import Flask

app = Flask(__name__)


@app.route('/hello')
def hello():
    return 'Hello word!'


if __name__ == '__main__':
    app.run()
