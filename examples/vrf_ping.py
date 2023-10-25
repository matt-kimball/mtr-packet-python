import asyncio
import sys
import mtrpacket


# we pass a command prefix to allow mtr-packet access to more complex environments.
# in this example, mtr-packet is run from within my_vrf using iproute2.
async def probe(host, command_prefix):
    async with mtrpacket.MtrPacket(command_prefix=command_prefix) as mtr:
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
    command_prefix = sys.argv[2]
else:
    print('Usage: python3 ping.py <hostname> "<command prefix>"')
    sys.exit(1)


#  We need asyncio's event loop to run the coroutine
loop = asyncio.get_event_loop()
try:
    probe_coroutine = probe(hostname, command_prefix)
    try:
        loop.run_until_complete(probe_coroutine)
    except mtrpacket.HostResolveError:
        print("Can't resolve host '{}'".format(hostname))
finally:
    loop.close()

# example: python3 vrf_ping.py 8.8.8.8 "ip netns exec myns"