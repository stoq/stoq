#!/usr/bin/env python
# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2012 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s):   Stoq Team   <stoq-devel@async.com.br>
##
""" stoqdbadmin: Command line utility to manipulate the database.  """

import logging
import optparse
import sys


class StoqCommandHandler:
    def __init__(self, prog_name):
        self.prog_name = prog_name

    def _read_config(self, options, create=False, register_station=True,
                     check_schema=True, load_plugins=True):
        from stoqlib.lib.configparser import StoqConfig
        from stoq.lib.startup import setup
        config = StoqConfig()
        if options.load_config and options.filename:
            config.load(options.filename)
        else:
            config.load_default()
        if create:
            config.create()

        # FIXME: This should be removed and we should just import
        #        the global settings after fixing StoqConfig to
        #        only update the global settings.
        self._db_settings = config.get_settings()
        setup(config, options, register_station=register_station,
              check_schema=check_schema, load_plugins=load_plugins)
        return config

    def add_options(self, parser, cmd):

        group = optparse.OptionGroup(parser, 'Database migration')
        group.add_option('', '--dry-run',
                         action="store_true",
                         dest="dry",
                         help='Dry run, do not commit')
        parser.add_option_group(group)

        func = getattr(self, 'opt_' + cmd, None)
        if not func:
            return

        group = optparse.OptionGroup(parser, '%s options' % cmd)
        func(parser, group)
        parser.add_option_group(group)

    def run_command(self, options, cmd, args):
        func = getattr(self, 'cmd_' + cmd, None)
        if func is None:
            self._read_config(options, load_plugins=False,
                              register_station=False)
            from stoqlib.lib.pluginmanager import get_plugin_manager
            manager = get_plugin_manager()
            if cmd in manager.installed_plugins_names:
                if not len(args):
                    raise SystemExit("%s: %s requires at least 2 argument(s)" % (
                        self.prog_name, cmd))
                plugin = manager.get_plugin(cmd)
                return plugin.handle_dbadmin_command(args[0], options, args[1:])
            else:
                print("%s: Invalid command: `%s' type `%s help' for usage." % (
                    self.prog_name, cmd, self.prog_name))
                return 1

        nargs = func.func_code.co_argcount - 2
        if len(args) < nargs:
            raise SystemExit("%s: %s requires at least %d argument(s)" % (
                self.prog_name, cmd, nargs))
        self.args = args
        return func(options, *args)

    def cmd_help(self, options):
        """Show available commands help"""
        cmds = []
        max_len = 0

        for attr in dir(self):
            if not attr.startswith('cmd_'):
                continue

            name = attr[4:]
            doc = getattr(self, attr).__doc__ or ''
            max_len = max(max_len, len(name))
            cmds.append((name, doc.split(r'\n')[0]))

        max_len = max_len + 2

        print('Usage: stoqdbadmin [plugin] <command> [<args>]')
        print()
        print('Available commands:')

        for name, doc in cmds:
            print('  %s%s' % (name.ljust(max_len), doc))

        self._read_config(options, load_plugins=False,
                          register_station=False)

        from stoqlib.lib.pluginmanager import get_plugin_manager
        manager = get_plugin_manager()
        for plugin_name in manager.installed_plugins_names:
            plugin = manager.get_plugin(plugin_name)
            for command in plugin.get_dbadmin_commands():
                print('   %s %s' % (plugin_name, command))

        return 0

    def cmd_init(self, options):
        """Creates and initializes a database"""
        # Create a database user before trying to connect
        if options.create_dbuser:
            if not options.username:
                raise SystemExit(
                    "This option requires a --username set")
            retval = self._create_dbuser(options.username)
            if retval != 0:
                return retval
        config = self._read_config(options, register_station=False,
                                   check_schema=False,
                                   load_plugins=False)

        from stoqlib.database.admin import initialize_system
        from stoqlib.database.settings import db_settings
        if options.dbname:
            db_settings.dbname = options.dbname
        if options.address:
            db_settings.address = options.address
        if options.port:
            db_settings.port = options.port
        if options.username:
            db_settings.username = options.username
        if options.password:
            db_settings.password = options.password

        try:
            initialize_system(password=unicode(options.password),
                              force=options.force, empty=options.empty)
        except ValueError as e:
            # Database server is missing pg_trgm
            if 'pg_trgm' in str(e):
                return 31
            else:
                raise

        if options.create_examples or options.demo:
            from stoqlib.importers.stoqlibexamples import create
            create(utilities=True)

        if options.register_station and not options.empty:
            self._register_station()

        if options.plugins:
            self._enable_plugins(unicode(options.plugins).split(','))

        if options.demo:
            self._enable_demo()
        config.flush()

    def opt_init(self, parser, group):
        group.add_option('-e', '--create-examples',
                         action='store_true',
                         default=False,
                         dest='create_examples')
        group.add_option('', '--no-register-station',
                         action='store_false',
                         default=True,
                         dest='register_station')
        group.add_option('', '--enable-plugins',
                         action='store',
                         dest='plugins')
        group.add_option('', '--demo',
                         action='store_true',
                         dest='demo')
        group.add_option('', '--create-dbuser',
                         action='store_true',
                         dest='create_dbuser')
        group.add_option('', '--force',
                         action='store_true',
                         dest='force')
        group.add_option('', '--empty',
                         action='store_true',
                         dest='empty')

    def cmd_configure(self, options):
        """Save initial configuration"""
        if not options.dbname:
            print('dbname missing')
            return 1
        if not options.address:
            print('address missing')
            return 1
        config = self._read_config(options, create=True, register_station=False,
                                   check_schema=False, load_plugins=False)
        config.flush()

    def cmd_register(self, options):
        """Register a station computer"""
        self._read_config(options, register_station=False)

        self._register_station()

    def _enable_demo(self):
        from stoqlib.database.runtime import new_store
        store = new_store()
        store.execute("UPDATE parameter_data SET field_value = '1' WHERE field_name = 'DEMO_MODE';")
        store.commit()
        store.close()

    def _enable_plugins(self, plugin_names):
        from stoqlib.lib.pluginmanager import (PluginError,
                                               get_plugin_manager)
        manager = get_plugin_manager()

        for plugin_name in plugin_names:
            if plugin_name in manager.installed_plugins_names:
                print('ERROR: Plugin %s is already enabled' % (plugin_name, ))
                return

            if plugin_name not in manager.available_plugins_names:
                self._run_task(manager.download_plugin(plugin_name))

            try:
                manager.install_plugin(plugin_name)
            except PluginError as err:
                print('ERROR: %s' % (str(err), ))
                return

    def _provide_app_info(self):
        # FIXME: The webservice need the IAppInfo provided to get the stoq
        # version. We cannot do that workaround there because we don't want to
        # import stoq inside stoqlib. Either way, this code to download the
        # egg will move to the plugin dialog soon.
        from kiwi.component import provide_utility
        from stoqlib.lib.appinfo import AppInfo
        from stoqlib.lib.interfaces import IAppInfo
        import stoq
        info = AppInfo()
        info.set("version", stoq.version)
        provide_utility(IAppInfo, info)

    def _setup_logging(self):
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.WARNING)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)

        root = logging.getLogger()
        root.setLevel(logging.WARNING)
        root.addHandler(ch)

    def _run_task(self, deferred):
        from twisted.internet import reactor

        def stop_reactor(*args):
            if reactor.running:
                reactor.stop()

        deferred.addCallback(stop_reactor)
        deferred.addErrback(stop_reactor)
        reactor.run()

    def _register_station(self):
        # Register the current computer as a branch station
        from stoqlib.database.runtime import new_store
        from stoqlib.domain.person import Branch
        from stoqlib.domain.station import BranchStation
        from stoqlib.exceptions import StoqlibError
        from stoqlib.net.socketutils import get_hostname
        store = new_store()

        branches = store.find(Branch)
        if branches:
            branch = branches[0]
        else:
            branch = None

        try:
            BranchStation(store=store,
                          is_active=True,
                          branch=branch,
                          name=get_hostname())
        except StoqlibError as e:
            raise SystemExit("ERROR: %s" % e)

        store.commit()
        store.close()

    def _create_dbuser(self, username):
        import os
        from stoqlib.lib.process import Process, PIPE
        for envname in ['PGUSER', 'PGHOST']:
            if envname in os.environ:
                del os.environ[envname]

        # See if we can connect to the database
        args = ['psql', 'postgres', username, '-c', 'SELECT 1;']
        proc = Process(args, stdout=PIPE)
        proc.communicate()
        if proc.returncode == 0:
            return 0

        from stoqlib.lib.kiwilibrary import library

        createdbuser = library.get_resource_filename(
            'stoq', 'scripts', 'createdbuser.sh')

        args = ['pkexec',
                '-u', 'postgres',
                createdbuser,
                username]
        proc = Process(args)
        proc.communicate()

        if proc.returncode != 0:
            print("ERROR: Failed to run %r" % (args, ))
            return 30
        return 0

    def opt_updateschema(self, parser, group):
        group.add_option('-b', '--disable-backup',
                         action='store_false',
                         default=True,
                         dest='disable_backup')

    def cmd_updateschema(self, options):
        """Update the database schema"""
        from stoqlib.api import api
        from stoqlib.database.migration import StoqlibSchemaMigration
        from stoqlib.lib.environment import is_developer_mode
        from stoqlib.net.server import ServerProxy
        from twisted.internet import reactor

        self._read_config(options, check_schema=False, load_plugins=False,
                          register_station=False)

        # This is a little bit tricky to be able to apply the initial
        # plugin infrastructure
        migration = StoqlibSchemaMigration()

        if is_developer_mode():
            backup = False
        else:
            backup = options.disable_backup

        @api.async
        def migrate(retval):
            server = ServerProxy()
            running = yield server.check_running()
            if running:
                yield server.call('pause_tasks')

            try:
                retval[0] = yield migration.update_async(backup=backup)
            finally:
                # The schema was upgraded. If it was running before,
                # restart it so it can load the new code
                if running:
                    yield server.call('restart')

                if reactor.running:
                    reactor.stop()

        retval = [False]
        reactor.callWhenRunning(migrate, retval)
        reactor.run()

        return 0 if retval[0] else 1

    def opt_clone(self, parser, group):
        group.add_option('', '--dry',
                         action='store_true',
                         dest='dry')

    def opt_update(self, parser, group):
        group.add_option('', '--dry',
                         action='store_true',
                         dest='dry')

    def cmd_dump(self, options, output):
        """Create a database dump"""
        self._read_config(options)

        if output == '-':
            output = None
        self._db_settings.dump_database(output, gzip=options.gzip,
                                        format=options.format)

    def opt_dump(self, parser, group):
        group.add_option('-z', '--gzip',
                         action='store_true',
                         dest='gzip')
        group.add_option('-F', '--format',
                         action='store',
                         default='custom',
                         help="dump format see man pg_dump for more information",
                         dest='format')

    def cmd_restore(self, options, schema):
        """Restore a database dump"""
        self._read_config(options, register_station=False,
                          check_schema=False)
        self._db_settings.execute_sql(schema)

    def cmd_enable_plugin(self, options, plugin_name):
        """Enable a plugin on Stoq"""
        self._read_config(options, register_station=False,
                          check_schema=False,
                          load_plugins=False)
        self._provide_app_info()
        self._setup_logging()

        self._enable_plugins([unicode(plugin_name)])

    def cmd_update_plugins(self, options):
        """Update plugins on Stoq"""
        self._read_config(options, register_station=False,
                          check_schema=False,
                          load_plugins=False)
        self._provide_app_info()
        self._setup_logging()

        from twisted.internet.defer import DeferredList
        from stoqlib.lib.pluginmanager import get_plugin_manager
        manager = get_plugin_manager()

        deferred_list = [
            manager.download_plugin(egg_plugin)
            for egg_plugin in manager.egg_plugins_names]
        self._run_task(DeferredList(deferred_list))

    def cmd_generate_sintegra(self, options, filename, month):
        """Generate a sintegra file"""
        import datetime
        self._read_config(options)

        year, month = map(int, month.split('-'))
        start = datetime.date(year, month, 1)
        for day in [31, 30, 29, 28]:
            try:
                end = datetime.date(year, month, day)
                break
            except ValueError:
                pass
        from stoqlib.lib.sintegragenerator import generate
        generate(filename, start, end)

    def cmd_shell(self, options):
        """Drop to a shell for executing SQL queries"""
        self._read_config(options, register_station=False,
                          check_schema=False)
        self._db_settings.start_shell(options.command)

    def opt_shell(self, parser, group):
        group.add_option('-c', '--command',
                         action='store',
                         help='Execute SQL command',
                         dest='command')

    def cmd_serve(self, options):
        """Serve a Stoq XMLRPC server"""
        from twisted.internet import reactor
        from stoqlib.lib.daemonutils import DaemonManager

        print('* Starting XMLRPC server...')

        self._read_config(options, register_station=False)
        port = options.serverport and int(options.serverport)
        dm = DaemonManager(port=port)

        def on_server_running(daemon_manager):
            uri = daemon_manager.base_uri
            print('The XMLRPC server is running on ' + uri)

        defer = dm.start()
        defer.addCallback(on_server_running)

        reactor.run()

    def opt_serve(self, parser, group):
        group.add_option('', '--serverport',
                         action='store',
                         help='Port to serve the server',
                         dest='serverport')

    def cmd_import(self, options):
        """Import data into Stoq"""
        self._read_config(options, register_station=False)
        from stoqlib.importers import importer
        importer = importer.get_by_type(options.type)
        importer.feed_file(options.import_filename)
        importer.process()

    def opt_import(self, parser, group):
        group.add_option('-t', '--type',
                         action="store",
                         help="Type of file to import",
                         dest="type")
        group.add_option('', '--import-filename',
                         action="store",
                         help="Filename to import",
                         dest="import_filename")

    def cmd_console(self, options):
        """Drop to a Stoq python console"""
        from stoqlib.lib.console import Console
        self._read_config(options, register_station=False)
        console = Console()
        console.populate_namespace(options.bare)
        if options.script:
            console.execute(options.script)
        else:
            console.interact()

        if options.commit:
            console.store.commit()

    def opt_console(self, parser, group):
        group.add_option('-b', '--bare',
                         action="store_true",
                         dest="bare")
        group.add_option('-c', '--command',
                         action="store_true",
                         dest="command")
        group.add_option('', '--commit',
                         action="store_true",
                         dest="commit")
        group.add_option('-s', '--script',
                         action="store",
                         dest="script")


def main(args):
    args = args[1:]
    if not args:
        # defaults to help
        args.append('help')

    cmd = args[0]
    args = args[1:]

    # import library or else externals won't be on sys.path
    from stoqlib.lib.kiwilibrary import library
    library  # pylint: disable=W0104

    from stoq.lib.options import get_option_parser
    parser = get_option_parser()

    handler = StoqCommandHandler(parser.get_prog_name())
    handler.add_options(parser, cmd)
    options, args = parser.parse_args(args)

    return handler.run_command(options, cmd, args)

if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv))
    except KeyboardInterrupt:
        print('Interrupted')
