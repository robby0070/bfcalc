from appJar import gui
from datetime import datetime, date
from sortedcontainers import SortedDict
import numpy as np
import random

import os 
import json
    
measurements = [
	"peso",
	"bicipite",
	"tricipite",
	"pettorale",
	"scapola",
	"addome",
	"ileo",
	"coscia",
	"ginocchio",
]

results = [
	"P6",
	"PU",
	"Pollock",
	"BM",
	"BM%",
	"BF",
	"BF%",
]

clients = SortedDict()
currentClient = ""
currentDate = ""
dateFormat = "%Y-%m-%d"

disableChangeDate = False

def findValue (filename, value, age) :
	with open(filename, 'r') as file :
		file.readline()
		for line in file:
			if abs(float(line[:line.find(';')]) - value) < 0.1 :
				values = line.split(';')
				return float(values[age - 5])
	return 0

def calcValues(date) :
	## getting entries ##
	CM = clients[currentClient]["measurements"][date.strftime(dateFormat)]

	filename = "tables/"
	filename += "maschi_" if clients[currentClient]["sex"] == "M" else "femmine_"

	## calculating age ##
	birth = datetime.strptime(clients[currentClient]["date-birth"], dateFormat)
	age = date.year - birth.year - ((date.month, date.day) < (birth.month, birth.day))

	## calculationg pu and p6 values ##
	pu = CM["data"]["ileo"]
	media_icg = (CM["data"]["ileo"] + CM["data"]["coscia"] + CM["data"]["ginocchio"]) / 3.
	p6 = CM["data"]["bicipite"] + CM["data"]["tricipite"] + CM["data"]["scapola"] + media_icg
	CM["results"]["PU"]= findValue(filename + "pu.csv", pu, age)
	CM["results"]["P6"] = findValue(filename + "p6.csv", p6, age)

	## calculating pollock ##
	if clients[currentClient]["sex"] == "M" :
		pollock_sum = CM["data"]["pettorale"] + CM["data"]["addome"] + CM["data"]["coscia"]
		CM["results"]["Pollock"] = 495 / (1.1093800 - 0.0008267 * pollock_sum + \
			0.0000016 * pollock_sum * pollock_sum - 0.0002574 * age) - 450
	else :
		pollock_sum = CM["data"]["addome"] + CM["data"]["ileo"] + CM["data"]["tricipite"]
		CM["results"]["Pollock"] = 495 / (1.0902369 - 0.0009379 * pollock_sum + \
			0.0000026 * pollock_sum * pollock_sum - 0.00000979 * age) - 450
	
	## caclulating BF and BM ##	
	CM["results"]["BF%"] = (CM["results"]["PU"] + CM["results"]["P6"] + CM["results"]["Pollock"]) / 3.
	CM["results"]["BM%"] = 100 - CM["results"]["BF%"]
	CM["results"]["BF"] = CM["data"]["peso"] / 100 * CM["results"]["BF%"]
	CM["results"]["BM"] = CM["data"]["peso"] / 100 * CM["results"]["BM%"]
	
	for i, value in CM["results"].items() :
		CM["results"][i] = round(value, 2)

def updateMeasurements() :
	app.clearListBox("listbox-clients", False)
	for client in clients :
		app.addListItem("listbox-clients", client)

def updateMeasurements() :
	app.clearListBox("listbox-measurements", False)
	for date in clients[currentClient]["measurements"] :
		app.addListItem("listbox-measurements", date)

def updateResults() :
	for r in results :
		app.setLabel("label-" + r + "-value", \
			clients[currentClient]["measurements"][currentDate]["results"][r])

def save(path) :
	with open(path, "w") as file :
		json.dump(clients, file, indent=4)

def toolbar(tool) :
	if "SAVE" in tool :
		save("clients.json")
	elif tool == "GRAPH" :
		with app.subWindow("subwindow-graph") :
			fig.clf()
			plt = fig.add_subplot(111)
			plt.plot(getDates(), getPlots()["BF%"])
			plt.plot(getDates(), getPlots()["peso"])
			plt.plot(getDates(), getPlots()["BM"])
			plt.set_title(currentClient)
			plt.set_ylabel('percentuale')
			app.refreshPlot("fig1")
		app.showSubWindow("subwindow-graph")

def updateClients() :
	app.clearListBox("listbox-clients", False)
	for client in clients :
			app.addListItem("listbox-clients", client)

def load(filename) :
	global clients
	global currentClient
	with open(filename, "r") as file :
		clients = json.load(file, object_pairs_hook=SortedDict)
	currentClient = list(clients.keys())[0]
	
def selectClient() :
	global currentClient
	global disableChangeDate
	selected = app.getListBox("listbox-clients")
	if selected == [] : 
		return False
	currentClient = selected[0]
	app.setEntry("entry-name", currentClient, False)
	disableChangeDate = True
	app.setOptionBox("optionbox-sex", clients[currentClient]["sex"])
	birth_date = datetime.strptime(clients[currentClient]["date-birth"], dateFormat)
	app.setDatePicker("datepicker-birth", birth_date)
	disableChangeDate = False
	updateMeasurements()
	return True

def selectMeasurement() :
	global currentDate
	selected = app.getListBox("listbox-measurements")
	if selected == [] :
		return False
	currentDate = selected[0]

	for m in measurements:
		app.setEntry("numeric-" + m + "-input", \
			clients[currentClient]["measurements"][currentDate]["data"][m], False)
	updateResults()	

def newClient() :
	global clients
	global currentClient 
	prefix, i = "client", 0
	while True: 
		client = prefix + str(i)
		i += 1
		if not client in clients :
			break

	clients[client] = {
		"date-birth": "2000-01-01",
		"measurements": SortedDict(),
		"sex": "M",
	}
	currentClient = client
	updateClients()
	app.selectListItem("listbox-clients", currentClient)

