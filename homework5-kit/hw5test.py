#!/usr/bin/python

# Auto Grader and self-tester for Duke CS/ECE 250 (and other stuff)
# Version 1.2
# By Tyler Bletsch (Tyler.Bletsch@duke.edu)

#  ** YOU DON'T NEED TO MODIFY THIS SCRIPT JUST TO CHANGE ASSIGNMENTS **
# In earlier versions, you'd edit this script to change the tests.
# No longer is this the case. Now you just change variables in settings.py,
# and the only reason to change this file is to add new features. This way
# the same tester script can be used everywhere.

import sys,os,re,platform
from itertools import izip_longest
from optparse import OptionParser

# =========== CONSTANTS ===========
VALID_MODES = ('EXECUTABLE', 'SPIM', 'LOGISIM') # used for mode verification
DEFAULT_SETTINGS_FILE = 'settings.py'

# =========== GENERAL UTILITY ==============

import shutil
def apply_file_filter(filter, filename,backup_filename=None):
    if backup_filename:
        shutil.copy(filename,backup_filename)
    fp_src = open(backup_filename,"r")
    fp_dst = open(filename,"w")
    for line in filter(fp_src):
        fp_dst.write(line)
    fp_src.close()
    fp_dst.close()
    
def is_executable_available(ex):
    return my_system("which %s >&/dev/null" % ex)==0

# what fraction difference (like percent difference but not x100) between two numbers
# special cases: if a=b=0, returns 0.0, if b=0 & a!=b, returns 1.0
def frac_difference(a,b):
    if b==0:
        if a==0: return 0.0
        else:    return 1.0
    return a/b - 1.0

def iff(c,a,b):
    if c: return a
    else: return b
    
# ============== DIFF FUNCTIONS =================

def normal_diff(expected_output_filename, actual_output_filename, diff_filename):
    command = "diff -bwB %s %s > %s" % (expected_output_filename, actual_output_filename, diff_filename)
    r = my_system(command)
    return r == 0
    
# for hoopstat-like files (name followed by float, equal to within delta given and/or fractional difference given)
def hoopstat_diff(file1, file2, outfile, delta=None, frac_delta=0.001):
    fp1 = open(file1,"r")
    fp2 = open(file2,"r")
    out = open(outfile,"w")
    n = 0
    retval = True
    def line_match(line1, line2):
        if line1==line2: 
            return True
        m1 = re.match(r"(\w+)\s+([.\d]+)$", line1)
        if not m1: return False
        m2 = re.match(r"(\w+)\s+([.\d]+)$", line2)
        if not m2: return False
        k1 = m1.group(1)
        v1 = float(m1.group(2))
        k2 = m2.group(1)
        v2 = float(m2.group(2))
        if k1 != k2:
            return False
        if delta is not None  and  abs(v1-v2) > delta:
            return False
        if frac_delta is not None  and  abs(frac_difference(v1,v2)) > frac_delta:
            return False
        return True
    for line1,line2 in izip_longest(fp1,fp2, fillvalue=""):
        line1 = line1.rstrip()
        line2 = line2.rstrip()
        n += 1
        if not line_match(line1, line2):
            out.write("< %s\n> %s\n" % (line1,line2))
            retval = False
    fp1.close()
    fp2.close()
    out.close()
    return retval

# ============== SPIM-SPECIFIC FUNCTIONS =================

def filter_spim(stream):
    header_line_prefixes = [
        "SPIM Version",
        "Copyright 1990-",
        "All Rights",
        "See the file README",
        "Loaded:"
    ]
    for i,line in enumerate(stream):
        if i<len(header_line_prefixes) and any(line.startswith(prefix) for prefix in header_line_prefixes): continue
        yield line
        
def filter_remove_prompts(stream):
    for line in stream:
        line = re.sub(r'.*:[ \t]*','',line)
        if re.search(r'\S',line): yield line

def filter_remove_spim_and_prompts(stream): return filter_remove_prompts(filter_spim(stream))

# this will remove spim headers and colon-terminated prompts
def spim_clean(filename):
    apply_file_filter(filter_remove_spim_and_prompts,filename,filename+".orig")
    
