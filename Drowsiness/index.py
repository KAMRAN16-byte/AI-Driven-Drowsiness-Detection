from tkinter import *
import tkinter as tk
from flask import Flask,redirect, url_for,render_template,request
import os

def d_dtcn():
	try:
		root = Tk()
		root.configure(background = "#231f20")
		root.iconphoto(False, tk.PhotoImage(file='site/img/100x100.gif'))
	except Exception as e:
		print(f"Error: {e}")

	def function1(): 
		os.system("python drowsiness_detection.py --shape_predictor shape_predictor_68_face_landmarks.dat")
		exit()

	def function2(): 
		os.system("python drowsiness_detection_marks.py --shape_predictor shape_predictor_68_face_landmarks.dat")
		exit()

	def function3():
		os.system("python EAR_cal.py")
		exit()

	
		
	root.title("DROWSINESS DETECTION ")
	Label(root, text="DROWSINESS DETECTION",font=("Montserrat Bold",20),fg="black",bg="#8dc172",height=2).grid(row=2,rowspan=2,columnspan=5,sticky=N+E+W+S,padx=5,pady=10)
	Button(root,text="Run With Calibration.",font=("Montserrat Bold",20),bg="#92338e",fg='#8dc172',command=function1).grid(row=5,columnspan=5,sticky=W+E+N+S,padx=5,pady=5)
	Button(root,text="Run With 68 Marks. (No Cal)",font=("Montserrat Bold",20),bg="#92338e",fg='#8dc172',command=function2).grid(row=7,columnspan=5,sticky=W+E+N+S,padx=5,pady=5)
	Button(root,text="Run Only Calibration",font=("Montserrat Bold",20),bg="#92338e",fg='#8dc172',command=function3).grid(row=9,columnspan=5,sticky=W+E+N+S,padx=5,pady=5)
	Button(root,text="Exit",font=("Montserrat Bold",20),bg="#8dc172",fg='#92338e',command=root.destroy).grid(row=11,columnspan=5,sticky=W+E+N+S,padx=5,pady=5)



	root.mainloop()