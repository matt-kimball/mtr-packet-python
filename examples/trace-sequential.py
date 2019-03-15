import asyncio
import sys
import mtrpacket


#
#  Coroutine which sends probes for each network hop.
#  In this case, we wait for each probe to complete before
#  sending the next, but a more complicated program could
#  issue multiple probes concurrently.
#
async def trace(host):
    async with mtrpacket.MtrPacket() as mtr:

        #
        #  The time-to-live (TTL) value of the probe determines
        #  the number of network hops the probe will take
        #  before its status is reported
        #
        for ttl in range(1, 256):
            result = await mtr.probe(host, ttl=ttl)

            #  Format the probe results for printing
            line = '{}.'.format(ttl)
            if result.time_ms:
                line += ' {}ms'.format(result.time_ms)
            line += ' {}'.format(result.result)
            if result.responder:
                line += ' from {}'.format(result.responder)

            print(line)

            #  If a probe arrived at its destination IP address,
            #  there is no need for further probing.
            if result.success:
                break


#  Get a hostname to trace to on the commandline
if len(sys.argv) > 1:
    hostname = sys.argv[1]
else:
    print('Usage: python3 trace-sequential.py <hostname>')
    sys.exit(1)


#  We need asyncio's event loop to run the coroutine
loop = asyncio.get_event_loop()
try:
    trace_coroutine = trace(hostname)
    try:
        loop.run_until_complete(trace_coroutine)
    except mtrpacket.HostResolveError:
        print("Can't resolve host '{}'".format(hostname))
finally:
    loop.close()
