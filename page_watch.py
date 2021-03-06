import sys
import os
import hashlib
import tempfile
import difflib
"""
This file contains a simple program to store a list of static webpages, 
and ot fetch them to check for differences since the first save. It uses a 
linux style .pagewatch directionr in the users home dir in order to save
the list of files and cached origional version.
"""

#boilerplate metadata block
__author__ = "Far McKon"
__copyright__ = "Copyright 2011, Far McKon Light Industries"
__license__ = "GPL"
__version__ = "1.0.1.0"
__maintainer__ = "Far McKon"
__email__ = "FarMcKon@gmail.com"

pagewatch_list_filename =	os.path.expanduser("~/.pagewatch/watchlist.txt")
pagewatch_old_data_dir =	os.path.expanduser("~/.pagewatch/old_pages")


def dircheck_and_create(dirname):
	""" takes a directory name (NOT a filename) checks if it exists, or if it needs
		to be created, prompts user for creation
	"""
	if( not os.path.exists(dirname) ):
		var = raw_input("May we create " + dirname +" settings dir for you (yes/no)?")
		if(var == 'y' or var == 'yes' or var == 'Y' ):
			os.mkdir( dirname )
			return True
		elif(var == 'n' or var == 'no' or var == 'N' ):
			print "cannot contiune. Goodbye"
			return False
		print "you entered ", var , "which I did not understand. Goodbye"
		return False
	print "dir exists"
	return True	
	
def filecheck_and_create(filename):
	""" takes a file name and checks if it exists, or if it needs
		to be created, prompts user for creation
	"""	if( not os.path.isfile(filename) ):
		var = raw_input("May we create " + filename  +" file for you (yes/no)?")
		if(var == 'y' or var == 'yes' or var == 'Y' ):
			open(filename, 'w').close() 
			return True
		elif(var == 'n' or var == 'no' or var == 'N' ):
			print "cannot contiune. Goodbye"
			return False
		print "you entered ", var , "which I did not understand. Goodbye"
		return False
	return True
	
def wget(url, filename=None):
	""" Fetches a url wget style. if filename is not specified, a tmpfile is created.
	returns None, or the temp filename used to store the data
	""" 
	import urllib2
	try:
		opener1 = urllib2.build_opener()
		page1 = opener1.open(url)
		data = page1.read()
	except Exception:
		print "wget fail"
		return None 
	
	tmp_filename = filename
	if(tmp_filename == None):
		tmp_filename = tempfile.mkstemp()[1] #tmpnam, but safe
	print tmp_filename # test
	fout = open(tmp_filename, "wb")
	fout.write(data)
	fout.close()
	return tmp_filename
	
def md5sum(fileName, excludeLine="", includeLine=""):
    """Compute md5 hash of the specified file. exclude line is a 
    pattern that is use to discard any line that starts iwth that pattern,
    include line is concatenated to to end of the passed file before an md5 is created
    """
    #thanks to http://thejaswihr.blogspot.com/2008/06/python-md5-checksum-of-file.html 
    # for this function
    m = hashlib.md5()
    try:
        fd = open(fileName,"rb")
    except IOError:
        print "Unable to open the file in readmode:", filename
        return
    content = fd.readlines()
    fd.close()
    for eachLine in content:
        if excludeLine and eachLine.startswith(excludeLine):
            continue
        m.update(eachLine)
    m.update(includeLine)
    return m.hexdigest()

def run_check():
	""" Checks the url watchlist for changes. 
	returns 'False' if a test was not performed
	otherwise returns a dict of text of diff's, 
	None is a valid value indicating tests were run, but no differnece were found"""
	diffsDir = {}
	
	check_file = pagewatch_list_filename
	ok = dircheck_and_create( os.path.dirname(check_file) )	
	if(ok == False):
		return False
	ok = filecheck_and_create(check_file)	
	if(ok == False):
		return False


	#Load a txt file
	fh = open(check_file, 'r')
	lines = fh.readlines()
	
	for line in lines:
		if line[0] == '#' or line[0] == '\n': #comment,space,EOF line
			continue
		(url, md5, old_ver_filename) = line.split(' : ')  #split into 'url md5 filename', ' : ' delinated
		print 'url: ', url
		print 'md5: ', md5
		print 'old version zip: ', old_ver_filename

		#wget that url to a tmp file
		tmp_filename = wget(url)
		if(tmp_filename == None):
			print "run_check fail to fetch " , url ," (tmp_filename " , tmp_filename ,")"
			return False

		#if new md5 != md5 in file line
		md5_of_tmp = md5sum(tmp_filename)
		print "md5 of tmp: ", str(md5_of_tmp)
		
		if( str(md5_of_tmp) == str(md5) ):
			#print "md5 match!"
			continue  
		else :
			#print "no md5 match!"
			old_fn = os.path.expanduser(old_ver_filename.strip()) #read from file, do expanduser
			old_fh = open(old_fn, 'rb')
			old_data = old_fh.readlines()
			new_fh = open(tmp_filename, 'rb')
			new_data = new_fh.readlines()

			differ = difflib.HtmlDiff()
			#unzip old file, return a diff of the two files.
			#update md5 file, add new url entry
			diffsDir[url] = differ.make_file(old_data,new_data)
			
			#print diffsDir[url]
			print 'url: ', url
	#return the dictionry of diff's
	return diffsDir

#pagewatch_add
def add_page( url ):
	""" This funciton adds a page to the pagewatch list,
	and caches the baseline version of that page for future diffs
	"""
	# wget the url
	print "getting url ", url
	tmp_filename = wget(url)
	if(tmp_filename == None):
		print "add_page, fail to fetch " , url ," (tmp_filename " , tmp_filename ,")"
		return False

	md5 = md5sum(tmp_filename)
	print "content md5 ", sum
	#check if we can drop a tmpfile in there
	dircheck_and_create(pagewatch_old_data_dir)
	print "pagewatch_old_data_dir", pagewatch_old_data_dir
	cache_filename = tempfile.mkstemp(dir=pagewatch_old_data_dir)[1] #tmpnam, but safe
	print "cache file ", cache_filename
	#copy our page into our cache
	fh = open(cache_filename, "wb");
	fh.write( open(tmp_filename, 'rb').read() )
	
	#
	list_fh = open(pagewatch_list_filename, 'a')
	list_fh.write(" : ".join([url, md5, cache_filename])	)
	list_fh.write('\n')
	list_fh.close()
	
if __name__ == "__main__":
	"""
	Standard main function, only runs if the module was called from the commnad line
	"""
	print " Pagewatch to the rescue!"
	#print sys.argv

	#TODO add real options parsing in the future
	if( len(sys.argv) < 2):
		#print "looking for changes"
		diffsDir = run_check()
		if( diffsDir == False):
			print "Error in checking the pages available. "
			exit(-1)
		if( diffsDir == None) :
			print "No changes detected, nothing to report  "
			exit(0)
		else:
			print "We found ", len(diffsDir), " changes in files"
	
	elif( len(sys.argv) >= 2):
		print "adding page" , sys.argv[1]
		add_page(sys.argv[1])
