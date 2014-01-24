# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
DocString manipulation methods to create test reports
"""

import ast
import os

from testimony.constants import DOCSTRING_TAGS, REPORT_TAGS


def main(report, paths):
    """
    Main function for testimony project

    Expects a valid report type and valid directory paths, hopefully argparse
    is taking care of validation
    """
    result = {
        'bugs': 0,
        'bugs_list': list(),
        'invalid_docstring': 0,
        'manual_count': 0,
        'tc_count': 0,
        }
    dir_list = []
    for path in paths:
        result = reset_counts(result)
        print "--------------------------------------------------------------"
        dir_list.append(path)
        dir_list = get_all_dirs(path, dir_list)
        for dirs in dir_list:
            print "\nTEST PATH: %s" % dirs
            for files in os.listdir(str(dirs)):
                if str(files).startswith('test_') and str(files).endswith('.py'):
                    #Do not print this text for test summary
                    if report != REPORT_TAGS[1]:
                        print "Analyzing %s..." % files
                    filepath = os.path.join(str(dirs), str(files))
                    list_strings, result = get_docstrings(report, filepath, result)
                    if report != REPORT_TAGS[1]:
                        print_testcases(report, list_strings, result)
                    else:
                        #for printing test summary later
                        result = update_summary(list_strings, result)
        #Print for test summary
        if report == REPORT_TAGS[1]:
            print_summary(result)
        #Print total number of invalid doc strings
        if report == REPORT_TAGS[2]:
            print "\nTotal Number of invalid docstrings:  %d" % result['invalid_docstring']
        #Print number of test cases affected by bugs and also the list of bugs
        if report == REPORT_TAGS[3]:
            print "\nTotal Number of test cases affected by bugs: %d" % result['bugs']
            print "List of bugs:                               ", result['bug_list']


def get_docstrings(report, path, result):
    """
    Function to read docstrings from test_*** methods for a given file
    """
    return_list = []
    obj = ast.parse(''.join(open(path)))
    #The body field inside obj.body[] contains the docstring
    #So first find the body field of obj.body[] array
    for i in range(0, len(obj.body)):
        parameters = obj.body[i]._fields
        for attr in parameters:
            if attr == 'body':
                break
    #Now iterate the found body[] list from obj.body[] to find the docstrings
    #Remember that this body[] list will have all different items like class
    #docstrings and functions. So first find the items which are functions
    for j in range(0, len(obj.body[i].body)):
        try:
            obj_param = obj.body[i].body[j]._fields
            for attr in obj_param:
                #Retrieve the func name to check if this is a test_* function
                if attr == 'name':
                    func_name = getattr(obj.body[i].body[j], "name")
                    if func_name.startswith('test'):
                        #Find the docstring value of this function
                        #Remove the trailing spaces
                        value = obj.body[i].body[j].body[0].value.s.lstrip()
                        #Split the docstring with @
                        doclines = value.split('@',)
                        item_list = []
                        for attr in doclines:
                            #Remove trailing spaces
                            attr = attr.rstrip()
                            #Remove any new line characters
                            attr = attr.rstrip('\n')
                            if attr != '':
                                if report == REPORT_TAGS[2]:
                                    docstring_tag = attr.split(" ", 1)
                                    #Error out invalid docstring
                                    if not any(x in docstring_tag[0].lower() for x in DOCSTRING_TAGS):
                                        item_list.append("-->Invalid DocString: %s<--" % attr)
                                        result['invalid_docstring'] = result['invalid_docstring'] + 1
                                elif report == REPORT_TAGS[3]:
                                    #Find the bug from docstring
                                    docstring_tag = attr.split(" ", 1)
                                    if DOCSTRING_TAGS[5] in docstring_tag[0].lower():
                                        item_list.append(attr)
                                        result['bugs'] = result['bugs'] + 1
                                        result['bug_list'].append(docstring_tag[1])
                                else:
                                    #For printing all test cases
                                    item_list.append(attr)
                        if len(item_list) != 0:
                            return_list.append(item_list)
        except AttributeError:
            if report == REPORT_TAGS[0] or report == REPORT_TAGS[2]:
                print "--> DocString Missing. Please update <--"
            result['no_docstring'] = result['no_docstring'] + 1
            continue
        except:
            print "!!!!!Exception in parsing DocString!!!!!"
    return return_list, result


def print_testcases(report, list_strings, result):
    """
    Prints all the test cases based on given criteria
    """
    tc = 0
    for docstring in list_strings:
        if report == REPORT_TAGS[0]:
            tc = tc + 1
            print "TC %d" % tc

        #verify if this needs to be printed
        manual_print = False
        auto_print = True
        for lineitem in docstring:
            docstring_tag = lineitem.split(" ", 1)
            if report == REPORT_TAGS[5]:
                if DOCSTRING_TAGS[6] in docstring_tag[0].lower():
                    auto_print = False
            if report == REPORT_TAGS[4]:
                if DOCSTRING_TAGS[6] in docstring_tag[0].lower():
                    manual_print = True
        if report == REPORT_TAGS[5] and auto_print is True:
            print_line_item(docstring)
        if report == REPORT_TAGS[4] and manual_print is True:
            print_line_item(docstring)
        if report == REPORT_TAGS[0] or report == REPORT_TAGS[2]:
            print_line_item(docstring)


def update_summary(list_strings, result):
    """
    Updates summary for reporting
    """
    for docstring in list_strings:
        result['tc_count'] = result['tc_count'] + 1
        for lineitem in docstring:
            if lineitem.startswith("Status") and "Manual" in lineitem:
                result['manual_count'] = result['manual_count'] + 1
    return result


def print_summary(result):
    """
    Prints summary for reporting
    """
    print "Total Number of test cases:      %d" % result['tc_count']
    print "Total Number of automated cases: %d" % (result['tc_count'] - result['manual_count'])
    print "Total Number of manual cases:    %d" % result['manual_count']
    print "Test cases with no docstrings:   %d" % result['no_docstring']


def reset_counts(result):
    """
    Resets all the counts to switch between UI and CLI reports
    """
    result['tc_count'] = 0
    result['manual_count'] = 0
    result['no_docstring'] = 0
    result['invalid_docstring'] = 0
    result['bugs'] = 0
    result['bug_list'] = []
    return result


def print_line_item(docstring):
    """
    Parses the given docstring list to print out each line item
    """
    for lineitem in docstring:
        print lineitem


def get_all_dirs(path, dir_list):
    """
    Returns all folders recursively
    """
    for root, dirs, files in os.walk(path):
        for attr in dirs:
            attr = os.path.join(os.path.abspath(root), attr)
            if os.path.isdir(attr):
                dir_list.append(attr)
    return dir_list