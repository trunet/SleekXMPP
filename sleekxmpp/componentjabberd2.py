# -*- coding: utf-8 -*-
"""
    sleekxmpp.clientxmpp
    ~~~~~~~~~~~~~~~~~~~~

    This module provides XMPP functionality that
    is specific to client connections.

    Part of SleekXMPP: The Sleek XMPP Library

    :copyright: (c) 2011 Nathanael C. Fritz
    :license: MIT, see LICENSE for more details
"""

from __future__ import absolute_import, unicode_literals

import logging

from sleekxmpp.stanza import StreamFeatures
from sleekxmpp.basexmpp import BaseXMPP
from sleekxmpp.exceptions import XMPPError
from sleekxmpp.xmlstream import XMLStream
from sleekxmpp.xmlstream.matcher import StanzaPath, MatchXPath
from sleekxmpp.xmlstream.handler import Callback

log = logging.getLogger(__name__)


class ComponentJabberd2(BaseXMPP):

    """
    SleekXMPP's client class. (Use only for good, not for evil.)

    Typical use pattern:

    .. code-block:: python

        xmpp = ClientXMPP('user@server.tld/resource', 'password')
        # ... Register plugins and event handlers ...
        xmpp.connect()
        xmpp.process(block=False) # block=True will block the current
                                  # thread. By default, block=False

    :param jid: The JID of the XMPP user account.
    :param password: The password for the XMPP user account.
    :param ssl: **Deprecated.**
    :param plugin_config: A dictionary of plugin configurations.
    :param plugin_whitelist: A list of approved plugins that
                    will be loaded when calling
                    :meth:`~sleekxmpp.basexmpp.BaseXMPP.register_plugins()`.
    :param escape_quotes: **Deprecated.**
    """

    def __init__(self, jid, password, plugin_config={}, plugin_whitelist=[],
                 escape_quotes=True, sasl_mech=None, lang='en'):
        BaseXMPP.__init__(self, jid, 'jabber:client')

        self.escape_quotes = escape_quotes
        self.plugin_config = plugin_config
        self.plugin_whitelist = plugin_whitelist
        self.default_port = 5347
        self.default_lang = lang

        self.credentials = {}

        self.password = password

        self.stream_header = "<stream:stream to='%s' %s %s %s %s>" % (
                self.boundjid.host,
                "xmlns:stream='%s'" % self.stream_ns,
                "xmlns='%s'" % self.default_ns,
                "xml:lang='%s'" % self.default_lang,
                "version='1.0'")
        self.stream_footer = "</stream:stream>"

        self.features = set()
        self._stream_feature_handlers = {}
        self._stream_feature_order = []

        #TODO: Use stream state here
        self.authenticated = False
        self.sessionstarted = False
        self.bound = False
        self.bindfail = False

        self.add_event_handler('connected', self._reset_connection_state)
        self.add_event_handler('session_bind', self._handle_session_bind)

        self.register_stanza(StreamFeatures)

        self.register_handler(
                Callback('Stream Features',
                         MatchXPath('{%s}features' % self.stream_ns),
                         self._handle_stream_features))

        # Setup default stream features
        self.register_plugin('feature_starttls')
        self.register_plugin('feature_bind')
        self.register_plugin('feature_session')
        self.register_plugin('feature_preapproval')
        self.register_plugin('feature_mechanisms')

        if sasl_mech:
            self['feature_mechanisms'].use_mech = sasl_mech

    @property
    def password(self):
        return self.credentials.get('password', '')

    @password.setter
    def password(self, value):
        self.credentials['password'] = value

    def connect(self, address=tuple(), reattempt=True,
                use_tls=True, use_ssl=False):
        """Connect to the XMPP server.

        When no address is given, a SRV lookup for the server will
        be attempted. If that fails, the server user in the JID
        will be used.

        :param address   -- A tuple containing the server's host and port.
        :param reattempt: If ``True``, repeat attempting to connect if an
                         error occurs. Defaults to ``True``.
        :param use_tls: Indicates if TLS should be used for the
                        connection. Defaults to ``True``.
        :param use_ssl: Indicates if the older SSL connection method
                        should be used. Defaults to ``False``.
        """
        self.session_started_event.clear()

        self._expected_server_name = self.boundjid.host

        return XMLStream.connect(self, address[0], address[1],
                                 use_tls=use_tls, use_ssl=use_ssl,
                                 reattempt=reattempt)

    def register_feature(self, name, handler, restart=False, order=5000):
        """Register a stream feature handler.

        :param name: The name of the stream feature.
        :param handler: The function to execute if the feature is received.
        :param restart: Indicates if feature processing should halt with
                        this feature. Defaults to ``False``.
        :param order: The relative ordering in which the feature should
                      be negotiated. Lower values will be attempted
                      earlier when available.
        """
        self._stream_feature_handlers[name] = (handler, restart)
        self._stream_feature_order.append((order, name))
        self._stream_feature_order.sort()

    def unregister_feature(self, name, order):
        if name in self._stream_feature_handlers:
            del self._stream_feature_handlers[name]
        self._stream_feature_order.remove((order, name))
        self._stream_feature_order.sort()

    def _reset_connection_state(self, event=None):
        #TODO: Use stream state here
        self.authenticated = False
        self.sessionstarted = False
        self.bound = False
        self.bindfail = False
        self.features = set()

    def _handle_stream_features(self, features):
        """Process the received stream features.

        :param features: The features stanza.
        """
        for order, name in self._stream_feature_order:
            if name in features['features']:
                handler, restart = self._stream_feature_handlers[name]
                if handler(features) and restart:
                    # Don't continue if the feature requires
                    # restarting the XML stream.
                    return True
        log.debug('Finished processing stream features.')
        self.event('stream_negotiated')

    def _handle_session_bind(self, jid):
        """Set the client roster to the JID set by the server.

        :param :class:`sleekxmpp.xmlstream.jid.JID` jid: The bound JID as
            dictated by the server. The same as :attr:`boundjid`.
        """
        self.client_roster = self.roster[jid]

ComponentJabberd2.registerFeature = ComponentJabberd2.register_feature
