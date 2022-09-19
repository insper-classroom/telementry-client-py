#!/usr/bin/env python3

import click
import configparser
import webbrowser
import requests
import json
import pathlib
import os
import pickle
import signal
import time

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".telemetry.ini")
QUEUE_FILE = os.path.join(os.path.expanduser("~"), ".telemetry.obj")

URL_BASE = "http://3.83.45.177:80/"
#URL_BASE = "http://localhost:3000/"
URL_LOGIN = URL_BASE + "student/login"
URL_GET_USER = URL_BASE + "student/info?"
URL_PUSH_DATA = URL_BASE + "student/push"


class Queue:
    def __init__(self, file):
        self.file = file
        self.queue = self.open()

    def open(self):
        if os.path.exists(self.file):
            with open(self.file, "rb") as f:
                return pickle.load(f)
        else:
            return list()

    def put(self, item):
        self.queue.append(item)

    def len(self):
        return len(self.queue)

    def read(self):
        return self.queue.pop(0)

    def dump(self):
        with open(self.file, "wb+") as f:
            pickle.dump(self.queue, f)


class telemetry:
    def __init__(self, courseName):
        self.courseName = courseName
        self.queue = Queue(QUEUE_FILE)
        self.userToken = ""
        self.statusOk = "O"
        self.statusFail = "F"
        self.statusNone = "N"
        self.TIMEOUT = 5
        signal.signal(signal.SIGALRM, self.interrupted)

    def checkToken(self, token):
        return True if len(token) == 64 else False

    def interrupted(signum, frame):
        signal.signal(signal.SIGALRM, interrupted)

    def prompToken(self):
        try:
            print("Past the token provide by the website after autentication")
            return input("Token:")
        except:
            return

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
        response = requests.get(URL_GET_USER + "token=" + token, timeout=self.TIMEOUT)
        if response.ok != 200:
            user = json.loads(response.content)
            return user[0]["fields"]
        else:
            return None

    def getStudentFromEmail(self, email):
        response = requests.get(URL_GET_USER + "email=" + email, timeout=self.TIMEOUT)
        if response.ok:
            user = json.loads(response.content)
            return user[0]["fields"]
        else:
            return None

    def getGitEmail(self):
        try:
            return os.popen("git config user.email").read().strip()
        except:
            return None

    def isFromCI(self):
        return True if os.environ.get("CI") == "CI" else False

    def getStudentFromCI(self):
        return os.environ.get("GITHUB_ACTOR")

    def auth(self):

        config = configparser.ConfigParser()
        if config.read(CONFIG_FILE):
            try:  # TODO fazer de outra froma
                token = config["active handout"]["token"]
                if self.checkToken(token):
                    user = self.getStudentFromToken(token)
                if user != None:
                    self.userToken = token
                    return True
            except:
                token = None
        else:
            email = self.getGitEmail()
            if email != None:
                user = self.getStudentFromEmail(email)
                if user != None:
                    self.createConfig(user["token"], user)
                    self.userToken = user["token"]
                    return True

        print("Wrong token, please update")

        webbrowser.open(URL_LOGIN, new=1)

        while True:
            signal.alarm(self.TIMEOUT)
            token = self.prompToken()
            signal.alarm(0)
            if token is not None:
                if self.checkToken(token):
                    user = self.getStudentFromToken(token)
                    if user != None:
                        break
                else:
                    print("Wrong token, please check copy and paste")
            else:
                print("[Timeout] Token not configured, push telemetry to queue")
                self.userToken = None
                return False

        self.createConfig(token, user)
        print("Hello %s" % user["name"])

        self.userToken = token
        return True

    def appendUserConfig(self, data):
        data["userToken"] = self.userToken
        data["courseName"] = self.courseName

    def pushDataToServer(self, data):
        data_json = json.dumps(data, indent=4)
        headers = {"Content-type": "application/json", "Accept": "text/plain"}
        try:
            response = requests.post(
                URL_PUSH_DATA,
                data=json.dumps(data),
                headers=headers,
                timeout=self.TIMEOUT,
            )
            return response.ok
        except:
            print("[ERRO] telemetry timeout")
            return False

    def push(self, log, name="", status="N", channel=0):
        fail = False

        if self.userToken == "":
            self.auth()

        data = {}
        data["channel"] = channel
        data["name"] = name
        data["status"] = status
        log["CI"] = self.isFromCI()
        log["ts"] = time.time()
        data["telemetry"] = log
        self.queue.put(data)

        if self.userToken != None:
            for i in range(self.queue.len()):
                data = self.queue.read()
                self.appendUserConfig(data)
                if not self.pushDataToServer(data):
                    self.queue.put(data)
                    break

        self.queue.dump()


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
