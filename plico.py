from appJar import gui
from datetime import datetime, date

import os 
import json


measurements = {"peso": 0, "bicipite": 0, "tricipite": 0, "pettorale": 0, \
	"scapola": 0, "addome": 0, "ileo": 0, "coscia": 0, "ginocchio": 0, }

results = { "p6" : 0, "pu" : 0, "pollock" : 0, "BM" : 0, "BM%" : 0, \
	"BF" : 0, "BF%" : 0, }

currentfile = ""

def findValue (filename, value, age) :
	with open(filename, 'r') as file :
		file.readline()
		for line in file:
			if abs(float(line[:line.find(';')]) - value) < 0.1 :
				values = line.split(';')
				return float(values[age - 5])
	return 0

def calcValues() :
	## getting entries ##	
	for measure in measurements:
		value = app.getEntry("num-" + measure)
		measurements[measure] = value if value != None else 0
	sex = app.getRadioButton("radio-sex")
	filename = "tables/"
	filename += "maschi_" if sex == "Maschio" else "femmine_"

	## calculating age ##
	birth = app.getDatePicker("date-birth")
	today = date.today()
	age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

	## calculationg pu and p6 values ##
	pu = measurements["ileo"]
	media_icg = (measurements["ileo"] + measurements["coscia"] + measurements["ginocchio"]) / 3.
	p6 = measurements["bicipite"] + measurements["tricipite"] + measurements["scapola"] + media_icg
	results["pu"]= findValue(filename + "pu.csv", pu, age)
	results["p6"] = findValue(filename + "p6.csv", p6, age)

	## calculating pollock ##
	if sex == "Maschio" :
		pollock_sum = measurements["pettorale"] + measurements["addome"] + measurements["coscia"]
		results["pollock"] = 495 / (1.1093800 - 0.0008267 * pollock_sum + \
			0.0000016 * pollock_sum * pollock_sum - 0.0002574 * age) - 450
	else :
		pollock_sum = measurements["addome"] + measurements["ileo"] + measurements["tricipite"]
		results["pollock"] = 495 / (1.0902369 - 0.0009379 * pollock_sum + \
			0.0000026 * pollock_sum * pollock_sum - 0.00000979 * age) - 450
	
	## caclulating BF and BM ##	
	results["BF%"] = (results["pu"] + results["p6"] + results["pollock"]) / 3.
	results["BM%"] = 100 - results["BF%"]
	results["BF"] = measurements["peso"] / 100 * results["BF%"]
	results["BM"] = measurements["peso"] / 100 * results["BM%"]

	## setting value ##
	for result in results :
		app.setLabel("label-" + result + "-value", "{:5.2f}".format(results[result]))

def submit (button) :
	if button == "Cancella":
		app.stop()
	else :
		calcValues()
	

def load () :
	with open(currentfile, "r") as file:
		data = json.load(file)
		app.setEntry("entry-name", data["nome"])
		app.setDatePicker("date-birth", datetime.strptime(data["nascita"], "%d-%m-%Y"))
		app.setRadioButton("radio-sex", data["sesso"])

def save () :
	calcValues()
	to_dump = {} 
	if os.path.isfile(currentfile) :
		with open(currentfile, "r") as file:
			to_dump = json.load(file)
	to_dump["nome"]  = app.getEntry("entry-name")
	to_dump["nascita"] = app.getDatePicker("date-birth").strftime("%d-%m-%Y")
	to_dump["sesso"] = app.getRadioButton("radio-sex")

	with open(currentfile, "w") as file :
		to_dump[str(date.today())] = { "misure" : measurements, "risultati" : results } 
		json.dump(to_dump, file, indent=4)

def toolbar(tool) :
	global currentfile
	if "SAVE" in tool :
		if (not currentfile) or (tool == "SAVE AS") :
			currentfile = app.saveBox(fileTypes=[("json", "*.json")], fileExt=".json", asFile=False)
		if currentfile :
			save()

	elif tool == "OPEN" :
		currentfile = app.openBox(fileTypes=[("json", "*.json")], multiple=False, mode='r')
		if currentfile :
			load()

def changesex(radio) :
	if app.getRadioButton("radio-sex") == "Maschio":
		app.enableEntry("num-pettorale")
	else :
		app.disableEntry("num-pettorale")

def printMeasurements(input, i) :
	for measure in measurements :
		app.addLabel("label-" + measure, measure.capitalize(), i, 0)
		if input :
			app.addNumericEntry("num-" + measure, i, 1)
		else :
			app.addLabel("label-" + measure +"-value", "eskere", i, 1)
			app.setLabelRelief("label-" + measure + "-value", "sunken")
		i += 1





def launch(win):
    app.showSubWindow(win)

with gui("developing", "1200x600") as app : 
	app.setFont(20)
	app.setSticky("new")
	app.setExpand("both")

	tools = ["SAVE", "SAVE AS", "OPEN"]
	app.addToolbar(tools, toolbar, findIcon=True)
	app.setToolbarImage("SAVE", "img/save.png")
	app.setToolbarImage("SAVE AS", "img/saveas.png")
	app.setToolbarImage("OPEN", "img/open.png")

	with app.panedFrame("clienti") :
		app.addListBox("clientList", ["Roberto Bertelli", "Luca Bertelli"])
		for i in range(0, 100) :
			app.addListItem("clientList", i)


		with app.panedFrame("anagrafe") :
			app.addEntry("entry-name")
			app.addLabelOptionBox("", ["M", "F"], 0, 1)
			app.addDatePicker("date-birth")
			app.setDatePickerRange("date-birth", 1950)
			app.addListBox("prova-prova", ["prova", "eskere"])
			with app.panedFrame("misura") :
				app.addLabel("eskere", "eskere")
				i = 0
				for result in results :
					app.addLabel("label-" + result, result.capitalize(), i, 0)
					app.addLabel("label-" + result + "-value", "	", i, 1)
					app.setLabelBg("label-" + result + "-value", "white")
					app.setLabelRelief("label-" + result + "-value", "sunken")
				# app.addPieChart("asdfasdf", {"apples":50, "oranges":200, "grapes":75, 
						# "beef":300, "turkey":150}, 0, 2)
					i += 1
				printMeasurements(False, i)

				
	with app.subWindow("one") :
		# with app.labelFrame("Misure") :
			# printMeasurements(True)
		app.addButtons(["Conferma", "Cancella"], submit, colspan=2)