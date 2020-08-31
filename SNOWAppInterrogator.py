"""
Title: SNOWAppInterrogator.py
Author:  Benjamin McConnell
Created: 26 AUG 2020
Last Updated: 27 AUG 2020


Description:
This script was written to demonstrate the authors ability to interface 
with ServiceNow's REST APIs. There are a 4 REST API calls that aim
to demonstrate proficiency in a variety of programming skills. 
"""
#Import dependencies
import logging
from logging.handlers import RotatingFileHandler
import argparse
import requests
import json
import xml.etree.ElementTree as ET

def main():
    '''
    This is the main function where the primary execution logic resides. 
    While a main function isn't necessary in Python, it's used here for
    convenience and readability. This brings the primary logic to the top
    and allows the reader to more easily interpret the script by reading
    from top to bottom
    '''
    log.info("Beginning Execution")
    
    #Demo 1. Pull all Application Records
    records = getAllTableRecords(args, args.application)
    inc = 1
    for record in records["result"]:
        print ('%s. %s - %s' %(inc, record["number"], record["description"] ))
        inc = inc + 1

    #Demo 2. Pull all Business Rules Associated with Application and
    #Identify potentially cutomized business rules
    busRules = getBusinessRules(args, args.application)
    custBusRules = identifyCustomBusinessRules(busRules)
    inc = 1
    for rule in custBusRules:
        log.info('%s. %s' % (inc, rule["sys_name"]))
        inc = inc + 1
    
    #Demo3: Dynamically Generate a new object class based on the ServiceNow Application Schema
    log.info('Generating new class from Servicenow %s schema...' % args.application)
    newClass = classFactory(args.application)
    log.info('Successfull created new class: \r %s' % newClass)

    #Demo4: Create a new record in ServiceNow
    newObject = createRecord(args,args.application)
    log.info(newObject)

    log.info('Completed Script execution')
###################################################################################
def parseArguments():
    '''
    This function configure the command line paramater parser. It sets a help description
    for the script and enables the user to get instructions on parameter usage at the
    command line. 
    '''
    #Parse Arguments
    helpText = """
    This script can be used to interrogate a ServiceNow application and identify components
    that have been customized. 
    """

    #Initialize parser and add script specific help text
    parser = argparse.ArgumentParser(description=helpText)

    #Add long and short arguments
    parser.add_argument("--instance", "-i", help="ServiceNow Instance URL")
    parser.add_argument("--username", "-u", help="ServiceNow API Username")
    parser.add_argument("--password", "-p", help="ServiceNow API Password")
    parser.add_argument("--application", "-a", help="ServiceNow Application Name. ex:'Incident Management'")
    
    #Parse parameters \
    return parser.parse_args()

def setupLogging(fileName):
    '''This function setups a log handler to provide consistent formatting for log
    files. It also sets up automatic creation of a new log file after the log file
    grows to 100Mb. It will keep 2 historical and 1 active log file at all times
    and overwrite them as needed.   
    '''
    handler = RotatingFileHandler('%s.log' % fileName, maxBytes=100000000, backupCount=2)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(fmt='[%(asctime)s]-%(levelname)s> \
    %(module)s> %(funcName)s> Line %(lineno)d: %(message)s',\
    datefmt='%m/%d/%Y %I:%M:%S %p')

    handler.setFormatter(formatter)
    logger = logging.Logger('logger')
    logger.addHandler(handler)
    return logger

def getAllTableRecords(args, application, query=''):
    '''This is a generalized function for pulling all records for
    the given application table. 
    '''
    # Prepare request
    url = '%s/api/now/table/%s' % (args.instance, application)
    headers = {"Accept":"application/json"}

    # Send request
    try: 
        log.info("Retrieving all %s records..." % args.application)
        response = requests.get(url, auth=(args.username, args.password), headers=headers, params=query)
        response.raise_for_status()

    #Handle any errors that occur
    except requests.exceptions.HTTPError as eh:
        log.error('%s:%s' %(eh, response.json()))
        print('%s -- %s'%(eh,response.json()))
        exit()

    except requests.exceptions.ConnectionError as ec:
        log.error(ec)
        print('There seems to be something wrong with your internet connection. '
        'Double check your connection and script parameters. -- %s' % ec)
        exit()
  
    except requests.exceptions.RequestException as e:
        log.error(e)
        print ('There is an issue with your connection to ServiceNow. -- %s' %e)
        exit()
 
    
    else:
        #If successful, try to decode the json response
        try:
            data = response.json()

        except json.decoder.JSONDecodeError as e:
            log.error("A problem occured decoding the response from ServiceNow.")
            print ("A problem occured decoding the response from ServiceNow.")
            if response.headers['Content-Type'] == 'text/html':
                log.error('A json object was not returned. '
                'Verify that your instance is active and try again.')
                print(
                'A json object was not returned. Verify that your instance is'  
                ' active and try again.'
                )
            exit()

        else:
            log.info('Successfully retrieved all %s records ' % args.application)
            return data