# =============== TEST HELPER FUNCTIONS ============
def get_expected_output_filename(suite_name, test_num):
    return TEST_DIR+"/%s_expected_%d.txt" % (suite_name, test_num)
    
def get_actual_output_filename(suite_name, test_num):
    return TEST_DIR+"/%s_actual_%d.txt" % (suite_name, test_num)
    
def get_diff_filename(suite_name, test_num):
    return TEST_DIR+"/%s_diff_%d.txt" % (suite_name, test_num)

def path_relative_to_test_dir(path):
    return os.path.join(TEST_DIR,path)

def clean():
    my_system("rm -f "+TEST_DIR+"/*_actual_*.txt* "+TEST_DIR+"/*_diff_*.txt*")
    
def verbose_print(s):
    if verbose_mode: sys.stdout.write("\033[90m%s\033[m\n" % s)

def error_print(s):
    sys.stdout.write("\033[91m%s\033[m\n" % s)

def my_system(command):
    verbose_print("$ %s" % command)
    r = os.system(command)
    #sys.exit(1)
    #r=0
    if platform.system()[-1] == 'x':
        return r>>8 # platforms ending in 'x' are probably Linux/Unix, and they put exit status in the high byte
    else:
        return r # windowsy platforms just return exit status directly
    
def run_test(suite_name,test_num,test):
    desc = test['desc']
    args = test.get('args',[])
    infile = test.get('infile',None)
    do_valgrind = test.get('valgrind',False)
    points_available = test.get('points',0)
    preprocess_actual_func = test.get('preprocess_actual',None)
    diff_func = test.get('diff',normal_diff)
    command_append = test.get('command_append','')
    suite_filename = suite2filename(suite_name)
    
    
    if infile: 
        infile = path_relative_to_test_dir(infile)
        
    points_awarded = points_available
    
    expected_output_filename = get_expected_output_filename(suite_name, test_num)
    actual_output_filename = get_actual_output_filename(suite_name, test_num)
    diff_filename = get_diff_filename(suite_name, test_num)
    
    is_pass = True
    fail_reason = ''
    
    args_string = " ".join(args)
    if MODE=='EXECUTABLE':
        command = "./%s %s %s >& %s" % (suite_filename, args_string, command_append, actual_output_filename)
    elif MODE=='SPIM':
        command = "%s -f %s %s %s >& %s" % (SPIM_BINARY, suite_filename, args_string, command_append, actual_output_filename)
    elif MODE=='LOGISIM':
        command = "java -jar logisim_cli.jar -f %s %s %s > %s" % (suite_filename, args_string, command_append, actual_output_filename)
    
    if infile: command += " < %s" % infile
    
    r = my_system(command)
    orig_exit_status = r
    if r != 0:
        is_pass = False
        points_awarded *= NON_ZERO_EXIT_STATUS_PENALTY
        fail_reason += "Exit status is non-zero. "

    if preprocess_actual_func:
        verbose_print("Preprocessing output file '%s'" % actual_output_filename)
        preprocess_actual_func(actual_output_filename)
        
    if not diff_func(expected_output_filename,actual_output_filename,diff_filename):
        is_pass = False
        points_awarded = 0
        fail_reason += "Output differs from expected (see diff for details). "
    
    if do_valgrind:
        if MODE != 'EXECUTABLE':
            error_print("Script error: tried to valgrind, but script isn't setup for executables (MODE=%s). Fix script." % MODE)
            sys.exit(2)
            
        command = "valgrind -q --error-exitcode=88 --show-reachable=yes --leak-check=full ./%s %s >& /dev/null" % (suite_name, " ".join(args))
        r = my_system(command)
        if r == 88:
            is_pass = False
            points_awarded *= VALGRIND_PENALTY
            fail_reason += "Valgrind detected memory leak. "
        elif r != orig_exit_status:
            is_pass = False 
            points_awarded *= VALGRIND_PENALTY
            fail_reason += "Got unexpected exit status from valgrind (%d)? " % r
        
    result_string = "%10s test #%2d (%-30s): " % (suite_name, test_num, desc)
    if IS_GRADER:
        result_string += "\033[36m(%4.1f/%4.1f)\033[m " % (points_awarded, points_available)
        
    if is_pass: result_string += "\033[32;7mpass\033[m"
    else:       result_string += "\033[41mFAIL\033[0;31m %s\033[m" % fail_reason
    
    print result_string
    
    return (is_pass,fail_reason,points_awarded,points_available)

