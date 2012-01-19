#!/usr/bin/env python
# -*- Mode: Python; coding: iso-8859-1 -*-
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
                    raise SystemExit(
                        "%s: %s requires at least 2 argument(s)" % (
                        self.prog_name, cmd))
                plugin = manager.get_plugin(cmd)
                return plugin.handle_dbadmin_command(args[0], options, args[1:])
            else:
                print "%s: Invalid command: `%s' type `%s help' for usage." % (
                    self.prog_name, cmd, self.prog_name)
                return 1

        nargs = func.func_code.co_argcount - 2
        if len(args) < nargs:
            raise SystemExit(
                "%s: %s requires at least %d argument(s)" % (
                self.prog_name, cmd, nargs))
        self.args = args
        return func(options, *args)

    def cmd_help(self, options):
        cmds = [attr[4:] for attr in dir(self) if attr.startswith('cmd_')]
        cmds.sort()
        cmds.remove('help')

        print 'Available commands:'
        for name in cmds:
            print '  ', name

        self._read_config(options, load_plugins=False,
                          register_station=False)

        from stoqlib.lib.pluginmanager import get_plugin_manager
        manager = get_plugin_manager()
        for plugin_name in manager.installed_plugins_names:
            plugin = manager.get_plugin(plugin_name)
            for command in plugin.get_dbadmin_commands():
                print '   %s %s' % (plugin_name, command)

        return 0

    def cmd_init(self, options):
        from stoq.lib.startup import clean_database

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
        clean_database(config, options)

        if options.create_examples or options.demo:
            from stoqlib.importers.stoqlibexamples import create
            create(utilities=True)

        if options.register_station:
            self._register_station()

        if options.plugins:
            self._enable_plugins(options.plugins.split(','))

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

    def cmd_configure(self, options):
        if not options.dbname:
            print 'dbname missing'
            return 1
        if not options.address:
            print 'address missing'
            return 1
        config = self._read_config(options, create=True, register_station=False,
                                   check_schema=False, load_plugins=False)
        config.flush()

    def cmd_register(self, options):
        self._read_config(options, register_station=False)

        self._register_station()

    def _enable_demo(self):
        from stoqlib.database.runtime import new_transaction
        trans = new_transaction()
        trans.query("UPDATE parameter_data SET field_value = '1' WHERE field_name = 'DEMO_MODE';")
        trans.commit()

    def _enable_plugins(self, plugin_names):
        from stoqlib.lib.pluginmanager import (PluginError,
                                               get_plugin_manager)
        manager = get_plugin_manager()

        for plugin_name in plugin_names:
            try:
                manager.install_plugin(plugin_name)
            except PluginError as err:
                print err
                print "Available plugins:"
                for plugin_name in manager.available_plugins_names:
                    print "  %s" % (plugin_name, )
                return

    def _register_station(self):
        # Register the current computer as a branch station
        import socket
        from stoqlib.database.runtime import new_transaction
        from stoqlib.domain.interfaces import IBranch
        from stoqlib.domain.person import Person
        from stoqlib.domain.station import BranchStation
        from stoqlib.exceptions import StoqlibError
        trans = new_transaction()

        branches = Person.iselect(IBranch, connection=trans)
        if branches:
            branch = branches[0]
        else:
            branch = None

        try:
            BranchStation(connection=trans,
                          is_active=True,
                          branch=branch,
                          name=socket.gethostname())
        except StoqlibError, e:
            raise SystemExit("ERROR: %s" % e)

        trans.commit()

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

        args = ['pkexec',
                '-u', 'postgres',
                'stoqcreatedbuser',
                username]
        proc = Process(args)
        proc.communicate()
        if proc.returncode != 0:
            print "ERROR: Failed to run %r" % (args, )
            return 30
        return 0

    def opt_updateschema(self, parser, group):
        group.add_option('-b', '--disable-backup',
                         action='store_false',
                         default=True,
                         dest='disable_backup')

    def cmd_updateschema(self, options):
        from stoqlib.database.migration import StoqlibSchemaMigration

        self._read_config(options, check_schema=False, load_plugins=False,
                          register_station=False)

        # This is a little bit tricky to be able to apply the initial
        # plugin infrastructure
        migration = StoqlibSchemaMigration()
        if not migration.update(backup=options.disable_backup):
            return 1

    def cmd_serve(self, options):
        from stoqlib.database.synchronization import SynchronizationService
        self._read_config(options, check_schema=False, register_station=False)
        service = SynchronizationService("", 9000)
        service.serve()

    def cmd_clone(self, options, hostname, station):
        from stoqlib.database.synchronization import SynchronizationClient
        self._read_config(options)

        client = SynchronizationClient(hostname, 9000)
        if options.dry:
            client.disable_commit()
        client_station = client.get_station_name()
        if client_station != station:
            raise SystemExit(
                "The station name for the server is %s, expected %s" %
                (client_station, station))
        client.clean()
        client.clone(station)

    def opt_clone(self, parser, group):
        group.add_option('', '--dry',
                         action='store_true',
                         dest='dry')

    def cmd_update(self, options, hostname, station):
        from stoqlib.database.synchronization import SynchronizationClient
        self._read_config(options)

        client = SynchronizationClient(hostname, 9000)
        if options.dry:
            client.disable_commit()
        client_station = client.get_station_name()
        if client_station != station:
            raise SystemExit(
                "The station name for the server is %s, expected %s" %
                (client_station, station))
        client.update(station)

    def opt_update(self, parser, group):
        group.add_option('', '--dry',
                         action='store_true',
                         dest='dry')

    def cmd_dump(self, options, output):
        from stoqlib.database.database import dump_database
        self._read_config(options)

        if output == '-':
            output = None
        dump_database(output)

    def cmd_restore(self, options, schema):
        from stoqlib.database.database import execute_sql

        self._read_config(options, register_station=False,
                          check_schema=False)
        execute_sql(schema)

    def cmd_enable_plugin(self, options, plugin_name):
        self._read_config(options, register_station=False,
                          check_schema=False,
                          load_plugins=False)

        self._enable_plugins([plugin_name])

    def cmd_generate_sintegra(self, options, filename, month):
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
        from stoqlib.database.database import start_shell
        self._read_config(options, register_station=False,
                          check_schema=False)
        start_shell(options.command)

    def opt_shell(self, parser, group):
        group.add_option('-c', '--command',
                         action='store',
                         help='Execute SQL command',
                         dest='command')

    def cmd_import(self, options):
        self._read_config(options, register_station=False)
        from stoqlib.importers import importer
        importer = importer.get_by_type(options.type)
        importer.feed_file(options.filename)
        importer.process()

    def opt_import(self, parser, group):
        group.add_option('-t', '--type',
                         action="store",
                         help="Type of file to import",
                         dest="type")
        group.add_option('', '--import-filename',
                         action="store",
                         help="Filename to import",
                         dest="filename")

    def cmd_console(self, options):
        from stoqlib.lib.console import Console
        self._read_config(options, register_station=False)
        console = Console()
        console.populate_namespace(options.bare)
        if options.script:
            console.execute(options.script)
        else:
            console.interact()

        if options.commit:
            console.trans.commit()

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
    pname = args[0]
    args = args[1:]
    if not args:
        print "Type '%s help' for usage." % pname
        return 1

    cmd = args[0]
    args = args[1:]

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
        print 'Interrupted'
