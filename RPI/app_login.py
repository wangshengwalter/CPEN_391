import json
import tkinter as tk
import requests
from PIL import ImageTk, Image
import os
import interface
import renderingUtil
import database
import multiprocessing as mp
from functools import partial
import ctypes
import testyboi as testy
import time
import Camera.camera as camera
import Camera.camera2 as camera2
import cv2

# import functions and classes
import googleVision

# current working directory
workingDir = os.path.dirname(os.path.abspath(__file__))
backgroundColour = "#263D42"

pictureExists = False
newPicture = False
acceptNextImage = True
objectImg = "/images/download.jpg"
buffer = None
imageQueue = mp.Queue()
ackQueue = mp.Queue()
customerIdQueue = mp.Queue()
loginSuccessQueue = mp.Queue()


class App(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.attributes('-fullscreen', True)

        self.canvas = tk.Canvas(self, bg=backgroundColour)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Set up Menu
        MainMenu(self)

        # Set up Frames
        container = tk.Frame(self.canvas)
        container.place(relwidth=0.75, relheight=0.85, relx=0.1, rely=0.1)
        # container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for F in (LandingPage, RegularItems, CustomItems, LoginPage):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(LoginPage)

    def show_frame(self, context):
        frame = self.frames[context]
        frame.tkraise()

class LoginPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        label = tk.Label(self, text="Welcome to Ingredients Decoder")
        label.config(font=('helvetica', 30))
        label.pack(padx=10, pady=10)

        guest_login = tk.Button(self, text="Log in as a guest", height = 2, font=('helvetica', 15), command= lambda: self.loginAsGuest())
        guest_login.pack()

        bt_login = tk.Button(self, text="Log in using bluetooth", height = 2, font=('helvetica', 15), command=lambda: self.loginBT())
        bt_login.pack()

        self.loginStatus = tk.Label(self, text="Please log in to continue", height = 2, font=('helvetica', 15))
        self.loginStatus.pack()
        self.continue_button = tk.Button()
        self.controllor = controller

    def loginAsGuest(self):
        renderingUtil.refresh(self.loginStatus)
        self.loginStatus = tk.Label(self, text="You have successfully loged in as guest", height = 2, font=('helvetica', 15))
        self.loginStatus.pack()
        renderingUtil.refresh(self.continue_button)
        self.continue_button = tk.Button(self, text="Continue", height = 2, font=('helvetica', 15), command= lambda: self.continueToLanding())
        self.continue_button.pack()

    def loginBT(self):
        #if loginSuccess == True:
        textInput = "Browsing for a bluetooth login.... "
        renderingUtil.refresh(self.loginStatus)
        self.loginStatus = tk.Label(self, text=textInput, height = 2, font=('helvetica', 15))
        self.loginStatus.pack()
        renderingUtil.refresh(self.continue_button)

    def continueToLanding(self):
        #go to landing page
        self.controllor.show_frame(LandingPage)
        #reset login status
        renderingUtil.refresh(self.loginStatus)
        self.loginStatus = tk.Label(self, text="Please log in to continue", height = 2, font=('helvetica', 15))
        self.loginStatus.pack()
        #delete continue button
        renderingUtil.refresh(self.continue_button)


class LandingPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        label = tk.Label(self, text="You have successfully loged in")
        label.config(font=('helvetica', 30))
        label.pack(padx=10, pady=10)

        regular_page = tk.Button(self, text="Regular Items", height = 2, font=('helvetica', 15), command=lambda: controller.show_frame(RegularItems))
        regular_page.pack()

        custom_page = tk.Button(self, text="Custom Items", height = 2, font=('helvetica', 15), command=lambda: controller.show_frame(CustomItems))
        custom_page.pack()

        user_list = tk.Button(self, text="View personalized list", height = 2, font=('helvetica', 15),
                              command=lambda: self.show_plist(LandingPage, controller))
        user_list.pack()

        login_page = tk.Button(self, text="Log out", height = 2, font=('helvetica', 15), command=lambda: controller.show_frame(LoginPage))
        login_page.pack()

        self.user_list = tk.Label()

        # why gif not running~
        self.img = ImageTk.PhotoImage(Image.open(workingDir + "/images/cat.gif"))
        welcomeImg = tk.Label(self, image=self.img)
        welcomeImg.pack()

    def show_plist(self, context, controller):
        URL = "http://52.138.39.36:3000/plist"
        userName = 'customer1'
        PARAMS = {'username': 'customer1'}
        response = requests.post(url=URL, json=PARAMS)
        resJson = response.json()
        userList = []

        renderingUtil.refresh(self.user_list)
        for element in resJson['message']:
            userList.append(element["p"])
        str1 = ""
        for element in userList:
            str1 += element.lower()
            str1 += " "
        self.user_list = tk.Label(controller.frames[context], text='Here is your list: ' + str1, font=('helvetica', 15))
        self.user_list.pack(padx=10, pady=10)


class CommonDisplay:
    def __init__(self, controller, parent, message, scanFunction, *args, **kwargs):
        self.infoButtonList = []
        self.counter = 0
        self.itemList = [None]*20 #20 items max
        self.ingredientsList = [None]*20
        self.subcanvas = tk.Canvas()

        readImg = renderingUtil.resizeImage("/images/Capture.jpg")
        self.img = ImageTk.PhotoImage(readImg)
        self.alert = tk.Label()

        # CommonDisplay.__init__(self)

        label = tk.Label(self, text=message)
        label.config(font=('helvetica', 30))
        label.pack(padx=10, pady=10)
        scan_items = tk.Button(self, text="Check Ingredients", height = 2, font=('helvetica', 15),
                               command=lambda: scanFunction("customer1"))

        scan_items.pack()
        start_page = tk.Button(self, text="Back to Home Page", height = 2, font=('helvetica', 15), command=lambda: self.backToHomePage(controller))
        start_page.pack()

        self.instruction = tk.Label(self, text="Place item inside box with ingredients list facing camera", font=('helvetica', 15))
        self.instruction.pack()

        self.promptLabel = tk.Label(self, image=self.img)
        self.promptLabel.pack()

    def backToHomePage(self, controller):
        for i in self.itemList:
            if i != None:
                renderingUtil.refresh(i)
        for j in self.ingredientsList:
            if j != None:
                renderingUtil.refresh(j)
        renderingUtil.refresh(self.subcanvas)
        renderingUtil.refresh(self.alert)
        controller.show_frame(LandingPage)

    def printIntersection(self, warning, matchingArr):
        renderingUtil.refresh(self.alert)
        if matchingArr == "notOCR":
            self.alert = tk.Label(self, text="No ingredients text detected", font=('helvetica', 15))
            self.alert.pack()
            return
        if matchingArr == "notRecognition":
            self.alert = tk.Label(self, text="Not recognized as a store custom item. Maybe try regular item instead?", font=('helvetica', 15))
            self.alert.pack()
            return
        if not matchingArr:
            self.alert = tk.Label(self, text="No harmful ingredients detected", font=('helvetica', 15))
            self.alert.pack()
        else:
            warning = "We found the following " + warning + " that you might not want: \n "
            for element in matchingArr:
                warning += element + ", "
            warning = warning[:-2]
            self.alert = tk.Label(self, text=warning, font=('helvetica', 15))
            self.alert.pack()

    def CheckIngredientsOCR(self, username):
        if self.noImg():
            return
        # get the text from OCR
        responseOCR = googleVision.requestOCR(objectImg)
        # get user plist
        userList = database.Get_Personal_List(username)
        # get the matching array
        matchingArr = googleVision.getMatchingArr(responseOCR, userList)
        self.printIntersection("ingredients matching your personal list", matchingArr)

    def printIngredients(self, subcanvas, itemIngredients, i):
        self.ingredientsList[i] = tk.Label(subcanvas, text=itemIngredients, borderwidth=2, relief="solid", height=2,
                                           font=('helvetica', 15))
        self.ingredientsList[i].grid(row=i, column=1)

    def CheckIngredientsRecognition(self, username):
        if self.noImg():
            return
        # get the text from OCR
        tags_array = googleVision.requestRecognition(objectImg)
        ingredients_array = database.Get_Custom_Ingredients(tags_array)

        self.subcanvas = tk.Canvas(app.canvas, height=100000000)
        self.subcanvas.pack(padx=(50, 50), pady=(550, 0))

        # init ingredients list array
        max = 0
        for i in range(0, len(tags_array)):  # Rows
            if ingredients_array[i] != '0':
                ahoy = partial(self.printIngredients, self.subcanvas, ingredients_array[i], i)
                self.itemList[i] = tk.Button(self.subcanvas, text=tags_array[i], borderwidth=2, relief="solid", height = 2, font=('helvetica', 15),
                                            command=ahoy)
                self.itemList[i].grid(row=i, column=0, padx=10, sticky="W")
                if self.itemList[i].winfo_width() > max:
                    max = self.itemList[i].winfo_width()
                    #ingredients_list = tk.Label(subcanvas, text=ingredients_array[i], borderwidth=2, relief="solid")
                    #ingredients_list.grid(row=i, column=1)
        userList = database.Get_Personal_List(username)
        # get the matching array
        matchingArr = googleVision.getMatchingArr(ingredients_array, userList)
        self.printIntersection("ingredients matching your personal list", matchingArr)

    def CheckHarmfulOCR(self):
        if self.noImg():
            return
        responseOCR = googleVision.requestOCR(objectImg)
        harmfulList = database.Get_Harmful_List()
        matchingArr = googleVision.getMatchingArr(responseOCR, harmfulList)
        self.printIntersection("generally harmful ingredients", matchingArr)

    def CheckHarmfulRecognition(self):
        if self.noImg():
            return
        responseRec = googleVision.requestRecognition(objectImg)
        responseRec = database.Get_Custom_Ingredients(responseRec)
        harmfulList = database.Get_Harmful_List()
        matchingArr = googleVision.getMatchingArr(responseRec, harmfulList)
        self.printIntersection("generally harmful ingredients", matchingArr)

    def MakeAcceptNextImage(self):
        global acceptNextImage
        acceptNextImage = True
        actualPoll()

    def noImg(self):
        if objectImg is None:
            self.alert = tk.Label(self,
                                  text="No object detected, or image has not loaded yet. \n PLease wait for image of object to show up before attempting scan",
                                  font=('helvetica', 15))
            self.alert.pack()
            return True
        return False


class RegularItems(tk.Frame, CommonDisplay):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        CommonDisplay.__init__(self, message="Scan regular items here", scanFunction=self.CheckIngredientsOCR,
                               parent=parent, controller=controller)


class CustomItems(tk.Frame, CommonDisplay):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        CommonDisplay.__init__(self, message="Scan store custom items here",
                               scanFunction=self.CheckIngredientsRecognition, parent=parent, controller=controller)


class MainMenu:
    def __init__(self, master):
        menubar = tk.Menu(master)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Exit", command=master.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        master.config(menu=menubar)


app = App()


def loadProcessedImage(frame):
    # tell users to make google vision call
    global app
    renderingUtil.refresh(app.frames[frame].instruction)
    try:
        tryOpen = Image.open(workingDir + objectImg)
        app.frames[frame].instruction = tk.Label(app.frames[frame], text="Your item is ready to be scanned", font=('helvetica', 15))
    except OSError:
        print('cannot open')
        app.frames[frame].instruction = tk.Label(app.frames[frame], text="Please place an item in front of the camera", font=('helvetica', 15))
    app.frames[frame].instruction.pack()

    # change the image
    renderingUtil.refresh(app.frames[frame].promptLabel)
    readImg = renderingUtil.resizeImage(objectImg)
    app.frames[frame].img = ImageTk.PhotoImage(readImg)
    app.frames[frame].promptLabel = tk.Label(app.frames[frame], image=app.frames[frame].img)
    app.frames[frame].promptLabel.pack()

def bluetoothLogin(frame, customerId):
    global app
    renderingUtil.refresh(app.frames[frame].loginStatus)
    textInput = "you have successfully loged in as " + customerId
    app.frames[frame].loginStatus = tk.Label(app.frames[frame], text=textInput, height = 2, font=('helvetica', 15))
    app.frames[frame].loginStatus.pack()
    renderingUtil.refresh(app.frames[frame].continue_button)
    app.frames[frame].continue_button = tk.Button(app.frames[frame], text="Continue", height = 2, font=('helvetica', 15), command= lambda: app.frames[frame].continueToLanding())
    app.frames[frame].continue_button.pack()

def pollPicture():
    actualPoll()
    app.after(1000, pollPicture)


def actualPoll():
    global app
    global acceptNextImage
    global objectImg
    global imageQueue
    global ackQueue
    global loginSuccess
    global customerId
    if not imageQueue.empty():
        print("not empty")
        imageQueue.get()
        if acceptNextImage:
            loadProcessedImage(RegularItems)
            loadProcessedImage(CustomItems)
            # acceptNextImage = False
        ackQueue.put(True)

    if not loginSuccessQueue.empty():
        success = loginSuccessQueue.get()
        if success == True:
            customerId = customerIdQueue.get()
            bluetoothLogin(LoginPage, customerId)

app.after(3000, pollPicture)
if __name__ == "__main__":
    #producer = mp.Process(target=camera.run, args=(imageQueue, ackQueue))
    producer = mp.Process(target=camera2.run, args=(customerIdQueue, loginSuccessQueue))
    producer.start()
    ackQueue.put(True)
    app.mainloop()

app.mainloop()