def getBusinessRules(args, application):
    '''This function retrieves business rules for the given applcation 
    by querying the Table API. 
    '''
    BUSINESS_RULE_TABLE_NAME = 'sys_script'
    query = 'sysparm_query=collection=%s' % application
    data = getAllTableRecords(args, BUSINESS_RULE_TABLE_NAME, query)
    return data


def identifyCustomBusinessRules(busRules):
    '''This function identifies business rules that have been customized
    by checking if the creator is the same as the last user to update the
    business rule. This is an extremely crude test, but it demonstrates the concept.
    '''
    customBusRules = []
    for rule in busRules["result"]:
        if rule["sys_created_by"] != rule ["sys_updated_by"] :
            customBusRules.append(rule)
    return customBusRules

def createRecord (args, application, query=''):
    '''This function creates a new record in the given ServiceNow application table.
    It does this leveraging the post method on the Table API. 
    '''
    #Prepare request
    url = '%s/api/now/table/%s' % (args.instance, application)
    headers = {"Content-Type":"application/xml","Accept":"application/json"}
    data=BuildXML()
    
    # Send request 
    try:  
        log.info("Creating %s record..." % args.application)
        response = requests.post(url, auth=(args.username, args.password), headers=headers, params=query, data=data)
        response.raise_for_status()

    #Handle any errors that occur
    except requests.exceptions.HTTPError as eh:
        log.error('%s:%s' %(eh, response.json()))
        print('%s -- %s'%(eh,response.json()))
        exit()

    except requests.exceptions.ConnectionError as ec:
        log.error(ec)
        print('There seems to be something wrong with your internet connection. \
        Double check your connection and script parameters. -- %s' % ec)
        exit()

    except requests.exceptions.RequestException as e:
        log.error(e)
        print ('There is an issue with your connection to ServiceNow. -- %s' %e)
        exit()

    else:
        #If successful, try to decode the json response
        try:
            data = response.json()

        except json.decoder.JSONDecodeError as e:
            log.error("A problem occured decoding the response from ServiceNow.")
            print ("A problem occured decoding the response from ServiceNow.")
            if response.headers['Content-Type'] == 'text/html':
                log.error('A json object was not returned. '
                'Verify that your instance is active and try again.')
                print(
                'A json object was not returned. Verify that your instance is'  
                ' active and try again.'
                )
            exit()

        else:
            log.info('Successfully retrieved all %s records ' % args.application)
            return data

def BuildXML() : 
    '''This function builds an XML payload that can be passed during a post request to
    the ServiceNow Table API. 
    '''
    root = ET.Element("request") 
    entry = ET.Element("entry") 
    root.append (entry) 
    
    shortDescription = ET.SubElement(entry, "short_description") 
    shortDescription.text = "The sky is falling!"
    urgency = ET.SubElement(entry, "urgency") 
    urgency.text = "2"
    impact = ET.SubElement(entry,"impact") 
    impact.text = "2"

    return ET.tostring(root)

def PullClassSchema():
    '''This function queries the sys_dictionary table through the ServiceNow Table API
    to retrieve a list of attributes associated with the given application table name.
    '''
    #Prepare request
    dictUrl = '%s/api/now/table/sys_dictionary' % args.instance
    query = 'sysparm_query=name=%s^ORname=task' % args.application
    headers = {"Accept":"application/json"}
    
    # Send request   
    try:
        log.info('Retreiving schema for %s table...' %args.application)
        response = requests.get(dictUrl, auth=(args.username, args.password), headers=headers, params=query)
        response.raise_for_status()

    #Handle any errors that occur
    except requests.exceptions.HTTPError as eh:
        log.error('%s:%s' %(eh, response.json()))
        print('%s -- %s'%(eh,response.json()))
        exit()

    except requests.exceptions.ConnectionError as ec:
        log.error(ec)
        print('There seems to be something wrong with your internet connection. \
        Double check your connection and script parameters. -- %s' % ec)
        exit()

    except requests.exceptions.RequestException as e:
        log.error(e)
        print ('There is an issue with your connection to ServiceNow. -- %s' %e)
        exit()
 

    else:
        #If successful, try to decode the json response
        try:
            data = response.json()

        except json.decoder.JSONDecodeError as e:
            log.error("A problem occured decoding the response from ServiceNow.")
            print ("A problem occured decoding the response from ServiceNow.")
            if response.headers['Content-Type'] == 'text/html':
                log.error('A json object was not returned. '
                'Verify that your instance is active and try again.')
                print(
                'A json object was not returned. Verify that your instance is'  
                ' active and try again.'
                )
            exit()

        else:
            log.info('Successfully retrieved all %s records ' % args.application)
            return data

def classFactory(application):
    '''This function generates a python object class from the given 
    ServiceNow application table schema.  
    '''
    classAttributes = {}
    schema = PullClassSchema()
    for attr in schema['result']:
        classAttributes[attr["element"]] = attr['internal_type']
        log.info('%s: %s'%(attr['element'], attr['internal_type']['value']))
    newClass = type(application, (object, ), classAttributes) 
    return newClass

#Initialize Global Objects
log = setupLogging('SNOWAppInterrogator')
log.info("Initializing")
args = parseArguments()
url = '%s/api/now/table/%s' % (args.instance, args.application)

#Execute main script
if __name__ == "__main__":
    main()

