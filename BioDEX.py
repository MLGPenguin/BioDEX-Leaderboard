'''
Leaderboard
Score
Users - (ID, Score)
A way to add/deduct score
Sort the leaderboard by highest score
Way to determine what each species is worth (dictionary?)

All of the above in an interface (Enter UserID to get score, etc.) - tkinter.

'''

import sqlite3 as sql
from tkinter import *
from tkinter import messagebox
import datetime
import random

CATCH_OF_THE_DAY_MULTIPLIER = 3
SPECIES_SCORES = {
    "Tree": 10, 
    "Special Tree": 25, 
    "Bush": 5,
    "Bird": 30,
    "Insect": 10,
    "Pelican": 50,
    "Bat": 40,
    "DoDo": 1000
    }

def getRarities():
    '''
    Determines a relative probability for each species dependent on the score received for submitting them as defined 
    in the dictionary SPECIES_SCORES above, 
    This will be removed in a future version when a rarity can be calculated based on global data.
    '''
    global SPECIES_SCORES
    sumProbability = 0
    newProbabilities = {}
    for species in SPECIES_SCORES: sumProbability += (1/SPECIES_SCORES[species])
    for species in SPECIES_SCORES: newProbabilities[species] = ((1/SPECIES_SCORES[species])/sumProbability)
    return newProbabilities

def getRandomSpecies():
    ''' Chooses a random species from the list dependent on rarity '''
    rand = random.random()
    species = getRarities()
    i = 0
    for s in species:
        rand -= species[s]
        if rand <= 0:
            return s
    return None



class database:
    def __init__(self):
        '''Initialises the database connection and creates any non-existing tables.'''
        self.connection = sql.connect("users.sqlite")
        self.executeCommand("CREATE TABLE IF NOT EXISTS scores(id varchar(12), name varchar(12), score int, PRIMARY KEY (id))")
        self.executeCommand("CREATE TABLE IF NOT EXISTS entries(submitter varchar(12), type varchar, points_awarded int, time TIMESTAMP)")

    def executeCommand(self, cmd: str, params: tuple = ()):
        '''Executes a command through the connection'''
        cursor = self.connection.cursor()
        return cursor.execute(cmd, params)

    def contains(self, column: str, value) -> bool:
        '''returns if the given column contains the given value'''
        return self.executeCommand(f"SELECT EXISTS (SELECT 1 FROM scores WHERE {column} = ?)", (value,)).fetchone()[0] == 1
    
    def getHighestScore(self):
        '''returns the highest score in the database'''
        return self.executeCommand("SELECT MAX(score) FROM scores").fetchone()[0]

    def newUser(self, name: str):
        '''Creates a new user if they don't already exist, populates with default values.'''
        score = 0
        id = name.lower()
        if self.contains("id", id):
            return
        self.executeCommand("INSERT INTO scores VALUES (?, ?, ?)", (id, name, score))
        self.connection.commit()

    def newRecord(self, id: str, type: str, points: int, addpoints: bool):
        '''Inserts a new record when a user would submit an image '''
        self.executeCommand("INSERT INTO entries VALUES(?, ?, ?, ?)", (id.lower(), type, points, datetime.datetime.now().replace(microsecond=0)))
        self.connection.commit()
        if addpoints: self.addScore(id, points)

    def setScore(self, name: str, score: int):
        '''Sets the score of the user.'''
        id = name.lower()
        if self.contains("id", id):
            self.executeCommand("UPDATE scores SET score = ? WHERE id = ?", (score, id))
            self.connection.commit()

    def addScore(self, name: str, score: int):
        '''Adds a score to the users existing score.'''
        id = name.lower()
        self.executeCommand("UPDATE scores SET score = score + ? WHERE id = ?", (score, id))
        self.connection.commit()

    def getScore(self, name: str):
        '''Gets the score of the user.'''
        score = self.executeCommand("SELECT Score FROM scores WHERE id = ?", (name.lower(),)).fetchone()
        return score[0] if score != None else None
    
    def getEntries(self, id: str):
        return self.executeCommand("SELECT * FROM entries WHERE submitter = ? ORDER BY time DESC", (id.lower(),)).fetchall()
    
    def getName(self, id: str):
        name = self.executeCommand("SELECT Name FROM scores WHERE id = ?", (id.lower(),)).fetchone()
        return name[0] if name != None else None

    def getLeaderboard(self):
        '''Returns the top 10 entries in the leaderboard'''
        return self.getFullLeaderboard()[0:9]

    def getFullLeaderboard(self):
        '''Returns the entire leaderboard'''
        return self.executeCommand("SELECT Name, Score, id FROM scores ORDER BY Score DESC").fetchall()

    def getLeaderboardPosition(self, name: str):
        '''Gets the position of this user on the leaderboard'''
        placement = 1
        id = name.lower()
        for row in self.getFullLeaderboard():
            if row[2] == id:
                return placement
            placement+=1

    def containsUser(self, name: str) -> bool:
        return self.contains("id", name.lower())

