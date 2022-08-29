#!/usr/bin/env python3

import click
import configparser
import webbrowser
import requests
import json

CONFIG_FILE = "config.ini"

URL_BASE = "http://3.83.45.177:3000/"
# URL_BASE = "http://localhost:3000/"
URL_LOGIN = URL_BASE + "student/login"
URL_GET_USER = URL_BASE + "student/info?token="
URL_PUSH_DATA = URL_BASE + "student/push"


class telemetry:
    def __init__(self, courseName):
        self.courseName = courseName
        self.userToken = None

    def checkToken(self, token):
        return True if len(token) == 64 else False

    def prompToken(self):
        print("Past the token provide by the website after autentication")
        return input("Token:")

    def createConfig(self, token, user):
        config = configparser.ConfigParser()
        config["active handout"] = {}
        config["active handout"]["token"] = token
        config["active handout"]["nickname"] = user["nickname"]
        config["active handout"]["name"] = user["name"]
        config["active handout"]["email"] = user["email"]
        with open(CONFIG_FILE, "w") as configfile:
            config.write(configfile)

    def getStudentFromToken(self, token):
        response = requests.get(URL_GET_USER + token)
        if response.status_code != 200:
            return None
        else:
            user = json.loads(response.content)
            return user[0]["fields"]

    def auth(self):
        config = configparser.ConfigParser()
        if config.read(CONFIG_FILE):
            try:
                token = config["active handout"]["token"]
            except:
                token = ""
            if self.checkToken(token):
                self.userToken = token
                return True

            print("Wrong token, please update")

        webbrowser.open(URL_LOGIN, new=1)

        while True:
            token = self.prompToken()
            if self.checkToken(token):
                user = self.getStudentFromToken(token)
                if user != None:
                    break

            print("Wrong token, please check copy and paste")

        self.createConfig(token, user)
        print("Hello %s" % user["name"])

        self.userToken = token
        return True

    def push(self, log, channel=0):
        if self.userToken == None:
            self.auth()

        data = {}
        data["userToken"] = self.userToken
        data["courseName"] = self.courseName
        data["channel"] = channel
        data["telemetry"] = log

        data_json = json.dumps(data, indent=4)
        headers = {"Content-type": "application/json", "Accept": "text/plain"}
        responde = requests.post(URL_PUSH_DATA, data=json.dumps(data), headers=headers)


@click.group()
@click.option("--debug", "-b", is_flag=True, help="Enables verbose mode.")
@click.pass_context
def cli(ctx, debug):
    pass


@click.command()
def auth():
    t = telemetry("")
    if t.auth():
        print("All set! Configuration ok")


cli.add_command(auth)

if __name__ == "__main__":
    cli()