def suite2filename(suite_name):
    if 'force_suite_filename' in globals(): 
        suite_filename = force_suite_filename # allow suite filename forced by setting
    elif MODE=='EXECUTABLE':
        suite_filename = suite_name
    elif MODE=='SPIM':
        suite_filename = "%s.s" % suite_name
    elif MODE=='LOGISIM':
        suite_filename = "%s.circ" % suite_name
        
    return suite_filename
    
def run_test_suite(suite_name):
    total_points_awarded = 0
    total_points_available = 0
    suite = suites[suite_name]
    
    suite_filename = suite2filename(suite_name)
        
    if not os.path.isfile(suite_filename):
        error_print("%s: Not found." % suite_filename)
        return
        
    for test_num,test in enumerate(suite):
        (is_pass,fail_reason,points_awarded,points_available) = run_test(suite_name,test_num,test)
        total_points_awarded += points_awarded
        total_points_available += points_available
    if IS_GRADER:
        print "\033[36;1mPoints awarded for %s: %4.1f/%4.1f (assuming no partial credit)\033[m" % (suite_name, total_points_awarded, total_points_available)
        print ""

# ======================= ACTUAL IMMEDIATE CODE ==============

parser = OptionParser("Usage: %prog [options] <suite>")
 
parser.add_option("-v", "--verbose", dest="verbose", help="Print extra info.", action="store_true")
parser.add_option("-f", "--settings-file", dest="settings_file", help="Read settings from python script given. Default: %default", metavar="FILE", default=DEFAULT_SETTINGS_FILE)
 
(options, args) = parser.parse_args()
settings_file = options.settings_file
verbose_mode = options.verbose
 
try:
    execfile(settings_file)
    settings_missing = False
except IOError,e:
    error_print("Can't load settings file: %s" % e)
    # defaults to get us through the usage message
    settings_missing = True
    suite_names = []

if (len(args)<=0):
    if settings_missing:
        print "Auto tester [SETTINGS FILE MISSING]"
    else: 
        sw_name = iff(IS_GRADER,"\033[31;7mAuto GRADER\033[m","Auto tester")
        print "%s for %s, %s" % (sw_name, ASSIGNMENT, SEMESTER)
    print ""
    parser.print_help()
    print ""
    print "Where <suite> is one of:"
    print "  %-15s: Run all program tests" % ("ALL",)
    print "  %-15s: Remove all the test output produced by this tool" % ("CLEAN",)
    for suite_name in suite_names:
        print "  %-15s: Run tests for %s" % (suite_name,suite_name)
    sys.exit(1)

if not suite_names:
    error_print("Error: No test suites loaded. Aborting.")
    sys.exit(2)
    
requested_suite_name = args[0]

# some sanity checks first
if MODE not in VALID_MODES:
    error_print("ERROR: This script's mode setting is not one of the valid settings. Fix the script.")
    sys.exit(2)

if MODE=='SPIM' and not is_executable_available(SPIM_BINARY):
    error_print("ERROR: Unable to find command-line spim. This tool is meant to be used on the Duke Linux machines (where spim is pre-installed). You can try to install it yourself, but it's kind of annoying.")
    sys.exit(1)
    
if MODE=='LOGISIM' and not os.path.isfile(LOGISIM_JAR):
    error_print("ERROR: Unable to find Logisim JAR file '%s'." % LOGISIM_JAR)
    sys.exit(1)


if requested_suite_name == "ALL":
    for suite_name in suite_names:
        run_test_suite(suite_name)
elif requested_suite_name == "CLEAN":
    verbose_mode=True # force verbose for this
    clean()
elif requested_suite_name in suite_names:
    run_test_suite(requested_suite_name)
else:
    print "%s: No such test suite" % (requested_suite_name)