db = database()
currentlyLoggedIn = None

root  =  Tk()  # create root window
root.title("BioDex")
root.maxsize(900,  600)
root.config(bg="red")

# Create left and right frames
leftFrame  =  Frame(root, relief=RIDGE, bd=10, width=200,  height=400,  bg='#cccccc')
leftFrame.pack(side='left',  fill='both',  padx=10,  pady=5,  expand=True)

rightFrame  =  Frame(root, relief=RIDGE, bd=10,  width=650,  height=400,  bg='#cccccc')
rightFrame.pack(side='right',  fill='both',  padx=10,  pady=5,  expand=True)

# Left frame
Label(leftFrame,  text="Catch of the Day!", relief=RIDGE, bd=5, bg='#cccccc', font = '16' ).pack(side='top',  padx=5,  pady=5)
image  =  PhotoImage(file='tree1.png')
originalImage  =  image.subsample(5,5)
Label(leftFrame,  image=originalImage, bg ='#cccccc').pack(fill='both',  padx=5,  pady=5)



#Leaderboard section/right frame
LBlabels = [] 
lbheader = Label(rightFrame,  text='   Leaderboard   ', font='16' )
lbheader.pack(fill='both',  padx=5,  pady=5)
showingLeaderboard = True

def updateLeaderboard():
    '''Fills the leaderboard frame with the top 10 entries.'''
    global LBlabels, currentlyLoggedIn, showingLeaderboard
    showingLeaderboard = True
    it = 1
    position = -1 if currentlyLoggedIn == None or not db.containsUser(currentlyLoggedIn) else db.getLeaderboardPosition(currentlyLoggedIn)
    lbheader.config(text='   Leaderboard   ')
    for entry in db.getLeaderboard():
        color = "red" if it == position else None
        label = Label(rightFrame, text=f"{it}. {entry[0]}: {entry[1]}", font = 10, anchor='w', highlightthickness=2, highlightbackground=color)
        label.pack(fill="both", padx=5, pady=5)
        LBlabels.append(label)
        it+=1

def destroyLabels():
    '''Removes all entries in the leaderboard from the leaderboard frame.'''
    for label in LBlabels:
        label.destroy()

def refreshLeaderboard():
    '''API method for combining the above two methods, as they will be required to be used in tandem often'''
    destroyLabels()
    updateLeaderboard()

def refreshRightFrame():
    global showingLeaderboard
    destroyLabels()
    if showingLeaderboard: updateLeaderboard()
    else: displayEntries()

def displayEntries():
    global currentlyLoggedIn, showingLeaderboard
    showingLeaderboard = False
    if currentlyLoggedIn == None:
        messagebox.showerror("Error", "You must be logged in to do this")
        return
    entries = db.getEntries(currentlyLoggedIn)[0:9]
    lbheader.config(text="   Collected   ")
    if entries == None:
        return
    destroyLabels()
    for entry in entries:
        label = Label(rightFrame, text=f"{entry[1]}: {entry[2]}", font=10, anchor='w')
        label.pack(fill="both", padx=5, pady=5)
        LBlabels.append(label)

updateLeaderboard()

