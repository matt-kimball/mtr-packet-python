import asyncio
import collections
import os
import unittest

import mtrpacket


Command = collections.namedtuple('Command', ['token', 'command', 'args'])


def make_command(line):

    """Convert a command string into a Command named type"""

    atoms = line.decode('ascii').strip().split(' ')

    token = atoms[0]
    command = atoms[1]
    args = {}

    i = 2
    while i + 1 < len(atoms):
        args[atoms[i]] = atoms[i + 1]
        i += 2

    return Command(token, command, args)


class MtrPacketSubstitute:

    """Substitute the 'mtr-packet' executable with an alternative

    To be used in a 'with' code block to provide an altnerative
    to 'mtr-packet' for mtrpacket.MtrPacket objects used in that block.
    """

    def __init__(self, substitute):
        self.substitute = substitute
        self.saved = None

    def __enter__(self):
        try:
            self.saved = os.environ['MTR_PACKET']
        except KeyError:
            self.saved = None

        os.environ['MTR_PACKET'] = self.substitute

    def __exit__(self, etype, evalue, traceback):
        if self.saved:
            os.environ['MTR_PACKET'] = self.saved
        else:
            del os.environ['MTR_PACKET']


class TestProcExit(unittest.TestCase):

    """Test behavior when the mtr-packet subprocess unexpectedly exits"""

    async def async_proc_exit(self):
        async with mtrpacket.MtrPacket() as mtr:
            await mtr.probe('127.0.0.1')

    def test_proc_exit(self):
        with MtrPacketSubstitute('true'):
            with self.assertRaises(mtrpacket.ProcessError):
                asyncio_run(self.async_proc_exit())


class TestMissingExecutable(unittest.TestCase):

    """Test behavior when 'mtr-packet' is missing"""

    async def async_missing_exec(self):
        async with mtrpacket.MtrPacket() as mtr:
            pass

    def test_missing_exec(self):
        with MtrPacketSubstitute('mtr-packet-missing'):
            with self.assertRaises(mtrpacket.ProcessError):
                asyncio_run(self.async_missing_exec())


class TestCancellation(unittest.TestCase):

    """Test whether a task waiting on a probe can be cancelled

    There was a problem where cancelling a task waiting on a
    probe caused exceptions within the cancellation due to a
    cancelled future being completed with an exception.

    Test for that.
    """

    async def command_wait(self, mtr):
        await mtr.probe('127.255.255.255', timeout=60)

    async def async_launch(self):
        async with mtrpacket.MtrPacket() as mtr:
            coro = self.command_wait(mtr)
            task = asyncio.ensure_future(coro)
            await asyncio.sleep(1)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


    def test_cancel(self):
        asyncio_run(self.async_launch())


class TestCommands(unittest.TestCase):

    """Bind a socket as a substitute for mtr-packet and test commands passed

    We will substitute 'nc' for 'mtr-packet' and connect to a socket in this
    process, which allows us to get the commands issued to and generate
    responses as if we were the 'mtr-packet' subprocess.
    """

    def gen_handle_command(self, in_queue, out_queue):
        async def handle_command(reader, writer):
            while not reader.at_eof():
                line = await reader.readline()

                if line:
                    command = make_command(line)

                    if command.command == 'check-support':
                        reply = command.token + ' feature-support support ok\n'
                    else:
                        #  Save received commands to in_queue
                        in_queue.put_nowait(command)

                        #  Respond with a canned response from out_queue
                        reply_body = await out_queue.get()
                        reply = command.token + ' ' + reply_body + '\n'

                    writer.write(reply.encode('ascii'))

            writer.close()

        return handle_command

    async def send_probes(self, mtr, in_queue, out_queue):
        out_queue.put_nowait('reply ip-4 8.8.4.4 round-trip-time 1000')
        result = await mtr.probe('8.8.8.8', bit_pattern=42)
        command = await in_queue.get()

        assert command.command == 'send-probe'
        assert command.args['ip-4'] == '8.8.8.8'
        assert command.args['bit-pattern'] == '42'
        assert result.success
        assert result.responder == '8.8.4.4'
        assert result.time_ms == 1.0

        out_queue.put_nowait('reply ip-4 127.0.1.1 round-trip-time 500')
        result = await mtr.probe('127.0.1.1', local_ip='127.0.0.1')
        command = await in_queue.get()

        assert command.command == 'send-probe'
        assert command.args['ip-4'] == '127.0.1.1'
        assert command.args['local-ip-4'] == '127.0.0.1'
        assert result.success
        assert result.responder == '127.0.1.1'
        assert result.time_ms == 0.5

        out_queue.put_nowait('no-reply')
        result = await mtr.probe('::1', ttl=4)
        command = await in_queue.get()

        assert command.command == 'send-probe'
        assert command.args['ip-6'] == '::1'
        assert command.args['ttl'] == '4'
        assert not result.success
        assert result.result == 'no-reply'

        out_queue.put_nowait('ttl-expired ip-4 8.0.0.1 mpls 1,2,0,3,4,5,1,6')
        result = await mtr.probe('8.8.9.9')
        command = await in_queue.get()

        assert len(result.mpls) == 2
        assert result.mpls[0].label == 1
        assert result.mpls[0].traffic_class == 2
        assert result.mpls[0].bottom_of_stack is False
        assert result.mpls[0].ttl == 3
        assert result.mpls[1].label == 4
        assert result.mpls[1].traffic_class == 5
        assert result.mpls[1].bottom_of_stack is True
        assert result.mpls[1].ttl == 6

    async def async_commands(self):
        in_queue = asyncio.Queue()
        out_queue = asyncio.Queue()

        server = await asyncio.start_server(
            self.gen_handle_command(in_queue, out_queue), '127.0.0.1', 8901)

        try:
            async with mtrpacket.MtrPacket() as mtr:
                await self.send_probes(mtr, in_queue, out_queue)
        finally:
            server.close()

    def test_commands(self):
        with MtrPacketSubstitute('./nc_mock.sh'):
            asyncio_run(self.async_commands())


def asyncio_run(coro):

    """Equivalent to Python 3.7's asyncio.run"""

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(loop.create_task(coro))


unittest.main()
