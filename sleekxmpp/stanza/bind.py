"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import sleekxmpp
from sleekxmpp.xmlstream.stanzabase import ElementBase, ET, JID
from sleekxmpp.stanza.iq import Iq

class Bind(ElementBase):
    #namespace = 'example:task'
    name = 'bind'
    plugin_attrib = 'bind'
    interfaces = set(('name', 'default', 'log', 'error'))
    sub_interfaces = interfaces