userBar  =  Frame(leftFrame,  width=90,  height=185,  bg='#cc0000')
userBar.pack(side='left',  fill='both',  padx=5,  pady=5,  expand=True)

scoreBar  =  Frame(leftFrame,  width=90,  height=185,  bg='#cc0000')
scoreBar.pack(side='right',  fill='both',  padx=5,  pady=5,  expand=True)


#button function
def clicked():
    '''if button is clicked, print button clicked'''
    print("Button clicked!!")



#display login
def logIn(logOn):
    '''Handles the log-in logic (updating the leaderboard and creating any new accounts)'''
    global currentlyLoggedIn
    logOn = userInput.get()
    if len(logOn) > 12:
        messagebox.showerror('Error', "Your name may not contain more than 12 characters.")
        return
    elif len(logOn) == 0: 
        messagebox.showerror("Error", "You must specify a username.")
        return
    currentlyLoggedIn = logOn
    if not db.containsUser(currentlyLoggedIn):
        db.newUser(currentlyLoggedIn)
    refreshLeaderboard()
    updateScore()
    return messagebox.showinfo('message',f'{db.getName(logOn)} will ' + str(logFun.get()) +'!')

#Log in/off system and entry box lockout
def logOff(event):
    '''Updates logFun variable for use in the logIn function.
    Also controls the Entry box state to block or allow modification based on logged in or not'''
    global logFun
    global userInput
    global log
    global currentlyLoggedIn
    if (logFun.get() == 'Log In'):
        logFun = StringVar(root, value = 'Log Off')
        userInput.config(state = 'disabled')
        return logFun.get() 
    else:
        logFun = StringVar(root, value = 'Log In')
        userInput.config(state = 'normal')
        currentlyLoggedIn = None
        return logFun.get()

#User input for username
#user = StringVar(userBar, value='Enter Username, then press Enter')

userInput = Entry(userBar, justify = 'center')
userInput.insert(END, 'Enter Username')
userInput.bind('<Return>', logIn)
userInput.pack(anchor='n',  padx=5,  pady=3,  ipadx=10)


#Score input for user 
score = StringVar(root, value ='Score')
def updateScore():
    '''Updates the score to match the score of the user whom is currently logged in'''
    global currentlyLoggedIn, score
    newscore = db.getScore(currentlyLoggedIn)
    text = "Score" if newscore == None else "Score: " + str(newscore)
    score.set(text)

#Input for user login system
logFun = StringVar(root, value = 'Log In')

# Displays current User name and score
log = Button(userBar,  text = 'Log In/Off',  command =lambda:[logIn(userInput.get()), logOff(str(logFun.get()))],  relief=RAISED).pack(anchor='n',  padx=5,  pady=3,  ipadx=10)
Label(scoreBar,  textvariable=score, font= '10',  relief=RAISED).pack(anchor='n',  padx=5,  pady=3,  ipadx=10)

def onClickNewCapture():
    global currentlyLoggedIn
    if currentlyLoggedIn == None:
        messagebox.showerror("Error", "You must be logged in to do this.")
        return
    type = getRandomSpecies()
    points = SPECIES_SCORES[type]
    db.newRecord(currentlyLoggedIn, type, points, True)
    messagebox.showinfo("Success", f"Congratulations! You have captured a {type} worth {points} points!")
    refreshRightFrame()

def onClickCollected():
    global showingLeaderboard
    if showingLeaderboard: displayEntries()
    else: refreshLeaderboard()

# Buttons, only triggers a message atm
# TODO change the middle columnn with statistics.
Button(userBar,  text="Collected",  command=onClickCollected).pack(padx=5,  pady=5)
Button(userBar,  text="New Capture",  command=onClickNewCapture).pack(padx=5,  pady=5)
Button(scoreBar,  text="Orientation",  command=clicked).pack(padx=5,  pady=5)
Button(scoreBar,  text="Resize",  command=clicked).pack(padx=5,  pady=5)
Button(scoreBar,  text="Filters",  command=clicked).pack(padx=5,  pady=5)

root.mainloop()
db.connection.close()