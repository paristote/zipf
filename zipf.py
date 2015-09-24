import subprocess
import os
import re
import collections
import sys
import shutil
from flask import Flask, redirect, render_template, url_for, request

app=Flask(__name__)

class WordCounter(dict):
    def __missing__(self, key):
        return 0

WORD_DIC=WordCounter()
VALID_WORD_PATTERN=re.compile('^[a-zA-Z]+$')
WORD_SEPARATOR=re.compile('[:_=\'"\s\(\)]')

# Routes

@app.route("/")
def home():
	return render_template("index.html")

@app.route("/zipf", methods=['POST'])
def zipf():
	orga=request.form['orga']
	repo=request.form['repo']
	gitUrl="https://github.com/{0}/{1}.git".format(orga, repo)
	cloneFolder="{0}/{1}".format(orga, repo)
	gitExport(gitUrl, cloneFolder)
	walkProject(cloneFolder)
	return redirect(url_for("result"))

@app.route("/result")
def result():
	result=collections.Counter(WORD_DIC).most_common(50)
	return render_template("result.html", result=result)

# ZIPF

def gitExport(gitUrl, cloneFolder):
	if os.path.exists(cloneFolder):
		shutil.rmtree(cloneFolder)
	subprocess.check_call(["git", "clone", "-q", "--depth=1", gitUrl, cloneFolder])
	subprocess.check_call(["rm", "-rf", cloneFolder+"/.git"])

def isValid(word):
	return re.match(VALID_WORD_PATTERN, word)

def walkProject(cloneFolder):
	for root, dirs, files in os.walk(cloneFolder):
		for fname in files:
			if fname[0] != ".":
				countWordsInFile(os.path.join(root,fname))

def countWordsInFile(fileName):
	if os.path.exists(fileName):
		with open(fileName, 'r') as f:
			for line in f:
				words=re.split(WORD_SEPARATOR, line)
				for word in words:
					if isValid(word):
						WORD_DIC[word]+=1

	
if __name__ == "__main__":
    app.run(debug=True)

