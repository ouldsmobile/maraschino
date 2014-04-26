import platform, urllib2
try:
    import xml.etree.cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree

debug = False

def getXMLFromPMS(baseURL, path, options={}, authtoken='', raw=False):
    if not path.startswith('/'):
        path = '/%s' % path
    xargs = {}

    if options is None:
        xargs = getXArgsDeviceInfo()
    else:
        for k in options:
            xargs[k] = options[k]

    if not authtoken == '':
        xargs['X-Plex-Token'] = authtoken

    if debug:
        print "URL: %s%s" % (baseURL, path)
        print "xargs: %s" % xargs

    request = urllib2.Request(baseURL+path , None, xargs)
    try:
        response = urllib2.urlopen(request, timeout=20)
    except urllib2.URLError as e:
        if debug:
            print 'No Response from Plex Media Server'
            if hasattr(e, 'reason'):
                print "We failed to reach a server. Reason: %s" % e.reason
            elif hasattr(e, 'code'):
                print "The server couldn't fulfill the request. Error code: %s" % e.code
        return False
    except IOError:
        if debug:
            print 'Error loading response XML from Plex Media Server'
        return False

    if raw:
        return response

    # parse into etree
    XML = etree.parse(response)

    if debug:
        print "====== received PMS-XML ======"
        print prettyXML(XML)
        print "====== PMS-XML finished ======"

    return XML

def getXArgsDeviceInfo():
    xargs = dict()
    system = str(platform.system())
    if 'Darwin' in system:
        system = 'MacOSX'
    xargs['X-Plex-Device'] = str(platform.node())
    xargs['X-Plex-Model'] = '0.1'
    xargs['X-Plex-Client-Identifier'] = str(platform.node())
    xargs['X-Plex-Device-Name'] = 'Web Frontend'
    xargs['X-Plex-Platform'] = system
    xargs['X-Plex-Platform-Version'] = str(platform.release())
    xargs['X-Plex-Client-Platform'] = 'MacOSX'
    xargs['X-Plex-Product'] = 'Maraschino'
    xargs['X-Plex-Version'] = '0.1'

    return xargs

def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def prettyXML(XML):
    indent(XML.getroot())
    return(etree.tostring(XML.getroot()))

def xml_to_dict(root):
    d = dict()
    d = root.attrib

    for child in root:
        if child.tag in d: # if this key already exist in dict then create a list with all the entries
            l = []
            if type(d[child.tag]) is dict:
                l.append(d[child.tag])
            else:
                for item in d[child.tag]:
                    if type(item) is not str:
                        l.append(item)
            l.append(xml_to_dict(child))
            d[child.tag] = l
        else: # if key does not exist, create dictionary with it's children attributes
            d[child.tag] = xml_to_dict(child)

    return d
