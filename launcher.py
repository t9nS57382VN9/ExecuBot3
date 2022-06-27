import requests
import os
import json
import time
import sys
import msvcrt
import pathlib
from subprocess import Popen

currentpath = str(pathlib.Path(__file__).parent.absolute())

def die(msg):
    print(msg, end = "")
    input()
    sys.exit()

def selectGame():
    print("\n> ", end = "")
    keystroke = msvcrt.getch().decode("utf-8")
    print(keystroke + "\n")

    if keystroke.lower() == "j":
        startGame(int(input("enter the place ID of the game you want to join: ")))
    elif keystroke in quickPlayGames:
        startGame(quickPlayGames[keystroke.lower()])
    else:
        print("invalid option")
        selectGame()
	
def modify_rule(rule_name, state):
    """ Enable/Disable specific rule, 0 = Disable / 1 = Enable """
    state, message = ("yes", "Enabled") if state else ("no", "Disabled")
    subprocess.call(
        f"netsh advfirewall firewall set rule name={rule_name} new enable={state}", 
        shell=True, 
        stdout=DEVNULL, 
        stderr=DEVNULL
    )
    print(f"Rule {rule_name} {message}")

def startGame(placeID):
    modify_rule("RBXSERVER", 0)
    print("checking latest version of ROBLOX... ", end = "")
    version = requests.get("http://setup.roblox.com/version.txt").content.decode("ascii")
    path = os.getenv("LOCALAPPDATA")+"\\Roblox\\Versions\\"+version
    print("done! ("+version+")")

    if not os.path.exists(path):
        print("updating ROBLOX, please wait... ", end = "")
        bootstrapper = requests.get("http://setup.roblox.com/RobloxPlayerLauncher.exe")
        open(currentpath+"\\RobloxPlayerLauncher.exe", "wb").write(bootstrapper.content)
        os.system('"'+currentpath+'\\RobloxPlayerLauncher.exe" -install')
        print("done!")

    print("fetching CSRF token... ", end = "")
    req = requests.post(
        "https://auth.roblox.com/v1/authentication-ticket",
        headers = {"Cookie": ".ROBLOSECURITY="+config['.ROBLOSECURITY']}
    )
    csrf = req.headers['x-csrf-token']
    print("done!")

    print("fetching authentication ticket... ", end = "")
    req = requests.post(
        "https://auth.roblox.com/v1/authentication-ticket",
        headers =
        {
            "Cookie": ".ROBLOSECURITY="+config['.ROBLOSECURITY'],
            "Origin": "https://www.roblox.com",
            "Referer": "https://www.roblox.com/",
            "X-CSRF-TOKEN": csrf
        }
    )

    if(len(req.content) > 2):
        die("failed!\n\ncould not fetch authentication ticket - check that your .ROBLOSECURITY cookie is valid")

    ticket = req.headers['rbx-authentication-ticket']
    print("done!")

    print("\nstarting ROBLOX... ")

    if config['LaunchMode'] == "RobloxBootstrapper":
        location = path+"\\RobloxPlayerLauncher.exe"
        args = "roblox-player:1+launchmode:play+gameinfo:{ticket}+launchtime:{timestamp}+placelauncherurl:https%3A%2F%2Fassetgame.roblox.com%2Fgame%2FPlaceLauncher.ashx%3Frequest%3DRequestGame%26placeId%3D{placeID}%26isPlayTogetherGame%3Dfalse"
    elif config['LaunchMode'] == "DirectLaunch":
        location = path+"\\RobloxPlayerBeta.exe"
        args = "--play -a https://auth.roblox.com/v1/authentication-ticket/redeem -t {ticket} -j https://assetgame.roblox.com/game/PlaceLauncher.ashx?request=RequestGame&placeId={placeID}&isPlayTogetherGame=false --launchtime={timestamp}"

    modify_rule("RBXSERVER", 1)
    Popen([location, args.format(ticket = ticket, timestamp = '{0:.0f}'.format(round(time.time() * 1000)), placeID = placeID)])

    time.sleep(5)

os.system("cls")
print("ROBLOX desktop launcher - who needs a web browser?\n")

if not os.path.exists(currentpath+"\\config.json"):
	die("could not find config.json, is it in the same folder as the python script?")

config = json.loads(open(currentpath+"\\config.json", "r").read())

if "!!!" in config['.ROBLOSECURITY']:
    die("please configure your .ROBLOSECURITY cookie in config.json - you can obtain it using a browser cookie editor")

if not config['LaunchMode'] in ["RobloxBootstrapper", "DirectLaunch"]:
    die("LaunchMode option is invalid - configure it in config.json to be either 'RobloxBootstrapper' or 'DirectLaunch'")

if config['QuickPlay']:
    print("choose a game to play:")
    quickPlayGames = {}
    for game in config['QuickPlay']:
        quickPlayGames[game['KeyIndex']] = game['ID']
        print("[{0}] {1}".format(game['KeyIndex'], game['Name']))

print("\n[j] Join via place ID")

#selectGame()

from http.server import BaseHTTPRequestHandler, HTTPServer
import time

hostName = "136.244.107.30"
serverPort = 8080

from urllib.parse import urlparse

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        query = urlparse(self.path).query
        query_components = dict(qc.split("=") for qc in query.split("&"))
        api = query_components["api"]
        if api == "requestJoin":
            placeID = query_components["placeid"]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes("<html><head><title>https://pythonbasics.org</title></head>", "utf-8"))
            self.wfile.write(bytes("<p>Request: %s</p>" % self.path, "utf-8"))
            self.wfile.write(bytes("<body>", "utf-8"))
            self.wfile.write(bytes("<p>This is an example web server.</p>", "utf-8"))
            self.wfile.write(bytes("</body></html>", "utf-8"))
            startGame(int(placeID))

if __name__ == "__main__":        
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
