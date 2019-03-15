import asyncio
import sys
import mtrpacket


#
#  We send the probe in a coroutine since mtrpacket operates
#  asynchronously.  In a more complicated program, this
#  allows other asynchronous operations to occur concurrently
#  with the probe.
#
async def probe(host):
    async with mtrpacket.MtrPacket() as mtr:
        result = await mtr.probe(host)

        #  If the ping got a reply, report the IP address and time
        if result.success:
            print('reply from {} in {} ms'.format(
                result.responder, result.time_ms))
        else:
            print('no reply ({})'.format(result.result))


#  Get a hostname to ping from the commandline
if len(sys.argv) > 1:
    hostname = sys.argv[1]
else:
    print('Usage: python3 ping.py <hostname>')
    sys.exit(1)


#  We need asyncio's event loop to run the coroutine
loop = asyncio.get_event_loop()
try:
    probe_coroutine = probe(hostname)
    try:
        loop.run_until_complete(probe_coroutine)
    except mtrpacket.HostResolveError:
        print("Can't resolve host '{}'".format(hostname))
finally:
    loop.close()
