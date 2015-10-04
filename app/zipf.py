import subprocess
import os
import re
import collections
import sys
import shutil
import urllib
import urlparse
from flask import Flask, redirect, render_template, url_for, request

app=Flask(__name__)

class WordCounter(dict):
    def __missing__(self, key):
        return 0

# Debug mode True or False
DEBUG=(len(sys.argv) >= 2 and "debug"==sys.argv[1])
# Where all analyzed repos are cloned
TEMP_FOLDER="../clones"
# Pattern to identify a valid word: only letters, 2 or more times
VALID_WORD_PATTERN=re.compile('^[a-zA-Z]{2,}$')
# Pattern to separate words in a line: any of : _ = ' " ( ) and whitespace chars
WORD_SEPARATOR=re.compile('[:_=\'"\s\(\)]')

# Error codes
ERR_EMPTY_ORGA_REPO=10
ERR_ORGA_REPO_DONT_EXIST=11

# Routes

@app.route("/")
def home():
	return render_template("index.html")

@app.route("/zipf", methods=['POST'])
def zipf():
	# Prepare variables
	orga=request.form['orga']
	repo=request.form['repo']
	logd("GitHub organization: "+orga)
	logd("GitHub repository  : "+repo)
	if len(orga) == 0 or len(repo) == 0 :
		return redirect(url_for("error", err=ERR_EMPTY_ORGA_REPO))

	gitUrl="https://github.com/{0}/{1}.git".format(orga, repo)
	cloneFolder="{0}/{1}/{2}".format(TEMP_FOLDER, orga, repo)

	# Clone the repository
	gitCloneSuccess=gitExport(gitUrl, cloneFolder)
	if not gitCloneSuccess:
		return redirect(url_for("error", err=ERR_ORGA_REPO_DONT_EXIST))

	# Get the list of all files in the repository
	files=walkProject(cloneFolder)

	# Count each word occurrences
	wordCount=WordCounter()
	for f in files:
		countWordsInFile(f, wordCount)

	# Keep only the top 50 words and order them desc
	mostCommon=collections.Counter(wordCount).most_common(50)

	# Transform the words dic into key=value url query string
	words=urllib.urlencode(mostCommon)
	return redirect(url_for("result", orga=orga, repo=repo, words=words))

@app.route("/result/<orga>/<repo>/<words>")
def result(orga, repo, words):
	# Transform the query string back into a dictionary of tuples (word, occurrences)
	result=urlparse.parse_qsl(words)
	return render_template("result.html", orga=orga, repo=repo, result=result)

@app.route("/error/<err>")
def error(err):
	return render_template("index.html", error=err)

# ZIPF

# Clone the GitHub repo and delete all .git folders
# Return False if the git command failed
# Return True otherwise, eg if the destination folder already exists
def gitExport(gitUrl, cloneFolder):
	if os.path.exists(cloneFolder):
		return True
	try:
		subprocess.check_call(["git", "clone", "-q", "--depth=1", gitUrl, cloneFolder])
	except subprocess.CalledProcessError as cpe:
		logd("Command failed "+str(cpe.cmd))
		return False
	try:
		subprocess.check_call(["rm", "-rf", cloneFolder+"/.git"])
	except subprocess.CalledProcessError as cpe:
		logd("Command failed "+str(cpe.cmd))
	return True

# True if the given string is a valid word
def isValid(word):
	return re.match(VALID_WORD_PATTERN, word)

# Walk through all folders and return a list of file paths
def walkProject(cloneFolder):
	res=set()
	for root, dirs, files in os.walk(cloneFolder):
		for fname in files:
			if fname[0] != ".":
				res.add(os.path.join(root,fname))
	return res

# Open the given file, then parse each line to count each word number of occurrence
# The result is added to the given WordCounter
def countWordsInFile(fileName, wc):
	if os.path.exists(fileName):
		with open(fileName, 'r') as f:
			for line in f:
				words=re.split(WORD_SEPARATOR, line)
				for word in words:
					if isValid(word):
						wc[word.lower()]+=1

# Print a debug log message
def logd(message):
	if DEBUG:
		print "[DEBUG] " + str(message)

# Delete the folder with the given full path
# Unused
def deleteFolder(folder):
	if os.path.exists(folder):
		shutil.rmtree(folder)
	
# Server

if DEBUG:
	print " * Running in DEBUG mode"

if __name__ == "__main__":
    app.run(debug=DEBUG)