def delClient() :
	clients.pop(currentClient)
	updateClients()

def newMeasurement() :
	global clients
	global currentDate
	d = date.today()
	currentDate = d.strftime(dateFormat)
	clients[currentClient]["measurements"][currentDate] = \
		{
			"data" : SortedDict((key, 0) for key in measurements),
			"results" : SortedDict((key, 0) for key in results) 
		}
	updateMeasurements()
	app.selectListItem("listbox-measurements", currentDate)

def delMeasurement() :
	clients[currentClient]["measurements"].pop(app.getListBox("listbox-measurements")[0])
	updateMeasurements()

def changeName() :
	global currentClient
	name = app.getEntry("entry-name")
	clients[name] = clients.pop(currentClient)
	app.setListItem("listbox-clients", currentClient, name)
	currentClient = name 
	updateClients()

def changeSex() :
	global clients
	if disableChangeDate :
		return False

	clients[currentClient]["sex"] = \
	app.getOptionBox("optionbox-sex")
	for measurement in clients[currentClient]["measurements"] :
		calcValues(datetime.strptime(measurement, dateFormat))
	updateResults()
	return True


def changeDate() :
	global currentDate
	newDate = app.getDatePicker("datepicker-measurement")
	newStringDate = newDate.strftime(dateFormat)
	clients[currentClient]["measurements"][newStringDate] = \
		clients[currentClient]["measurements"].pop(currentDate)
	app.setListItem("listbox-measurements", currentDate, newStringDate)
	calcValues(newDate)
	currentDate = newStringDate 
	updateResults()

def changeBirth() :
	global clients
	if disableChangeDate :
		return False

	clients[currentClient]["date-birth"] = \
		app.getDatePicker("datepicker-birth").strftime(dateFormat)
	for measurement in clients[currentClient]["measurements"] :
		calcValues(datetime.strptime(measurement, dateFormat))
	updateResults()
	return True

def updateValue(name) :
	clients[currentClient]["measurements"][currentDate]["data"][name.split('-')[1]] = \
		app.getEntry(name) if app.getEntry(name) != None else 0
	calcValues(datetime.strptime(currentDate, dateFormat))
	updateResults()

with gui("developing", "1200x600", stretch='both', sticky='news', font=18) as app :
	load("clients.json")
	tools = ["SAVE", "GRAPH"]
	app.addToolbar(tools, toolbar, findIcon=True)
	app.setToolbarImage("SAVE", "img/save.png")
	app.setToolbarImage("GRAPH", "img/graph.gif")


	with app.panedFrame("clients") :
		app.setSticky('news')
		app.addListBox("listbox-clients", colspan=2)
		app.setStretch('column')
		app.addNamedButton("+", "button-clients-plus", newClient)
		app.addNamedButton("-", "button-clients-minus", delClient, app.gr() - 1, 1)

		with app.panedFrame("anagrafe") :
			app.setStretch('column')
			app.setSticky("nwe")
			app.addEntry("entry-name")
			app.setSticky("ne")
			app.setEntryChangeFunction("entry-name", changeName)
			app.setSticky("nw")
			app.optionBox("optionbox-sex", ["M", "F"], 0, 1)
			app.setOptionBoxChangeFunction("optionbox-sex", changeSex)
			app.addDatePicker("datepicker-birth", colspan=2)
			app.setDatePickerRange("datepicker-birth", 1950)
			app.setDatePickerChangeFunction("datepicker-birth", changeBirth)

			app.setSticky('news')
			app.setStretch('row')
			app.addListBox("listbox-measurements", colspan=2)
			app.setStretch('column')
			app.addNamedButton("+", "button-measurements-plus", newMeasurement)
			app.addNamedButton("-", "button-measurements-minus", delMeasurement, app.gr() - 1, 1)

			with app.panedFrame("subwindow-measurements", vertical=True) :
				app.setSticky("ew")
				app.setStretch("column")
				app.addDatePicker("datepicker-measurement")
				app.setDatePickerRange("datepicker-measurement", 1990)
				app.setDatePicker("datepicker-measurement", date.today())
				app.setDatePickerChangeFunction("datepicker-measurement", changeDate)
				with app.panedFrame("measurements") :
					app.setSticky("w")
					i = 0
					for measurement in measurements :
						app.addLabel("label-" + measurement + "-input", measurement.capitalize(), i, 0)
						app.addNumericEntry("numeric-" + measurement + "-input", i, 1)
						app.setEntryChangeFunction("numeric-" + measurement + "-input", updateValue)
						i += 1
					with app.panedFrame("results") :
						app.setSticky("w")
						i = 0
						for r in results :
							app.addLabel("label-" + r, r, i, 0)
							app.addLabel("label-" + r + "-value", "	", i, 1)
							app.setLabelBg("label-" + r + "-value", "white")
							app.setLabelRelief("label-" + r + "-value", "sunken")
							i += 1

			app.setPaneSashPosition(10, "clients")
			app.setListBoxSubmitFunction("listbox-clients", selectClient)
			app.setListBoxSubmitFunction("listbox-measurements", selectMeasurement)
		updateClients()
		updateMeasurements()

	with app.subWindow("subwindow-graph") :
		def getDates() :
			return [ i for i in clients[currentClient]["measurements"] ]

		def getPlots() :
			c = clients[currentClient]["measurements"]
			return {
				"BF%" : [ i["results"]["BF%"] for i in c.values() ],
				"BM" : [ i["results"]["BM"] for i in c.values() ],
				"peso" : [ i["data"]["peso"] for i in c.values() ],
			}
		fig = app.addPlotFig("fig1")
