import asyncio
import curses
import sys

import mtrpacket


#
#  ProbeRecord keeps a record of round-trip times of probes and repsonder
#  IP addresses, for a particular time-to-live (TTL) value.
#
#  There may be multiple IP addresses for one particular TTL value,
#  because some networks have multiple equally weighted routes.
#
class ProbeRecord:
    def __init__(self, ttl):
        self.ttl = ttl
        self.success = False
        self.ip_addrs = []
        self.probe_times = []

    #  Format the information about this line for display
    def print(self, screen):
        line = '{:>2}. '.format(self.ttl)

        if self.ip_addrs:
            line += '{:42}'.format(self.ip_addrs[0])
        else:
            line += '{:42}'.format('  ???')

        for time in self.probe_times:
            if time is None:
                line += '          *'
            else:
                line += '  {:>7.3f}ms'.format(time)

        #  Use curses to display the line
        screen.addstr(line + '\n')

        #  List IP addresses beyond the first
        for addr in self.ip_addrs[1:]:
            screen.addstr('    ' + addr + '\n')


#  When we've got a result for one of our probes, we'll regenerate
#  the screen output, and allow curses to refresh it.
def redraw(screen, all_records):
    screen.erase()

    for record in all_records:
        record.print(screen)

        #  If one of our probes has arrived at the destination IP,
        #  we don't need to display further hops
        if record.success:
            break

    screen.refresh()


#  Perform multiple probes with a specific time to live (TTL) value
async def probe_ttl(mtr, hostname, ttl, record, redraw_callback):
    for count in range(3):
        result = await mtr.probe(hostname, ttl=ttl, timeout=1)

        if result.success:
            record.success = True

        #  Record the time of the latest probe
        record.probe_times.append(result.time_ms)

        addr = result.responder
        #  If the address of the responder isn't already in the list
        #  of addresses responding at this TTL, add it
        if addr and addr not in record.ip_addrs:
            record.ip_addrs.append(addr)

        #  Redraw the display, which will include this probe
        redraw_callback()

        #  Wait a small amount of time before sending the next probe
        #  to get an independent sample of network conditions
        await asyncio.sleep(0.1)


#  Launch all the probes for the trace.
#  We'll use a separate coroutine (probe_ttl) for each ttl value,
#  and those coroutines will run concurrently.
async def launch_probes(screen, hostname):
    all_records = []

    #  When one of the probes has a result to display, we'll use
    #  this callback to display it
    def redraw_hops():
        redraw(screen, all_records)

    async with mtrpacket.MtrPacket() as mtr:
        probe_tasks = []

        for ttl in range(1, 32):
            #  We need a new ProbeRecord for each ttl value
            record = ProbeRecord(ttl)
            all_records.append(record)

            #  Start a new asyncio task for this probe
            probe_coro = probe_ttl(mtr, hostname, ttl, record, redraw_hops)
            probe_tasks.append(asyncio.ensure_future(probe_coro))

            #  Give each probe a slight delay to avoid flooding
            #  the network interface, which might perturb the
            #  results
            await asyncio.sleep(0.05)

        #  Wait for all tasks to complete
        await asyncio.gather(*probe_tasks)


#  Use asyncio's event loop for the main body of our program.
#  We want to use curses for displaying results throughout our
#  execution, so we'll wrap the event loop with curses initialization.
def main(hostname):
    screen = curses.initscr()
    try:
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(launch_probes(screen, hostname))
        finally:
            loop.close()
    finally:
        curses.endwin()


#  Get the hostname to trace to on the commandline
if len(sys.argv) > 1:
    main(sys.argv[1])
else:
    print('Usage: python3 trace-concurrent.py <hostname>')
    sys.exit(1)
